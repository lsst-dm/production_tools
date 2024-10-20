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
        print(arq_job)
        return jsonify({"jobId": arq_job.job_id})

    else:
        abort(400, description=f"Invalid HTTP Method {request.method}")

@bp.route("/job/<job_id>")
async def job(job_id):

    redis_settings = arq.connections.RedisSettings(host=os.getenv("REDIS_HOST"),
                                                   port=os.getenv("REDIS_PORT"))

    redis = await arq.create_pool(redis_settings)
    arq_job = arq.jobs.Job(job_id=job_id, redis=redis)

    return jsonify({"status": (await arq_job.status()).value()})

async def cache_plots(ctx, repo, collection):
    print(f"cache_plots start {repo} {collection}")
    time.sleep(60)
    print(f"cache_plots finished {repo} {collection}")

class Worker:
    functions = [cache_plots]
    redis_settings = redis_settings

