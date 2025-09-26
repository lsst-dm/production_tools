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


from flask import Blueprint, send_file, g
import os
import io

from lsst.daf.butler import Butler, DatasetId
from lsst.resources import ResourcePath

bp = Blueprint("images", __name__, url_prefix="/plot-navigator/images", static_folder="../../../../static")

REPO_NAMES = os.getenv("BUTLER_REPO_NAMES").split(",")

butler_map = {}

def get_butler_map(repo):

    if repo in REPO_NAMES and (repo not in butler_map.keys()):
        print("Instantiating a butler")
        butler_map[repo] = Butler(repo)

    return butler_map[repo]

@bp.route("/uuid/<url:repo>/<uuid>")
def index(repo, uuid):

    if repo not in REPO_NAMES:
        return {"error": f"Invalid repo {repo}"}, 400

    butler = get_butler_map(repo)
    dataset_ref = butler.get_dataset(DatasetId(uuid))
    resource_path = ResourcePath(butler.getURI(dataset_ref))

    if dataset_ref.datasetType.storageClass_name != "Plot":
        return {"error": "Storage class of dataset is not 'Plot'"}, 400

    image = io.BytesIO(resource_path.read())
    return send_file(image, mimetype="image/png")

