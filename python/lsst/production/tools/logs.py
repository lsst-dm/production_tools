
from flask import Flask, Blueprint, render_template, request, jsonify
import lsst.daf.butler as dafButler

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route("/")
def index():
    return render_template("logs/index.html")

@bp.route("/collections")
def collections():
    search_term = request.args.get('term')

    butler = dafButler.Butler("/Users/ctslater/ci_imsim/DATA/butler.yaml")
    output = []
    for collection in butler.registry.queryCollections(search_term + "*"):
        output.append({"id": collection, "label": collection, "value": collection})

    return jsonify(output)



