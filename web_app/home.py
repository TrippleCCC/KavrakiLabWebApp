import time
import os
import io
import zipfile
import re
from web_app.util.regex_util import create_peptide_regex, add_bold_tags_to_peptides 
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
    peptide_regex = request.form.get("peptide-regex") or "off"
    return redirect(
            url_for(".results", allele=allele, peptide=peptide, 
                binder=binder, non_binder=non_binder, peptide_regex=peptide_regex))


@bp.route("/results", methods=["GET"])
def results():
    db = get_db()
    data = []

    allele = request.args.get("allele")
    peptide = request.args.get("peptide")
    binder = request.args.get("binder")
    non_binder = request.args.get("non_binder")
    peptide_regex = request.args.get("peptide_regex")

    # Begin Query building
    singleconf_files = Table("singleconf_files")
    query_builder = Query.from_(singleconf_files).select(
            singleconf_files.id, singleconf_files.allele, singleconf_files.peptide, 
            singleconf_files.binder, singleconf_files.filepath)

    # Add WHERE conditions for alleles and peptides
    if allele != "any-allele":
        # Process list of alleles
        alleles = list(map(lambda a: a.strip(), allele.split(",")))
        query_builder = query_builder.where(
                singleconf_files.allele.isin(alleles)
        )
        # TODO: if any-peptide is selected, we should have links to 
        # pre-zipped files for each allele
    if peptide != "any-peptide" and peptide_regex == "off":
        query_builder = query_builder.where(singleconf_files.peptide == peptide)

    # Add IN clause for binders
    binders = []
    if binder == "on":
        binders.append(1)
    if non_binder == "on":
        binders.append(0)
    query_builder = query_builder.where(singleconf_files.binder.isin(binders))

    # Add limit if allele and peptide are not specified
    if (allele, peptide) == ("any-allele", "any-peptide"):
        flash(LIMIT_MESSAGE, "warning")
        query_builder = query_builder.limit(2000)

    # Calculate query time
    start = time.time()

    data = db.execute(query_builder.get_sql()).fetchall()

    # Filter using regex
    if peptide_regex == "on":
        p_regex = create_peptide_regex(peptide)
        pattern = re.compile(p_regex)
        data = list(filter(lambda x: pattern.match(x["peptide"]) is not None, data))

    end = time.time()

    # If we are searching by regex then add b tags to peptide.
    if peptide_regex == "on":
        for i in range(len(data)):
            data[i]["peptide"] = add_bold_tags_to_peptides(peptide, data[i]["peptide"])

    query_time = end - start
    num_results = len(data)

    return render_template("results.html", results=data, allele=allele, 
            peptide=peptide, num_results=num_results, query_time=query_time,
            binder=binder, non_binder=non_binder, peptide_regex=peptide_regex)


@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")

    data = []

    # Begin Query building
    singleconf_files = Table("singleconf_files")
    query_builder = Query.from_(singleconf_files)

    # Determine the suggestions based on the suggestion type
    if suggest_type == "allele":
        query_builder = query_builder.select(singleconf_files.allele).distinct() \
                .where(singleconf_files.allele.like(f"%{query}%"))
    elif suggest_type == "peptide":
        query_builder = query_builder.select(singleconf_files.peptide).distinct() \
                .where(singleconf_files.peptide.like(f"%{query}%"))

    # limit suggestions to 5
    query_builder = query_builder.limit(5)

    # Retrive data and reformat
    data = db.execute(query_builder.get_sql()).fetchall()
    data = list(map(lambda r: {"value":r[suggest_type], "data":r[suggest_type]}, data))

    return jsonify({"suggestions":data}) 

