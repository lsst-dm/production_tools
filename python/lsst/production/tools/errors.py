
from flask import Flask, Blueprint, render_template

from collections import defaultdict
import datetime
import json
import os

import google.api_core.exceptions
from google.cloud import storage
from textdistance import levenshtein

bp = Blueprint('errors', __name__, url_prefix='/errors')


# LOG_BUCKET="drp-us-central1-logging"
# LOG_PREFIX="panda-rubinlog"

LOG_BUCKET=os.getenv("LOG_BUCKET")
LOG_PREFIX=os.getenv("LOG_PREFIX")

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


def download_logs(bucket, prefix, year, month, day):

    search_fmt_string = "{base:s}/{year:d}/{month:02d}/{day:02d}/"

    search_prefix = search_fmt_string.format(
        base=prefix, year=year, month=month, day=day
    )

    storage_client = storage.Client.create_anonymous_client()

    bucket = storage_client.bucket(bucket)

    files_to_download = bucket.list_blobs(prefix=search_prefix)

    logs = []

    for bucket_file in files_to_download:
        json_string = bucket_file.download_as_string()

        for line in json_string.decode().split("\n"):
            if len(line) == 0:
                continue
            json_value = json.loads(line)
            logs.append(json_value)

    return logs


@bp.route("/")
def index():
    return render_template("errors/index.html")

@bp.route("/day/<int:year>/<int:month>/<int:day>")
def day(year=0, month=0, day=0):

    if(year == 0):
        return "Invalid parameters"


    date_string="{:4d}-{:02d}-{:02d}".format(year, month, day)

    logs = download_logs(
        bucket,
        prefix,
        year,
        month,
        day,
    )

    summary = parse_logs_into_summary(logs)

    return render_template("errors/day.html", summary=summary,
                           date_string=date_string)

