import time
from flask import (
        Blueprint, render_template, redirect, url_for, request, current_app, jsonify
)

from application.db import get_db

bp = Blueprint("home", __name__, "/")

@bp.route("/", methods=["GET"])
def home():
    return render_template("base.html", allele=None)

@bp.route("/search", methods=["POST"])
def search():
    allele = request.form["allele"]
    peptide = request.form["peptide"]
    allele = allele if allele else "any-allele"
    peptide = peptide if peptide else "any-peptide"
    return redirect(url_for("home.results", allele=allele, peptide=peptide))

@bp.route("/results/<allele>/<peptide>", methods=["GET"])
def results(allele, peptide):
    db = get_db()
    data = []

    start = time.time()
    # Check the parameters and search the database
    # TODO: add pagination functionality for these results.
    if (allele, peptide) == ("any-allele", "any-peptide"):
        data = db.execute("SELECT * FROM pdb_files LIMIT 2000").fetchall()
    elif allele == "any-allele":
        data = db.execute("""SELECT * FROM pdb_files WHERE peptide = ?""",
                (peptide,)).fetchall()
    elif peptide == "any-peptide":
        data = db.execute("""SELECT * FROM pdb_files WHERE allele = ?""",
                (allele,)).fetchall()
    else:
        data = db.execute("""SELECT * FROM pdb_files WHERE allele = ?
            AND peptide = ?""", (allele, peptide)).fetchall()
    end = time.time()

    query_time = end - start
    num_results = len(data)

    return render_template("results.html", results=data, allele=allele, 
            peptide=peptide, num_results=num_results, query_time=query_time)

@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")
    if suggest_type == 'allele':
        data = db.execute("SELECT DISTINCT allele FROM pdb_files WHERE allele LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["allele"], "data":r["allele"]}, data))
    elif suggest_type == "peptide":
        data = db.execute("SELECT DISTINCT peptide FROM pdb_files WHERE peptide LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["peptide"], "data":r["peptide"]}, data))
    else:
        data = []

    return jsonify({"suggestions":data}) 
