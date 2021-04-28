import time
import os
import io
import zipfile
import re
from web_app.util.regex_util import create_peptide_regex, add_bold_tags_to_peptides 
from pypika import Query, Table, Tables, Order
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
    confirmation_type = request.form.get("confirmation-type")
    results_per_page = request.form.get("results-per-page")

    if not confirmation_type:
        flash("Please select Confirmation type.", "errors")
        return redirect(url_for(".home"))

    return redirect(
            url_for(".results", allele=allele, peptide=peptide, 
                binder=binder, non_binder=non_binder, peptide_regex=peptide_regex,
                confirmation_type=confirmation_type, results_per_page=results_per_page))


@bp.route("/results", methods=["GET"])
def results():
    db = get_db()
    data = []

    allele = request.args.get("allele")
    peptide = request.args.get("peptide")
    binder = request.args.get("binder")
    non_binder = request.args.get("non_binder")
    peptide_regex = request.args.get("peptide_regex")
    confirmation_type = request.args.get("confirmation_type")
    results_per_page = int(request.args.get("results_per_page"))

    # Ordering parameters
    order_allele = request.args.get("order_allele")
    order_peptide = request.args.get("order_peptide")
    order_binder = request.args.get("order_binder")
    order_conf = request.args.get("order_conf")
    

    # Begin Query building
    if confirmation_type == "singleconf":
        singleconf_files = Table("singleconf_files")
        query_builder = Query.from_(singleconf_files).select(
                singleconf_files.id, singleconf_files.allele, singleconf_files.peptide, 
                singleconf_files.binder, singleconf_files.filepath)
    elif confirmation_type == "multiconf":
        multiconf_files = Table("multiconf_files")
        query_builder = Query.from_(multiconf_files).select(
                multiconf_files.id, multiconf_files.allele, multiconf_files.peptide, 
                multiconf_files.binder, multiconf_files.num_confirmations)

    # Add WHERE conditions for alleles and peptides
    if allele != "any-allele":
        # Process list of alleles
        alleles = list(map(lambda a: a.strip(), allele.split(",")))
        if confirmation_type == "singleconf":
            query_builder = query_builder.where(
                    singleconf_files.allele.isin(alleles))
        elif confirmation_type == "multiconf":
            query_builder = query_builder.where(
                    multiconf_files.allele.isin(alleles))
        # TODO: if any-peptide is selected, we should have links to 
        # pre-zipped files for each allele
    if peptide != "any-peptide" and peptide_regex == "off":
        if confirmation_type == "singleconf":
            query_builder = query_builder.where(singleconf_files.peptide == peptide)
        elif confirmation_type == "multiconf":
            query_builder = query_builder.where(multiconf_files.peptide == peptide)


    # Add IN clause for binders
    binders = []
    if binder == "on":
        binders.append(1)
    if non_binder == "on":
        binders.append(0)

    if confirmation_type == "singleconf":
        query_builder = query_builder.where(singleconf_files.binder.isin(binders))
    elif confirmation_type == "multiconf":
        query_builder = query_builder.where(multiconf_files.binder.isin(binders))


    # apply ordering to resutls
    if confirmation_type == "singleconf":
        if order_allele == "asc":
            query_builder = query_builder.orderby(singleconf_files.allele, order=Order.asc)
        elif order_allele == "desc":
            query_builder = query_builder.orderby(singleconf_files.allele, order=Order.desc)

        if order_peptide == "asc":
            query_builder = query_builder.orderby(singleconf_files.peptide, order=Order.asc)
        elif order_peptide == "desc":
            query_builder = query_builder.orderby(singleconf_files.peptide, order=Order.desc)

        if order_binder == "asc":
            query_builder = query_builder.orderby(singleconf_files.binder, order=Order.asc)
        elif order_binder == "desc":
            query_builder = query_builder.orderby(singleconf_files.binder, order=Order.desc)
    elif confirmation_type == "multiconf":
        if order_conf == "asc":
            query_builder = query_builder.orderby(multiconf_files.num_confirmations, order=Order.asc)
        elif order_conf == "desc":
            query_builder = query_builder.orderby(multiconf_files.num_confirmations, order=Order.desc)

        if order_allele == "asc":
            query_builder = query_builder.orderby(multiconf_files.allele, order=Order.asc)
        elif order_allele == "desc":
            query_builder = query_builder.orderby(multiconf_files.allele, order=Order.desc)

        if order_peptide == "asc":
            query_builder = query_builder.orderby(multiconf_files.peptide, order=Order.asc)
        elif order_peptide == "desc":
            query_builder = query_builder.orderby(multiconf_files.peptide, order=Order.desc)

        if order_binder == "asc":
            query_builder = query_builder.orderby(multiconf_files.binder, order=Order.asc)
        elif order_binder == "desc":
            query_builder = query_builder.orderby(multiconf_files.binder, order=Order.desc)


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

    # split data into different pages
    pages = []
    for i in range(0, num_results, int(results_per_page)):
        pages.append(data[i:i+int(results_per_page)])


    # Generate order urls
    parameters = {
            "allele": allele, "peptide": peptide, "binder": binder,
            "non_binder": non_binder, "peptide_regex": peptide_regex,
            "confirmation_type": confirmation_type
            }
    order_urls = {
            "allele_asc": url_for(".results", order_allele="asc", **parameters),
            "allele_desc": url_for(".results", order_allele="desc", **parameters),
            "peptide_asc": url_for(".results", order_peptide="asc", **parameters),
            "peptide_desc": url_for(".results", order_peptide="desc", **parameters),
            "binder_asc": url_for(".results", order_binder="asc", **parameters),
            "binder_desc": url_for(".results", order_binder="desc", **parameters)
            }
    if confirmation_type == "multiconf":
        order_urls["num_confirmations_asc"] = url_for(".results", order_conf="asc", **parameters)
        order_urls["num_confirmations_desc"] = url_for(".results", order_conf="desc", **parameters)

    return render_template("results.html", allele=allele, 
            peptide=peptide, num_results=num_results, query_time=query_time,
            binder=binder, non_binder=non_binder, peptide_regex=peptide_regex,
            confirmation_type=confirmation_type, order_urls=order_urls, pages=pages,
            results_per_page=results_per_page)


@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")

    data = []

    # Begin Query building
    alleles, peptides = Tables("alleles", "peptides")
    allele_builder = Query.from_(alleles)
    peptides_builder = Query.from_(peptides)
    final_query = None

    # Determine the suggestions based on the suggestion type
    if suggest_type == "allele":
        final_query = allele_builder.select(alleles.allele).distinct() \
                .where(alleles.allele.like(f"%{query}%"))
    elif suggest_type == "peptide":
        final_query = peptides_builder.select(peptides.peptide).distinct() \
                .where(peptides.peptide.like(f"%{query}%"))

    # limit suggestions to 5
    final_query = final_query.limit(5)

    # Retrive data and reformat
    data = db.execute(final_query.get_sql()).fetchall()
    data = list(map(lambda r: {"value":r[suggest_type], "data":r[suggest_type]}, data))

    return jsonify({"suggestions":data}) 

