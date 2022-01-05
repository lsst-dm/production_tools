
from flask import Flask, Blueprint
import lsst.daf.butler as dafButler

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route("/")
def index():
    return "<p>Log Viewer Index</p>"

@bp.route("/collections")
def collections():
    butler = dafButler.Butler("/Users/ctslater/ci_imsim/DATA/butler.yaml")
    out_string = "<H1>Collections</H1>"
    out_string += "<ul>"
    for collection in butler.registry.queryCollections():
        out_string += "<li>" + collection
    out_string += "</ul>"

    return out_string



