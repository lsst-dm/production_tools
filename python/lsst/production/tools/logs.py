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

import os
import sys

import lsst.daf.butler as dafButler
from flask import Blueprint, Flask, jsonify, render_template, request

bp = Blueprint("logs", __name__, url_prefix="/logs")

try:
    BUTLER_URI = os.environ["BUTLER_URI"]
except KeyError:
    print("Must set environment variable BUTLER_URI")
    sys.exit(1)

#global_butler = dafButler.Butler(BUTLER_URI)

def get_butler():
    return global_butler


@bp.route("/")
def index():
    return render_template("logs/index.html")


@bp.route("/collections")
def collections():
    search_term = request.args.get("term")

    butler = get_butler()
    output = []
    for collection in butler.registry.queryCollections(search_term + "*"):
        output.append({"id": collection, "label": collection, "value": collection})

    return jsonify(output)


@bp.route("/instruments")
def instruments():
    butler = get_butler()

    instrument_recs = butler.registry.queryDimensionRecords("instrument")
    return jsonify([record.name for record in instrument_recs])


@bp.route("/skymaps")
def skymaps():
    butler = get_butler()

    # It would be nice for this to constrain on collection, but not implemented yet.
    skymap_recs = butler.registry.queryDimensionRecords("skymap")
    return jsonify([record.name for record in skymap_recs])


@bp.route("/dataId")
def dataId():
    butler = get_butler()

    collection = request.args.get("collection")

    if collection is None:
        return "Must specify a collection"

    dimension_types = {
        "exposure": int,
        "visit": int,
        "detector": int,
        "tract": int,
        "patch": int,
        "skymap": str,
        "instrument": str,
    }
    dataId = {}
    for dim_name, dim_type in dimension_types.items():
        value = request.args.get(dim_name, type=dim_type)
        if value is not None:
            dataId[dim_name] = value

    required_dimensions = (set(dataId.keys()) - set(["skymap", "instrument"]))
    log_types = butler.registry.queryDatasetTypes("*_log")
    target_dataset_types = filter(lambda datasetType: all([dimension in datasetType.dimensions
                                                           for dimension in required_dimensions]), log_types)
    dataRefs = []
    error_string = ""
    try:
        for dataset_type in target_dataset_types:
            if(len(dataRefs) > 200):
                error_string = "Large number of datasets selected; results truncated."
                break

            dataRefs.extend(butler.registry.queryDatasets(dataset_type, dataId=dataId, collections=collection))
    except (dafButler.registry.RegistryError) as e:

        return render_template(
            "logs/dataId.html", collection=collection, error=str(e),
        )


    logs = [
        {"datasetName": ref.datasetType.name, "uuid": ref.id, "dataId": ref.dataId}
        for ref in dataRefs
    ]

    dataId_string = ", ".join(
        "{:s} {}".format(dim.capitalize(), val) for (dim, val) in dataId.items()
    )

    return render_template(
        "logs/dataId.html", dataId=dataId_string, collection=collection, logs=logs, error=error_string,
    )


@bp.route("/logfile")
def logfile():
    butler = get_butler()
    message_template = """
    <p>{{severity}} - {{message}}</p>
    """

    uuid = request.args.get("uuid")
    datasetRef = butler.registry.getDataset(uuid)
    try:
        logs = butler.getDirect(datasetRef)
    except Exception as e:
        return "Failed to access log file: {}".format(str(e))

    return render_template("logs/messages.html", logs=logs)
