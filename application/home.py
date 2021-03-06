from flask import (
        Blueprint, render_template, redirect, url_for, request, current_app
)

from application.db import get_db

bp = Blueprint("home", __name__, "/")

@bp.route("/", methods=["GET"])
def home():
    return render_template("base.html")

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
    data = None
    if (allele, protein) == ("any-allele", "any-protein"):
        return render_template("results.html")
    elif allele == "any-allele":
        data = db.execute("""SELECT * FROM pdb_files WHERE protein = ?""",
                (protein,)).fetchall()
    elif protein == "any-protein":
        data = db.execute("""SELECT * FROM pdb_files WHERE allele = ?""",
                (allele,)).fetchall()

    return render_template("results.html", results=data)
