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

import datetime
import json
import os
from collections import defaultdict

import google.api_core.exceptions
from flask import Blueprint, Flask, render_template
from google.cloud import storage
from textdistance import levenshtein

bp = Blueprint("errors", __name__, url_prefix="/errors")


# LOG_BUCKET="drp-us-central1-logging"
# LOG_PREFIX="panda-rubinlog"

try:
    LOG_BUCKET = os.environ["LOG_BUCKET"]
    LOG_PREFIX = os.environ["LOG_PREFIX"]
except KeyError:
    print("Must set LOG_BUCKET and LOG_PREFIX environment variables")
    sys.exit(1)

CACHE_DIR = os.getenv("LOG_CACHE_DIR")


def find_matching_messages(new_message, message_list):

    similarity_cut = 5

    # Lots of errors report specific numbers, which are not important
    # in finding matching messages.
    substitutions = {ord("%d" % x): "" for x in range(0, 10)}
    new_msg_filtered = new_message.translate(substitutions)

    for test_message in message_list:
        test_msg_filtered = test_message.translate(substitutions)
        if levenshtein.distance(new_msg_filtered, test_msg_filtered) < similarity_cut:
            return test_message

    return None


def parse_logs_into_summary(logs):

    runs = defaultdict(list)
    for log in logs:
        try:
            run = log["jsonPayload"]["MDC"]["RUN"]
        except KeyError:
            continue
        runs[run].append(log)

    output_by_run = []
    for run_name, logs in runs.items():
        messages = defaultdict(set)
        for log in logs:
            message = log["jsonPayload"]["message"]
            label = log["jsonPayload"]["MDC"]["LABEL"]
            msg_key = find_matching_messages(message, messages.keys())
            if msg_key is None:
                msg_key = message

            messages[msg_key].add(label)

        output = {"run_name": run_name, "messages": messages}

        output_by_run.append(output)

    return output_by_run


def download_logs(bucket_name, prefix, year, month, day):

    search_fmt_string = "{base:s}/{year:d}/{month:02d}/{day:02d}/"

    search_prefix = search_fmt_string.format(
        base=prefix, year=year, month=month, day=day
    )

    storage_client = storage.Client.create_anonymous_client()

    bucket = storage_client.bucket(bucket_name)

    files_to_download = bucket.list_blobs(prefix=search_prefix)

    logs = []

    try:
        with open(
            os.path.join(CACHE_DIR, f"etags_{year:d}{month:02d}{day:02d}.json"), "r"
        ) as f:
            old_etags = json.load(f)
    except FileNotFoundError:
        old_etags = {}
    new_etags = {}

    for bucket_file in files_to_download:
        if CACHE_DIR is None:
            json_string = bucket_file.download_as_string().decode()
        else:
            cache_filename = os.path.join(CACHE_DIR, bucket_file.name)
            etag = bucket_file.name
            new_etags[bucket_file.name] = etag

            if old_etags.get(bucket_file.name, "") != etag:
                os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
                bucket_file.download_to_filename(cache_filename, if_etag_not_match=etag)

            with open(cache_filename, "r") as f:
                json_string = f.read()

        for line in json_string.split("\n"):
            if len(line) == 0:
                continue
            json_value = json.loads(line)
            logs.append(json_value)

    with open(
        os.path.join(CACHE_DIR, f"etags_{year:d}{month:02d}{day:02d}.json"), "w"
    ) as f:
        json.dump(new_etags, f)

    return logs


@bp.route("/")
def index():
    return render_template("errors/index.html")


@bp.route("/day/<int:year>/<int:month>/<int:day>")
def day(year=0, month=0, day=0):

    if year == 0:
        return "Invalid parameters"

    date_string = "{:4d}-{:02d}-{:02d}".format(year, month, day)

    logs = download_logs(
        LOG_BUCKET,
        LOG_PREFIX,
        year,
        month,
        day,
    )

    summary = parse_logs_into_summary(logs)

    return render_template("errors/day.html", summary=summary, date_string=date_string)
