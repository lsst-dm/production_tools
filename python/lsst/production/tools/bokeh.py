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

from datetime import datetime, timezone
from flask import Blueprint, Flask, render_template, url_for
import urllib.parse
bp = Blueprint("bokeh", __name__, url_prefix="/plot-navigator/bokeh", static_folder="../../../../static")

from bokeh.embed import json_item
from bokeh.plotting import figure
from bokeh.resources import CDN

import asyncio
import json
import os

from . import bokehPlotUtils

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


# async def readFromSasquatch(efdClientName, dataBaseName, dataSourceStr, datetimeStart, datetimeEnd):
async def readFromSasquatch(datetimeStart, datetimeEnd, dataSourceStr, instrument):
    from lsst_efd_client import EfdClient

    efdClientName = "usdfdev_efd"
    dataBaseName = "lsst.dm"

    dataType = f"{dataBaseName}.{dataSourceStr}"
    efd_client = EfdClient(efdClientName, db_name=dataBaseName)
    query = f"SELECT * FROM \"{dataType}\" WHERE time >= '{datetimeStart}' AND " \
            f"time <= '{datetimeEnd}' AND dataset_tag='LSSTComCamSim/rapid_analysis'"
    print("Reading data from Sasquatch with query:")
    print(query)
    visitDataAll = await efd_client.influx_client.query(query)

    if len(visitDataAll) == 0:
        raise RuntimeError("No data found in Sasquatch with search constraints.")

    # Don't assume data are sorted by visitId
    visitDataAll.sort_values(["visit", "detector"], ascending=[True, True], inplace=True)
    dayObsStart = datetimeStart[:10]
    dayObsEnd = str(datetimeEnd)[:10]
    print("dayObsStart = {}  dayObsEnd = {}".format(dayObsStart, dayObsEnd))

    currentUtc = datetime.now(timezone.utc)
    currentYear = currentUtc.year
    dayObsStartStrip = dayObsStart.replace("-", "")
    dayObsEndStrip = dayObsEnd.replace("-", "")
    # LSSTComCamSim data begin with 7024 (i.e. not 2024), so we need to account
    # for the this...
    visitList = list(set(visitDataAll["visit"]))
    minVisitYear = int(str(min(visitList))[:4])
    yearOffset = int((minVisitYear - currentYear)/1000)
    visitDayObsStartInt = int(dayObsStartStrip) + yearOffset*10000000
    visitDayObsEndInt = int(dayObsEndStrip) + yearOffset*10000000
    visitSelectMask = []
    for visit in visitDataAll["visit"].values:
        visitDayObsInt = int(visit[:8])
        if visitDayObsInt >= visitDayObsStartInt and visitDayObsInt <= visitDayObsEndInt:
            visitSelectMask.append(True)
        else:
            visitSelectMask.append(False)
    visitDataAll = visitDataAll[visitSelectMask].copy()
    if len(visitDataAll) == 0:
        raise RuntimeError("No data found with search constraints.")
    visitDataAll = bokehPlotUtils.addMetricColumns(visitDataAll)
    visitDataAll = bokehPlotUtils.addSeqNumColumn(visitDataAll)
    if instrument is not None:
        print("Selecting data from instrument: {}".format(instrument))
        visitDataAll = visitDataAll[visitDataAll["instrument"].values == instrument]
    else:
        print("WARNING: no instrument has been specified.  Use --instrument INSTRUMENTNAME to set one.")
    nDataId = len(visitDataAll)
    if nDataId == 0:
        raise RuntimeError("No data found with search and instrument constraints.")

    visitList = list(set(visitDataAll["visit"]))
    print("minVisit = {}  maxVisit = {}".format(min(visitList), max(visitList)))

    return visitDataAll


def make_plot0(queryTable):
    p = figure(title = "Consdb", sizing_mode="fixed", width=500, height=400)
    p.xaxis.axis_label = "exposure id"
    p.yaxis.axis_label = "Median psf_sigma"
    p.scatter(queryTable['exposure_id'], queryTable['psf_sigma_median'], fill_alpha=0.2, size=10)
    return p


def make_plot(queryTable, xCol="visit", yCol="zeroPoint"):
    p = figure(title = "Lauren Testing", sizing_mode="fixed", width=500, height=400)
    p.xaxis.axis_label = xCol
    p.yaxis.axis_label = yCol
    p.scatter(queryTable[xCol], queryTable[yCol], fill_alpha=0.2, size=10)
    return p

@bp.route("/")
def index():

    debug_text = ""

    return render_template("bokeh/index.html", debug_text=debug_text, resources=CDN.render())

@bp.route("/plot1")
def plot1():
    dataSourceStr = "calexpSummaryMetrics"
    instrument = "LSSTComCamSim"
    dayObsStart = "2024-06-25"
    dayObsEnd = "2024-06-27 12:00:00"
    visitDataAll = asyncio.run(readFromSasquatch(dayObsStart, dayObsEnd, dataSourceStr, instrument))

    plotTitleStr = "Per-Detector effTime Metrics"
    plotNameStr = "effTimeMetrics" + "_" + dayObsStart + "_" + dayObsEnd
    xColList = ["seqNum", "seqNum", "seqNum",
                "seqNum", "seqNum", "seqNum",
                "seqNum", "seqNum"]
    yColList = ["psfFwhm", "expTimeScaledZp", "skyBg",
                "effTimePsfSigmaScale", "effTimeZeroPointScale", "effTimeSkyBgScale",
                "effTime", "effTimeScale"]
    p = bokehPlotUtils.makeCorrPlots(
        visitDataAll, xColList, yColList, plotTitleStr, plotNameStr, dataSourceStr,
        instrument=instrument, butler=None, setXRange=True, setYRange=False, saveDir=None,
        plotWidth=350, plotHeight=350
    )

    return json.dumps(json_item(p, "plotdiv"))


def plot0():

    table = readFromConsDb("2024-06-18", "2024-06-18")

    p = make_plot(table)
    return json.dumps(json_item(p, "plotdiv"))


