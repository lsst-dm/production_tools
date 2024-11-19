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

import boto3
import botocore
import numpy as np
import yaml
from flask import Blueprint, Flask, render_template, url_for
from lsst.daf.butler import Butler

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
    return repo_name.split('/')[-1]


@bp.route("/")
def index():

    #collection_names = ["u/sr525/metricsPlotsPDR2_wholeSky"]
    official_collection_entries = []
    user_collection_entries = []

    session = boto3.Session(profile_name="rubin-plot-navigator")
    s3_client = session.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    try:

        is_truncated = True
        marker = ""

        while is_truncated:
            response = s3_client.list_objects(
                Bucket="rubin-plot-navigator",
                Marker=marker
            )
            is_truncated = response['IsTruncated']
            print(f"Number of responses {len(response['Contents'])} truncated {is_truncated}")
            for entry in response['Contents']:
                marker = entry['Key']
                for repo in REPO_NAMES:
                    repo_encoded = urllib.parse.quote_plus(repo)

                    if entry['Key'].startswith(repo_encoded):
                        collection_enc = entry['Key'].replace(repo_encoded + "/collection_", "", 1).replace(".json.gz", "")
                        collection = urllib.parse.unquote(collection_enc)

                        if collection.startswith('u'):
                            user_collection_entries.append({"name": collection,
                                                            "updated": entry['LastModified'],
                                                            "repo": shorten_repo(repo), "url":
                                                            urllib.parse.quote(collection, safe="")})
                        else:
                            official_collection_entries.append({"name": collection,
                                                                "updated": entry['LastModified'],
                                                                "repo": shorten_repo(repo), "url":
                                                                urllib.parse.quote(collection, safe="")})


    except botocore.exceptions.ClientError as e:
        print(e)

    official_collection_entries.sort(key=lambda x: x['updated'], reverse=True)
    user_collection_entries.sort(key=lambda x: x['updated'], reverse=True)

    return render_template("metrics/index.html", collection_entries=official_collection_entries,
                           user_collection_entries=user_collection_entries)


@bp.route("/collection/<repo>/<url:collection>")
def collection(repo, collection):
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
            if(repo == test_name.split('/')[-1]):
                expanded_repo_name = f"/repo/{repo}"

    if not expanded_repo_name:
        return {"error": f"Invalid repo name {repo}, collection {collection}"}, 404

    butler = Butler(expanded_repo_name)
    if(expanded_repo_name == "/repo/main"):
        dataId = {"skymap": "hsc_rings_v1", "instrument": "HSC"}
    else:
        dataId = {"skymap": "lsst_cells_v1", "instrument": "LSSTComCam"}

    t = butler.get(
        "objectTableCore_metricsTable", collections=collection, dataId=dataId
    )

    col_dict = {
        "table_cols": ["tract", "corners", "nPatches", "nInputs", "failed metrics"],
        "shape_cols": ["shapeSizeFractionalDiff", "e1Diff", "e2Diff"],
        "photom_cols": ["psfCModelScatter"],
        "stellar_locus_cols": ["yPerp", "wPerp", "xPerp"],
        "sky_cols": ["skyFluxStatisticMetric"],
    }
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
    header_dict, bands = mk_table_headers(t, col_dict)

    # Make the content for the table
    content_dict = {}
    for n, tract in enumerate(t["tract"]):
        row_list = []
        row_list.append(mk_tract_cell(tract))

        # Add a summary plot in the i band of the tract
        row_list.append(mk_summary_plot_cell(tract))
        # Add the number of patches
        row_list.append(mk_patch_num_cell(t, n, bands))
        # Add the number of inputs
        row_list.append(mk_num_inputs_cell(t, metric_defs, n, bands))

        num_bad = 0
        cell_vals = []
        # Get the number of failed values and prep cell contents
        for cell_val, bad_val, link, debug_group in mk_shape_cols(
            t, metric_defs, n, bands, col_dict["shape_cols"]
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell details for the stellar locus columns
        for cell_val, bad_val, link, debug_group in mk_stellar_locus_cols(
            t, metric_defs, n, col_dict["stellar_locus_cols"]
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell contents for the photometry columns
        for cell_val, bad_val, link, debug_group in mk_photom_cols(
            t, metric_defs, n, bands, col_dict["photom_cols"]
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell contents for the sky columns
        for cell_val, bad_val, link, debug_group in mk_sky_cols(
            t, metric_defs, n, bands, col_dict["sky_cols"]
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Add a nan/bad summary cell next but need to calculate these numbers first
        row_list.append((num_bad,))
        for val in cell_vals:
            row_list.append(val)

        content_dict[tract] = row_list

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
