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
from flask import Blueprint, Flask, jsonify, request, abort
import arq
import time

import json
import gzip
import urllib.parse
import boto3
import botocore

bp = Blueprint("cache", __name__, url_prefix="/plot-navigator/cache", static_folder="../../../../static")


# PUT /cache/  {repo: "", collection: ""}, return {jobId: ""}
# GET /cache/job/<job_id>, return {status: ""}

@bp.route("/", methods=["PUT"])
async def index():
    redis_settings = arq.connections.RedisSettings(host=os.getenv("REDIS_HOST"),
                                                   port=os.getenv("REDIS_PORT"))

    redis = await arq.create_pool(redis_settings)
    print(f"cache.index() received request: {request}")
    if request.method == 'PUT':

        data = request.get_json()
        arq_job = await redis.enqueue_job("cache_plots", data['repo'], data['collection'])
        return jsonify({"jobId": arq_job.job_id})

    else:
        abort(400, description=f"Invalid HTTP Method {request.method}")

@bp.route("/job/<job_id>")
async def job(job_id):

    redis_settings = arq.connections.RedisSettings(host=os.getenv("REDIS_HOST"),
                                                   port=os.getenv("REDIS_PORT"))

    redis = await arq.create_pool(redis_settings)
    arq_job = arq.jobs.Job(job_id=job_id, redis=redis)

    job_result = await arq_job.result_info()

    return jsonify({"status": await arq_job.status(),
                    "result": job_result.result if job_result is not None else ""})

async def cache_plots(ctx, repo, collection):

    butler = dafButler.Butler(repo)

    try:
        summary = summarize_collection(butler, collection)
    except dafButler.MissingCollectionError as e:
        return f"Error: {e}"

    encoded_collection_name = urllib.parse.quote_plus(collection)
    encoded_repo = urllib.parse.quote_plus(repo)
    filename = f"{encoded_repo}/collection_{encoded_collection_name}.json.gz"

    session = boto3.Session(profile_name='rubin-plot-navigator')
    s3_client = session.client('s3', endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    json_string = json.dumps(summary)
    json_gzipped = gzip.compress(json_string.encode())

    try:
        # response = s3_client.upload_fileobj(json_gzipped, 'rubin-plot-navigator', filename)
        response = s3_client.put_object(Body=json_gzipped, Bucket='rubin-plot-navigator', Key=filename)
    except botocore.exceptions.ClientError as e:
        return f"Error: {e}"


    n_plots = len(summary['tracts']) + len(summary['visits']) + len(summary['global'])
    return f"Success: {n_plots} plots"

class Worker:
    functions = [cache_plots]
    redis_settings = arq.connections.RedisSettings(host=os.getenv("REDIS_HOST"),
                                                   port=os.getenv("REDIS_PORT"))


def summarize_collection(butler, collection_name):

    out = {}

    summary = butler.registry.getCollectionSummary(collection_name)

    tract_plot_types = [x for x in list(summary.dataset_types) if x.storageClass_name == "Plot" and 'tract' in x.dimensions]
    visit_plot_types = [x for x in list(summary.dataset_types) if x.storageClass_name == "Plot" and 'visit' in x.dimensions]
    detector_plot_types = [x for x in list(summary.dataset_types) if x.storageClass_name == "Plot" and 'detector' in x.dimensions and 'visit' not in x.dimensions]
    global_plot_types = [x for x in list(summary.dataset_types) if x.storageClass_name == "Plot" and 'tract' not in x.dimensions and 'visit' not in x.dimensions]

    tract_datasets = list(butler.registry.queryDatasets(tract_plot_types, collections=collection_name, findFirst=True))
    out['tracts'] = {}
    for plot_type in tract_plot_types:
        ref_dicts = [{"dataId": json.dumps(dict(datasetRef.dataId.mapping)), "id": str(datasetRef.id)} for datasetRef in tract_datasets if datasetRef.datasetType == plot_type]
        if(len(ref_dicts) > 0):
            out['tracts'][plot_type.name] = ref_dicts

    visit_datasets = list(butler.registry.queryDatasets(visit_plot_types, collections=collection_name, findFirst=True))
    out['visits'] = {}
    for plot_type in visit_plot_types:
        ref_dicts = [{"dataId": json.dumps(dict(datasetRef.dataId.mapping)), "id": str(datasetRef.id)} for datasetRef in visit_datasets if datasetRef.datasetType == plot_type]
        if(len(ref_dicts) > 0):
            out['visits'][plot_type.name] = ref_dicts

    global_datasets = list(butler.registry.queryDatasets(global_plot_types, collections=collection_name, findFirst=True))
    out['global'] = {}
    for plot_type in global_plot_types:
        ref_dicts = [{"dataId": json.dumps(dict(datasetRef.dataId.mapping)), "id": str(datasetRef.id)} for datasetRef in global_datasets if datasetRef.datasetType == plot_type]
        if(len(ref_dicts) > 0):
            out['global'][plot_type.name] = ref_dicts

    #print("Tract plots: {:d}".format(len(out['tracts'])))
    #print("Visit plots: {:d}".format(len(out['visits'])))
    #print("Global plots: {:d}".format(len(out['global'])))

    return out
