import time
from flask import (
        Blueprint, render_template, redirect, url_for, request, current_app
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
