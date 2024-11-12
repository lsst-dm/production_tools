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
import urllib.parse
from werkzeug.routing import BaseConverter

from . import tractTable, logs, bokeh, cache, images


# This works like the built-in 'path' converter, but
# allows an initial forward slash in the parameter.
class UrlConverter(BaseConverter):

    part_isolating = False
    regex = ".*?"

    def to_python(self, value):
        print(value)
        return urllib.parse.unquote(value)

    def to_url(self, value):
        return urllib.parse.quote_plus(value)

def create_app():
    app = Flask(
        "production-tools",
    )
    app.url_map.converters['url'] = UrlConverter

    app.register_blueprint(logs.bp)
    app.register_blueprint(tractTable.bp)
    app.register_blueprint(bokeh.bp)
    app.register_blueprint(cache.bp)
    app.register_blueprint(images.bp)


    @app.route("/")
    def index():
        return render_template("index.html", tools=["metrics", "logs", "bokeh"])

    return app


__all__ = [tractTable, logs, bokeh, create_app, cache, images]
