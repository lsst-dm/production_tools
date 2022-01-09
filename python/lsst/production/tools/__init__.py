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

from flask import Flask, render_template

from . import errors, logs


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        root_path="/Users/ctslater/production-tools/",
    )

    app.register_blueprint(logs.bp)
    app.register_blueprint(errors.bp)

    @app.route("/")
    def index():
        return render_template("index.html", tools=["logs", "errors"])

    return app


__all__ = [logs, errors, create_app]
