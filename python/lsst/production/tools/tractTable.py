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

from lsst.daf.butler import Butler

from flask import Blueprint, Flask, render_template, url_for
import numpy as np
import urllib.parse
import yaml
import boto3
import botocore
import os

bp = Blueprint("metrics", __name__, url_prefix="/plot-navigator/metrics", static_folder="../../../../static")

NO_BUTLER = True

@bp.route("/")
def index():

    collection_names = ["u/sr525/metricsPlotsPDR2_wholeSky"]

    collection_entries = [{"name": name, "url": urllib.parse.quote(name, safe='')} for name in collection_names]

    return render_template("metrics/index.html",
                           collection_entries=collection_entries)


def mkTableValue(t, metricDefs, valColName, sigColName, n):
    if valColName in t.columns and sigColName in t.columns:
        val = t[valColName][n]
        valStr = f"{val:.3g}"
        sig = t[sigColName][n]
        sigStr = f"{sig:.3g}"
    elif valColName in t.columns and sigColName not in t.columns:
        val = t[valColName][n]
        valStr = f"{val:.3g}"
        sigStr = "-" 
    elif valColName not in t.columns and sigColName in t.columns:
        valStr = "_"
        sig = t[sigColName][n]
        sigStr = f"{sig:.3g}"
    else:
        return None, None

    if np.isnan(val):
        valStr = f"<FONT CLASS=nanValue>{val:.3g} </FONT>"
    if np.isnan(sig):
        sigStr = f"<FONT CLASS=nanValue>{sig:.3g}</FONT>\n"
    if valColName in metricDefs:
        highVal = metricDefs[valColName]["highThreshold"]
        lowVal = metricDefs[valColName]["lowThreshold"]
        link = metricDefs[valColName]["debugGroup"] + "ReportPage.html"
        if val < lowVal or val > highVal:
            #valStr = "<FONT CLASS=badValue><A HREF = " + link + f">{val:.3g}</A></FONT> "
            valStr = f"<FONT CLASS=badValue>{val:.3g}</FONT>"
    if sigColName in metricDefs:
        highSig = metricDefs[sigColName]["highThreshold"]
        lowSig = metricDefs[sigColName]["lowThreshold"]
        if sig < lowSig or sig > highSig:
            #sigStr = "<FONT CLASS=badValue><A HREF = " + link + f">{sig:.3g}</A></FONT>\n"
            sigStr = f"<FONT CLASS=badValue>{sig:.3g}</FONT>\n"

    return valStr, sigStr


def mkTableHeaders(t):

    colFirst = []
    bands = []
    for col in t.columns:
        colSections = col.split("_")
        for section in colSections:
            if len(section) == 1:
                bands.append(section)
            colFirst.append(col.split("_")[0])

    bands = list(set(bands))

    tableCols = ["tract", "failed metrics", "corners", "nPatches"]
    shapeCols = ["shapeSizeFractionalDiff", "e1Diff", "e2Diff"]
    photomCols = ["psfCModelScatter"]
    stellarLocusCols = ["yPerpPSF", "yPerpCModel", "wPerpCModel", "wPerpPSFP", "xPerpPSFP", "xPerpCModel"]
    stellarLocusCols = ["yPerp", "wPerp", "xPerp"]
    skyCols = ["skyFluxStatisticMetric"]

    tableHeaders = tableCols
    for shapeCol in shapeCols:
        tableHeaders.append(shapeCol + "<BR>High SN Stars")
        tableHeaders.append(shapeCol + "<BR>Low SN Stars")
    for col in stellarLocusCols:
        tableHeaders.append(col)

    headerList = []
    linkList = []
    headerDict = {}
    for header in tableHeaders:
        if header == "failed metrics":
            # Needs to link to metric fail page
            headerDict[header] = "metrics.index"
        elif header == "corners":
            # Needs to link to metric summary page
            headerDict[header] = "metrics.index"
        else:
            # Needs to link to the correct point on the histogram page
            #headerList.append("<A HREF = histPage.html#" + header.split("<BR>")[0] + f">{header}</A>")
            headerDict[header] = "metrics.index"

    return headerDict, bands

def mkTractCell(tract):
    #tractStr = "<a href='summary" + str(tract) + ".html' class=tract>"
    #tractStr += str(tract) + "</a>"
    tractStr = str(tract)

    return tractStr

def mkSummaryPlotCell(tract):
    plotStr = "<IMG SRC='static/summaryCalexp_" + str(tract) + "_i.png' CLASS=thumbnail>"
    return plotStr

def mkPatchNumCell(t, n, bands):
    patchStr = ""
    for band in ["g", "r", "i", "z", "y"]:
        if band in bands:
            patchCol = "coaddPatchCount_" + band + "_patchCount"
            patchStr += "<B>" + band + "</B>: " + str(int(t[patchCol][n])) + "<BR>\n"

    return patchStr


def mkShapeCols(t, metricDefs, n, bands):
    shapeCols = ["shapeSizeFractionalDiff", "e1Diff", "e2Diff"]
    shapeStrs = []
    for col in shapeCols:
        for sn in ["highSNStars", "lowSNStars"]:
            shapeStr = ""
            for band in ["g", "r", "i", "z", "y"]:
                if band in bands:
                    valColName = col + "_" + band + "_" + sn + "_median"
                    sigColName = col + "_" + band + "_" + sn + "_sigmaMad"
                    valStr, sigStr = mkTableValue(t, metricDefs, valColName, sigColName, n)
                    shapeStr += "<B>" + band + f"</B>: " + valStr + "  <B>&sigma;</B>: " + sigStr + "<BR>\n"
            shapeStrs.append(shapeStr)
    return shapeStrs


def mkStellarLocusCols(t, metricDefs, n):
    rowStrs = []
    stellarLocusCols = ["yPerp", "wPerp", "xPerp"]
    for col in stellarLocusCols:
        for (flux, flux1) in zip(["psfFlux", "CModel"], ["PSF", "CModel"]):
            if col[0] == "w" or col[0] == "x":
                flux1 += "P"
            valColName = col + flux1 + "_" + col + "_" + flux + "_median"
            sigColName = col + flux1 + "_" + col + "_" + flux + "_sigmaMAD"
            valStr, sigStr = mkTableValue(t, metricDefs, valColName, sigColName, n)
            if valStr is None:
                continue
            rowStr = "<B>Med</B>: " + valStr + "  <B>&sigma;</B>: " + sigStr + "<BR>\n"
        rowStrs.append(rowStr)

    return rowStrs


@bp.route("/collection/<collection_urlencoded>")
def collection(collection_urlencoded):

    collection = urllib.parse.unquote(collection_urlencoded)

    bands = ['g','r','i','z','y']

    # tracts = [{"number": 9812}, {"number": 1234}, {"number": 9000}]

    butler = Butler("/repo/main")
    dataId = {"skymap": "hsc_rings_v1", "instrument": "HSC"}
    t = butler.get("objectTableCore_metricsTable", collections=collection, dataId=dataId)

    # with open("../../metricThresholds/metricInformation.yaml", "r") as filename:
    #     metricDefs = yaml.safe_load(filename)

    session = boto3.Session(profile_name='rubin-plot-navigator')
    s3_client = session.client('s3', endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    metric_threshold_filename = "metricInformation.yaml"
    try:
        response = s3_client.get_object(Bucket='rubin-plot-navigator', Key=metric_threshold_filename)
        metricDefs = yaml.safe_load(response["Body"])
    except botocore.exceptions.ClientError as e:
        print(e)


    headerDict, bands = mkTableHeaders(t)
    contentDict = {}
    for (n, tract) in enumerate(t["tract"]):
        rowList = []
        rowList.append(mkTractCell(tract))

        # Add a nan/bad summary cell next but need to calculate these numbers first
        rowList.append("0")
        # Add a summary plot in the i band of the tract
        rowList.append(mkSummaryPlotCell(tract))
        rowList.append(mkPatchNumCell(t, n, bands))
        for cellStr in mkShapeCols(t, metricDefs, n, bands):
            rowList.append(cellStr)
        for cellStr in mkStellarLocusCols(t, metricDefs, n):
            rowList.append(cellStr)

        contentDict[tract] = rowList




    return render_template("metrics/tracts.html", headerDict=headerDict, contentDict=contentDict)

@bp.route("/histograms/<collection_name>")
def histograms(collection_name):

    bands = ['g','r','i','z','y']

    return render_template("metrics/histograms.html")


@bp.route("/tract/<collection_name>/<tract>")
def single_tract(collection_name, tract):

    collection_name = urllib.parse.unquote(collection_name)

    return render_template("metrics/single_tract.html", tract=tract)



