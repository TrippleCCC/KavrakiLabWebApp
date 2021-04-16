import uuid
import os
import threading
import io
import zipfile
from pypika import Query, Table
from flask import (
        Blueprint, redirect, url_for, request, send_file, flash, jsonify
)

from web_app.db import get_db


# Holds currently running threads
thread_table = {}
thread_progress = {}

# Datastructure for holding zip progress
class ZipProgress():
    def __init__(self, total):
        self.total = total
        self.progress = 0
        self.status = False
    
    def increment_progress(self):
        if self.status:
            return
        self.progress += 1
        if self.progress == self.total:
            self.status = True 

# Thread class for zipping files.
class ZipThread(threading.Thread):
    def __init__(self, thread_id, filepaths):
        self.thread_id = thread_id
        self.result = None
        self.filepaths = filepaths
        self.stop_event = threading.Event()
        super().__init__()

    def stop(self):
        self.stop_event.set()

    def run(self):
        # Read the files and zip the together
        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, "w") as zf:
            for filepath in self.filepaths:
                zf.write(filepath, compress_type=zipfile.ZIP_DEFLATED, 
                        arcname=os.path.basename(filepath))
                try:
                    thread_progress[self.thread_id].increment_progress()
                except KeyError:
                    # This means that the progress doesnt exist
                    return
                if self.stop_event.is_set():
                    return
        zip_file.seek(0)
        self.result = zip_file


bp = Blueprint("download", __name__, url_prefix="/download")

@bp.route("/", methods=["GET"])
def download():
    # Make sure that the path is in rdf_mount
    # TODO: Probably do more rigorous checks
    if "rdf_mount" not in request.args.get("path"):
        flash("Error in file path", "error")
        return redirect(url_for("home.results"))
    return send_file(request.args.get("path"), as_attachment=True)


@bp.route("/init", methods=["POST"])
def init_download():
    global thread_table
    global thread_progress

    
    download_type = request.json["downloadType"]
    if not download_type:
        return "", 403

    filepaths = []

    if download_type == "singleconf":
        # Get the file paths from the request.
        all_ids = request.json["ids"]
        if not all_ids:
            return "", 403

        singleconf_files = Table("singleconf_files")
        base_query = Query.from_(singleconf_files).select(singleconf_files.filepath)

        # Get all the file paths for the ids 
        db = get_db()
        for db_id in all_ids:
            query = base_query.where(singleconf_files.id == int(db_id)).get_sql()
            filepaths.append(db.execute(query).fetchone()["filepath"])
    elif download_type == "multiconf":

        id = request.json["id"]
        if not id:
            return "", 403

        # Get the folder path for the id
        multiconf_files = Table("multiconf_files")
        base_query = Query.from_(multiconf_files).select(multiconf_files.folderpath) \
                .where(multiconf_files.id == id)

        db = get_db()
        dir = db.execute(base_query.get_sql()).fetchone()["folderpath"]

        # Get the file paths for the multiconf files
        for root, _, files in os.walk(os.path.abspath(dir)):
            for file in files:
                filepaths.append(os.path.join(root, file))

    # Begin zip thread
    thread_id = str(uuid.uuid4())
    thread_table[thread_id] = ZipThread(thread_id, filepaths)
    thread_progress[thread_id] = ZipProgress(len(filepaths))
    thread_table[thread_id].start()

    return jsonify({"thread-id": thread_id})


@bp.route("/progress", methods=["POST"])
def get_progress():
    global thread_progress 

    thread_id = request.json["thread-id"]

    # Check if thread exists
    if thread_id not in thread_progress:
        return jsonify({"error": "thread has died"}) 

    # Return the progress of the current thread
    try:
        data = {"progress": thread_progress[thread_id].progress,
                "total": thread_progress[thread_id].total}
    except KeyError:
        return jsonify({"error": "thread has died"}) 

    return jsonify(data)
  

@bp.route("/get_zip", methods=["POST"])
def get_zip_file():
    global thread_table
    global thread_progress

    thread_id = request.json["thread-id"]

    # Get the zip file from the thread
    zipped_file = thread_table[thread_id].result
    
    # Remove references to the thread
    del thread_table[thread_id]
    del thread_progress[thread_id]

    return send_file(zipped_file, attachment_filename="download.zip", as_attachment=True)


@bp.route("/cancel", methods=["POST"])
def cancel_download():
    global thread_table
    global thread_progress

    # Get thread_id
    thread_id = request.json["thread-id"]

    # Terminate the thread and remove references
    thread_table[thread_id].stop()
    del thread_table[thread_id]
    del thread_progress[thread_id]

    return jsonify({"status":"exited"})

