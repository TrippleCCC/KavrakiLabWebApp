import os
import io
import zipfile
from flask import (
        Blueprint, redirect, url_for, request, send_file, flash
)


bp = Blueprint("download", __name__, url_prefix="/download")

@bp.route("/", methods=["GET"])
def download():
    # Make sure that the path is in rdf_mount
    if "rdf_mount" not in request.args.get("path"):
        flash("Error in file path", "error")
        return redirect(url_for("home.results"))
    return send_file(request.args.get("path"), as_attachment=True)


@bp.route("/all", methods=["POST"])
def download_all():
    # Get the file paths from the request.
    all_ids = request.json["ids"]
    if not all_ids:
        return "", 403

    # Get all the file paths for the ids 
    db = get_db()
    filepaths = []
    for db_id in all_ids:
        filepaths.append(db.execute("""SELECT filepath FROM pdb_files 
            WHERE id = ?""", (int(db_id),)).fetchone()[0]) 

    # Read the files and zip the together
    zip_file = io.BytesIO()
    with zipfile.ZipFile(zip_file, "w") as zf:
        for filepath in filepaths:
            zf.write(filepath, compress_type=zipfile.ZIP_DEFLATED, 
                    arcname=os.path.basename(filepath))
    zip_file.seek(0)
    return send_file(zip_file, attachment_filename="download.zip", as_attachment=True)
