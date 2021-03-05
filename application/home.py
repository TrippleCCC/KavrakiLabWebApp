from flask import (
        Blueprint, render_template
)

bp = Blueprint("home", __name__, "/")

@bp.route("/", methods=["GET"])
def hello():
    return render_template("base.html")


