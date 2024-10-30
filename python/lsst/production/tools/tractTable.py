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

NO_BUTLER = True


@bp.route("/")
def index():

    collection_names = ["u/sr525/metricsPlotsPDR2_wholeSky"]

    collection_entries = [
        {"name": name, "url": urllib.parse.quote(name, safe="")}
        for name in collection_names
    ]

    return render_template("metrics/index.html", collection_entries=collection_entries)


@bp.route("/collection/<collection_urlencoded>")
def collection(collection_urlencoded):
    """Make all the information needed to supply to the template
    for the tract summary table.

    Currently set up to take the standard columns from the
    analyzeObjectTableTract portion of the
    coaddObjectCore pipeline metrics.

    The thresholds for the metrics are in the metricDefs
    yaml file.
    """

    collection = urllib.parse.unquote(collection_urlencoded)

    butler = Butler("/repo/main")
    dataId = {"skymap": "hsc_rings_v1", "instrument": "HSC"}
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

        # Add a nan/bad summary cell next but need to calculate these numbers first
        row_list.append("0")
        # Add a summary plot in the i band of the tract
        row_list.append(mk_summary_plot_cell(tract))
        row_list.append(mk_patch_num_cell(t, n, bands))
        # Add the number of inputs
        row_list.append(mk_num_inputs_cell(t, metric_defs, n, bands))

        num_bad = 0
        cell_vals = []
        # Get the number of failed values and prep cell contents
        for cell_val, bad_val, link, debug_group in mk_shape_cols(
            t, metric_defs, n, bands, col_dict
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell details for the stellar locus columns
        for cell_val, bad_val, link, debug_group in mk_stellar_locus_cols(
            t, metric_defs, n, col_dict
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell contents for the photometry columns
        for cell_val, bad_val, link, debug_group in mk_photom_cols(
            t, metric_defs, n, bands, col_dict
        ):
            cell_vals.append((cell_val, link, debug_group))
            if bad_val is not None:
                num_bad += bad_val

        # Make the cell contents for the sky columns
        for cell_val, bad_val, link, debug_group in mk_sky_cols(
            t, metric_defs, n, bands, col_dict
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
        collection_urlencoded=collection_urlencoded,
    )


@bp.route("/histograms/<collection_name>")
def histograms(collection_name):

    bands = ["g", "r", "i", "z", "y"]

    return render_template("metrics/histograms.html")


@bp.route("/tract/<collection_name>/<tract>")
def single_tract(collection_name, tract):

    collection_name = urllib.parse.unquote(collection_name)

    return render_template("metrics/single_tract.html", tract=tract)



