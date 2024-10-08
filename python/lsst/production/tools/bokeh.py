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
bp = Blueprint("bokeh", __name__, url_prefix="/bokeh")

from bokeh.embed import json_item
from bokeh.plotting import figure
from bokeh.resources import CDN

import json
import os


def readFromConsDb(dayObsStart, dayObsEnd):
    from lsst.summit.utils import ConsDbClient
    with open(os.path.expandvars("${HOME}/.consDB_token"), "r") as f:
        token = f.read()
    consDbClient = ConsDbClient(f"https://user:{token}@usdf-rsp.slac.stanford.edu/consdb")

    dayObsStartInt = int(dayObsStart.replace("-", ""))
    dayObsEndInt = int(dayObsEnd.replace("-", ""))
    instrument = "lsstcomcamsim"
    whereStr = f'''
        WHERE obs_start_mjd IS NOT NULL
        AND s_ra IS NOT NULL
        AND s_dec IS NOT NULL
        AND sky_rotation IS NOT NULL
        AND ((band IS NOT NULL) OR (physical_filter IS NOT NULL))
        AND day_obs >= {dayObsStartInt}
    '''

    exposure_query = f'''SELECT * FROM cdb_{instrument}.exposure {whereStr}'''
    visit1_query = f'''SELECT * FROM cdb_{instrument}.visit1 {whereStr}'''
    ccdexposure_quicklook_query = f'''SELECT * FROM cdb_{instrument}.ccdexposure_quicklook'''
    ccdvisit1_quicklook_query = f'''SELECT * FROM cdb_{instrument}.ccdvisit1_quicklook JOIN cdb_{instrument}.visit1 ON cdb_{instrument}.ccdvisit1_quicklook.ccdvisit_id  = cdb_{instrument}.exposure.ccdvisit_id '''

    combinedQuery = f'''
        SELECT exposure_id, cdb_{instrument}.visit1_quicklook.psf_sigma_median as psf_sigma_median FROM 
        cdb_{instrument}.visit1_quicklook
        JOIN cdb_{instrument}.exposure ON (cdb_{instrument}.visit1_quicklook.visit_id =cdb_{instrument}.exposure.exposure_id)
        WHERE day_obs = {dayObsStartInt}
    '''

    return consDbClient.query(combinedQuery)


def make_plot(queryTable):
    p = figure(title = "Consdb", sizing_mode="fixed", width=500, height=400)
    p.xaxis.axis_label = "exposure id"
    p.yaxis.axis_label = "Median psf_sigma"
    p.scatter(queryTable['exposure_id'], queryTable['psf_sigma_median'], fill_alpha=0.2, size=10)
    return p

@bp.route("/")
def index():

    debug_text = ""

    return render_template("bokeh/index.html", debug_text=debug_text, resources=CDN.render())

@bp.route("/plot1")
def plot1():

    table = readFromConsDb("2024-06-18", "2024-06-18")

    p = make_plot(table)
    return json.dumps(json_item(p, "plotdiv"))


