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


from flask import Blueprint, Flask, render_template, url_for
import urllib.parse
bp = Blueprint("metrics", __name__, url_prefix="/metrics")

NO_BUTLER = True

@bp.route("/")
def index():

    collection_names = ["HSC/runs/RC2/w_2024_38"]

    collection_entries = [{"name": name, "url": urllib.parse.quote(name, safe='')} for name in collection_names]

    return render_template("metrics/index.html",
                           collection_entries=collection_entries)


@bp.route("/collection/<collection_urlencoded>")
def collection(collection_urlencoded):

    collection = urllib.parse.unquote(collection_urlencoded)

    bands = ['g','r','i','z','y']

    # tracts = [{"number": 9812}, {"number": 1234}, {"number": 9000}]

    if not NO_BUTLER:
        butler = Butler("/repo/main")
        dataId = {"skymap": "hsc_rings_v1", "instrument": "HSC"}
        metricsTable = butler.get("objectTableCore_metricsTable", collections=collection, dataId=dataId)
        # Load metricsTable from a file

    tracts = metricsTable['tract']

    return render_template("metrics/tracts.html", tracts=tracts, bands=bands)

@bp.route("/histograms/<collection_name>")
def histograms(collection_name):

    bands = ['g','r','i','z','y']

    return render_template("metrics/histograms.html")


@bp.route("/tract/<collection_name>/<tract>")
def single_tract(collection_name, tract):

    collection_name = urllib.parse.unquote(collection_name)

    return render_template("metrics/single_tract.html", tract=tract)



