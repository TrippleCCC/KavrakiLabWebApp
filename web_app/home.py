import time
import os
import io
import zipfile
from pypika import Query, Table
from flask import (
        Blueprint, render_template, redirect, url_for, request, current_app, jsonify, send_file, flash
)

from web_app.db import get_db

bp = Blueprint("home", __name__, "/")

LIMIT_MESSAGE = "Results have been limited to 2000 for all-allele, all-pepetide search"

@bp.route("/", methods=["GET"])
def home():
    return render_template("base.html", allele=None)

@bp.route("/search", methods=["POST"])
def search():
    # Handle query parameters. Then redirect.
    allele = request.form.get("allele") or "any-allele"
    peptide = request.form.get("peptide") or "any-peptide"
    binder = request.form.get("binder") or "off"
    non_binder = request.form.get("non-binder") or "off"
    return redirect(
            url_for(".results", allele=allele, peptide=peptide, binder=binder, non_binder=non_binder))


@bp.route("/results", methods=["GET"])
def results():
    db = get_db()
    data = []

    allele = request.args.get("allele")
    peptide = request.args.get("peptide")
    binder = request.args.get("binder")
    non_binder = request.args.get("non_binder")

    # Begin Query building
    pdb_files = Table("pdb_files")
    query_builder = Query.from_(pdb_files).select(
            pdb_files.id, pdb_files.allele, pdb_files.peptide, 
            pdb_files.binder, pdb_files.filepath)

    # Add WHERE conditions for alleles and peptides
    if allele != "any-allele":
        query_builder = query_builder.where(pdb_files.allele == allele)
    if peptide != "any-peptide":
        query_builder = query_builder.where(pdb_files.peptide == peptide)

    # Add IN clause for binders
    binders = []
    if binder == "on":
        binders.append(1)
    if non_binder == "on":
        binders.append(0)
    query_builder = query_builder.where(pdb_files.binder.isin(binders))

    # Add limit if allele and peptide are not specified
    if (allele, peptide) == ("any-allele", "any-peptide"):
        flash(LIMIT_MESSAGE, "warning")
        query_builder = query_builder.limit(2000)

    start = time.time()
    data = db.execute(query_builder.get_sql()).fetchall()
    end = time.time()

    query_time = end - start
    num_results = len(data)

    return render_template("results.html", results=data, allele=allele, 
            peptide=peptide, num_results=num_results, query_time=query_time,
            binder=binder, non_binder=non_binder)


@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")

    data = []

    # Begin Query building
    pdb_files = Table("pdb_files")
    query_builder = Query.from_(pdb_files)

    # Determine the suggestions based on the suggestion type
    if suggest_type == "allele":
        query_builder = query_builder.select(pdb_files.allele).distinct() \
                .where(pdb_files.allele.like(f"%{query}%"))
    elif suggest_type == "peptide":
        query_builder = query_builder.select(pdb_files.peptide).distinct() \
                .where(pdb_files.peptide.like(f"%{query}%"))

    query_builder = query_builder.limit(5)

    # Retrive data and reformat
    data = db.execute(query_builder.get_sql()).fetchall()
    data = list(map(lambda r: {"value":r[suggest_type], "data":r[suggest_type]}, data))

    return jsonify({"suggestions":data}) 

