
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

@bp.route("/dataId")
def dataId():
    butler = dafButler.Butler("/Users/ctslater/ci_imsim/DATA/butler.yaml")

    collection = request.args.get("collection")

    dimensions = ["visit", "detector", "tract", "patch"]
    dataId = {"instrument": "LSSTCam-imSim"}
    for dim in dimensions:
        value = request.args.get(dim, type=int)
        if(value is not None):
            dataId[dim] = value

    if(collection is None):
        return "Must specify a collection"

    dataId_string = ", ".join("{:s} {}".format(dim.capitalize(), val) for (dim, val) in dataId.items())

    dataRefs = butler.registry.queryDatasets("*_log", dataId=dataId,
                                             collections=collection)

    logs = [{"datasetName": x.datasetType.name,
             "uuid": x.id }
            for x in dataRefs]

    return render_template("logs/dataId.html", dataId=dataId_string,
                          collection=collection, logs=logs)

@bp.route("/logfile")
def logfile():
    butler = dafButler.Butler("/Users/ctslater/ci_imsim/DATA/butler.yaml")
    message_template = """
    <p>{{severity}} - {{message}}</p>
    """

    uuid = request.args.get("uuid")
    datasetRef = butler.registry.getDataset(uuid)
    logs = butler.getDirect(datasetRef)
    return render_template("logs/messages.html", logs=logs)

