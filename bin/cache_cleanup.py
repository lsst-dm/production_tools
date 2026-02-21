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
import re
import lsst.daf.butler as dafButler

import urllib.parse
import boto3
import botocore


def check_existence(butler, encoded_collection_filename):

    m = re.search("/collection_([a-zA-Z0-9%_.-]+).json.gz", encoded_collection_filename)
    if not m:
        raise ValueError(f"Cache filename {encoded_collection_filename} could not be parsed")

    collection = urllib.parse.unquote(m.group(1))

    try:
        matching_collections =  butler.registry.queryCollections(collection)

        return len(matching_collections) > 0

    except dafButler.MissingCollectionError:
        return False


def cleanup(repo, do_delete=False):

    butler = dafButler.Butler(repo)

    encoded_repo = urllib.parse.quote_plus(repo)

    session = boto3.Session(profile_name='rubin-plot-navigator')
    s3_client = session.client('s3', endpoint_url=os.getenv("S3_ENDPOINT_URL"))

    try:
        token = None
        while True:
            response = s3_client.list_objects_v2(Bucket='rubin-plot-navigator',
                                                 Prefix=f"{encoded_repo}/collection",
                                                 ContinuationToken=token if token else "")
            for entry in response['Contents']:
                does_exist = check_existence(butler, entry['Key'])
                print(f"{entry['Key']}: {does_exist}")

                if do_delete and (not does_exist):
                    print(f"Deleting {entry['Key']}")
                    s3_client.delete_object(Bucket='rubin-plot-navigator',
                                            Key=entry['Key'])

            if not response['IsTruncated']:
                break

            token = response['NextContinuationToken']

    except botocore.exceptions.ClientError as e:
        return f"Error: {e}"

if __name__ == "__main__":
    cleanup("dp2_prep", do_delete=False)
