# This file is part of production-tools.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import lsst.daf.butler as dafButler
from flask import Blueprint, Flask, jsonify, render_template, request

bp = Blueprint("logs", __name__, url_prefix="/logs")


@bp.route("/")
def index():
    return render_template("logs/index.html")


@bp.route("/collections")
def collections():
    search_term = request.args.get("term")

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
        if value is not None:
            dataId[dim] = value

    if collection is None:
        return "Must specify a collection"

    dataId_string = ", ".join(
        "{:s} {}".format(dim.capitalize(), val) for (dim, val) in dataId.items()
    )

    dataRefs = butler.registry.queryDatasets(
        "*_log", dataId=dataId, collections=collection
    )

    logs = [{"datasetName": x.datasetType.name, "uuid": x.id} for x in dataRefs]

    return render_template(
        "logs/dataId.html", dataId=dataId_string, collection=collection, logs=logs
    )


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
