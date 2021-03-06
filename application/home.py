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
    protein = request.form["protein"]
    allele = allele if allele else "any-allele"
    protein = protein if protein else "any-protein"
    return redirect(url_for("home.results", allele=allele, protein=protein))

@bp.route("/results/<allele>/<protein>", methods=["GET"])
def results(allele, protein):
    db = get_db()
    data = []

    start = time.time()
    # Check the parameters and search the database
    if (allele, protein) == ("any-allele", "any-protein"):
        return render_template("results.html")
    elif allele == "any-allele":
        data = db.execute("""SELECT * FROM pdb_files WHERE protein = ?""",
                (protein,)).fetchall()
    elif protein == "any-protein":
        data = db.execute("""SELECT * FROM pdb_files WHERE allele = ?""",
                (allele,)).fetchall()
    else:
        data = db.execute("""SELECT * FROM pdb_files WHERE allele = ?
            AND protein = ?""", (allele, protein)).fetchall()
    end = time.time()

    query_time = end - start
    num_results = len(data)

    return render_template("results.html", results=data, allele=allele, 
            protein=protein, num_results=num_results, query_time=query_time)

@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")
    if suggest_type == 'allele':
        data = db.execute("SELECT DISTINCT allele FROM pdb_files WHERE allele LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["allele"], "data":r["allele"]}, data))
    elif suggest_type == "protein":
        data = db.execute("SELECT DISTINCT protein FROM pdb_files WHERE protein LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["protein"], "data":r["protein"]}, data))
    else:
        data = []

    return jsonify({"suggestions":data}) 
