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
import urllib.parse
import fnmatch

import boto3
import botocore
import numpy as np
import yaml
from flask import Blueprint, Flask, render_template, url_for
from lsst.daf.butler import Butler, MissingDatasetTypeError

from .htmlUtils import *

bp = Blueprint(
    "metrics",
    __name__,
    url_prefix="/plot-navigator/metrics",
    static_folder="../../../../static",
)

REPO_NAMES = os.getenv("BUTLER_REPO_NAMES").split(",")


def shorten_repo(repo_name):
    """
    Return the repo name without any '/repo/' prefix
    """
    return repo_name.split("/")[-1]


@bp.route("/")
def index():

    # collection_names = ["u/sr525/metricsPlotsPDR2_wholeSky"]
    official_collection_entries = []
    user_collection_entries = []

    session = boto3.Session(profile_name="rubin-plot-navigator")
    s3_client = session.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    try:

        is_truncated = True
        marker = ""

        while is_truncated:
            response = s3_client.list_objects(
                Bucket="rubin-plot-navigator", Marker=marker
            )
            is_truncated = response["IsTruncated"]
            print(
                f"Number of responses {len(response['Contents'])} truncated {is_truncated}"
            )
            for entry in response["Contents"]:
                marker = entry["Key"]
                for repo in REPO_NAMES:
                    repo_encoded = urllib.parse.quote_plus(repo)

                    if entry["Key"].startswith(repo_encoded):
                        collection_enc = (
                            entry["Key"]
                            .replace(repo_encoded + "/collection_", "", 1)
                            .replace(".json.gz", "")
                        )
                        collection = urllib.parse.unquote(collection_enc)

                        if collection.startswith("u"):
                            user_collection_entries.append(
                                {
                                    "name": collection,
                                    "updated": entry["LastModified"],
                                    "repo": shorten_repo(repo),
                                    "url": urllib.parse.quote(collection, safe=""),
                                }
                            )
                        else:
                            official_collection_entries.append(
                                {
                                    "name": collection,
                                    "updated": entry["LastModified"],
                                    "repo": shorten_repo(repo),
                                    "url": urllib.parse.quote(collection, safe=""),
                                }
                            )

    except botocore.exceptions.ClientError as e:
        print(e)

    official_collection_entries.sort(key=lambda x: x["updated"], reverse=True)
    user_collection_entries.sort(key=lambda x: x["updated"], reverse=True)

    return render_template(
        "metrics/index.html",
        collection_entries=official_collection_entries,
        user_collection_entries=user_collection_entries,
    )


@bp.route("/collection/<repo>/<url:collection>/infoPage")
def infoPage(repo, collection):
    expanded_repo_name = None

    if repo in REPO_NAMES:
        expanded_repo_name = repo
    else:
        for test_name in REPO_NAMES:
            if repo == test_name.split("/")[-1]:
                expanded_repo_name = f"/repo/{repo}"

    if not expanded_repo_name:
        return {"error": f"Invalid repo name {repo}, collection {collection}"}, 404

    butler = Butler(expanded_repo_name)

    try:
        tables = butler.registry.queryDatasets("*etricsTable", collections=collection)
        table_names = list(set([table.datasetType.name for table in tables]))
    except MissingDatasetTypeError as e:
        table_names = []

    if len(table_names) > 0:
        # This is hacky and assumes that everything has
        # the same skymap
        dataId = list(tables)[0].dataId

    session = boto3.Session(profile_name="rubin-plot-navigator")
    s3_client = session.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    metric_threshold_filename = "metricInformation.yaml"
    try:
        response = s3_client.get_object(
            Bucket="rubin-plot-navigator", Key=metric_threshold_filename
        )
        metric_defs = yaml.safe_load(response["Body"])
    except botocore.exceptions.ClientError as e:
        print(e)

    if "objectTableCore_metricsTable" in table_names:
        t = butler.get(
            "objectTableCore_metricsTable", collections=collection, dataId=dataId
        )
        metrics = [
            "wPerpCModel_wPerp_cModelFlux_median",
            "psfCModelScatter_i_psf_cModel_diff_median",
        ]
        worst_coadd, bad_ids = worst(t, metrics, "tract")
        col_dict = {
            "id_col": "tract",
            "table_cols": ["corners", "nPatches", "nInputs", "failed metrics"],
            "shape_cols": ["shapeSizeFractionalDiff", "e1Diff", "e2Diff"],
            "photom_cols": ["psfCModelScatter"],
            "stellar_locus_cols": ["yPerp", "wPerp", "xPerp"],
            "sky_cols": ["skyFluxStatisticMetric"],
        }
        prefix = ""
        headers = ["tract"] + col_dict["table_cols"]
        for shape_col in col_dict["shape_cols"]:
            headers.append(shape_col + "<BR>high SN stars")
            headers.append(shape_col + "<BR>low SN stars")
        headers += col_dict["stellar_locus_cols"]
        headers += col_dict["photom_cols"]
        for col in col_dict["sky_cols"]:
            headers.append(col + "<BR>mean, stdev")
            headers.append(col + "<BR>median, sigmaMAD")

        coadd_headers, bands = make_table_headers(t, headers)
        coadd_content = make_table_cells(bad_ids, col_dict, bands, metric_defs, prefix)

    else:
        worst_coadd = []
        coadd_headers = []
        coadd_content = {}

    # Currently there are no visit level tables being made
    worst_visit = []

    return render_template(
        "metrics/infoPage.html",
        collection=collection,
        repo=repo,
        tables=table_names,
        worst_coadd=worst_coadd,
        coadd_headers=coadd_headers,
        coadd_content=coadd_content,
        worst_visit=worst_visit,
    )


@bp.route("/generalTable/<repo>/<url:collection>/<table_name>")
def generalTable(repo, collection, table_name):
    """Make all the information needed to supply to the template
    for the tract summary table.

    Currently set up to take the standard columns from the
    analyzeObjectTableTract portion of the
    coaddObjectCore pipeline metrics.

    The thresholds for the metrics are in the metricDefs
    yaml file.

    The repo name provided must not contain slashes, so the supplied
    repo name is matched against possible values in the REPO_NAMES
    environment variable after removing any '/repo/' prefix from
    those names.
    """
    expanded_repo_name = None

    if repo in REPO_NAMES:
        expanded_repo_name = repo
    else:
        for test_name in REPO_NAMES:
            if repo == test_name.split("/")[-1]:
                expanded_repo_name = f"/repo/{repo}"

    if not expanded_repo_name:
        return {"error": f"Invalid repo name {repo}, collection {collection}"}, 404

    butler = Butler(expanded_repo_name)

    table_name_short = table_name.split("/")[-1]
    tables = butler.registry.queryDatasets(table_name, collections=collection)
    for table in tables:
        dataId = table.dataId
    t = butler.get(table_name, collections=collection, dataId=dataId)

    # Empty string in source cols is for source count
    if table_name == "calibrate_metadata_metricsTable":
        prefix = "calexpMetadataMetrics"
        col_dict = {
            "id_col": "visit",
            "table_cols": ["day_obs", "detector", "band", "failed metrics"],
            "footprint_cols": ["positive", "negative", "sky"],
            "source_cols": ["", "saturated", "bad"],
            "mask_cols": [
                "bad",
                "cr",
                "crosstalk",
                "edge",
                "intrp",
                "no_data",
                "detected",
                "detected_negative",
                "sat",
                "streak",
                "suspect",
                "unmasked_nan",
            ],
        }

        headers = (
            ["visit"] + col_dict["table_cols"] + ["footprints", "sources", "masks"]
        )

    if table_name == "objectTableCore_metricsTable":
        col_dict = {
            "id_col": "tract",
            "table_cols": ["corners", "nPatches", "nInputs", "failed metrics"],
            "shape_cols": ["shapeSizeFractionalDiff", "e1Diff", "e2Diff"],
            "photom_cols": ["psfCModelScatter"],
            "stellar_locus_cols": ["yPerp", "wPerp", "xPerp"],
            "sky_cols": ["skyFluxStatisticMetric"],
        }
        prefix = ""
        headers = ["tract"] + col_dict["table_cols"]
        for shape_col in col_dict["shape_cols"]:
            headers.append(shape_col + "<BR>high SN stars")
            headers.append(shape_col + "<BR>low SN stars")
        headers += col_dict["stellar_locus_cols"]
        headers += col_dict["photom_cols"]
        for col in col_dict["sky_cols"]:
            headers.append(col + "<BR>mean, stdev")
            headers.append(col + "<BR>median, sigmaMAD")

    sar_cols = []
    for num in ["1", "2", "3"]:
        for stat in ["AM", "AF", "AD"]:
            sar_cols.append(("stellarAstrometricRepeatability" + num, stat + num))

    if table_name == "matchedVisitCore_metricsTable":
        col_dict = {"id_col": "tract",
                "table_cols": ["corners", "failed metrics"],
                "sasr_cols": ["dmL2AstroErr"],
                "var1_band_var2": sar_cols +
                                  [("stellarPhotometricRepeatability", "stellarPhotRepeatStdev"),
                                   ("stellarPhotometricRepeatability", "stellarPhotRepeatOutlierFraction"),
                                   ("stellarPhotometricRepeatability", "ct"),
                                   ("stellarPhotometricResidualsCalib", "photResidTractSigmaMad"),
                                   ("stellarPhotometricResidualsCalib", "photResidTractStdev"),
                                   ("stellarPhotometricResidualsCalib", "photResidTractMedian")]}
        prefix = ""
        headers = ["tract"] + col_dict["table_cols"]
        headers += ["Stellar Ast Self Rep"]
        for (line1, line2) in col_dict["var1_band_var2"]:
            headers.append(line1 + "<BR>" + line2)

    if fnmatch.fnmatch(table_name, "objectTable_tract_*_match_astrom_metricsTable"):
        col_dict = {"id_col": "tract",
                    "table_cols": ["corners", "failed metrics"],
                    "var1_band_var2": [("astromDiffMetrics", "AA1_RA_coadd"),
                                       ("astromDiffMetrics", "AA1_sigmaMad_RA_coadd"),
                                       ("astromDiffMetrics", "AA1_Dec_coadd"),
                                       ("astromDiffMetrics", "AA1_sigmaMad_Dec_coadd"),
                                       ("astromDiffMetrics", "AA1_tot_coadd"),
                                       ("astromDiffMetrics", "AA1_sigmaMad_tot_coadd")]}
        prefix = ""
        headers = ["tract"] + col_dict["table_cols"]
        for (line1, line2) in col_dict["var1_band_var2"]:
            headers.append(line1 + "<BR>" + line2)


    session = boto3.Session(profile_name="rubin-plot-navigator")
    s3_client = session.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    metric_threshold_filename = "metricInformation.yaml"
    try:
        response = s3_client.get_object(
            Bucket="rubin-plot-navigator", Key=metric_threshold_filename
        )
        metric_defs = yaml.safe_load(response["Body"])
    except botocore.exceptions.ClientError as e:
        print(e)

    # Make the headers for the table
    # Pulls the bands out of the coadd tables, ignore for visits
    header_dict, bands = make_table_headers(t, headers)

    # Make the content for the table
    content_dict = make_table_cells(t, col_dict, bands, metric_defs, prefix)
    return render_template(
        "metrics/tracts.html",
        header_dict=header_dict,
        content_dict=content_dict,
        collection=collection,
    )


@bp.route("/histograms/<collection_name>")
def histograms(collection_name):

    bands = ["g", "r", "i", "z", "y"]

    return render_template("metrics/histograms.html")


@bp.route("/tract/<collection_name>/<tract>")
def single_tract(collection_name, tract):

    collection_name = urllib.parse.unquote(collection_name)

    return render_template("metrics/single_tract.html", tract=tract)


@bp.route("/report/<collection_name>/<metric>")
def report_page(collection_name, metric):

    return render_template("metrics/report_page.html")
