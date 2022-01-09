
from flask import Flask, render_template

from . import logs, errors


def create_app():
    app = Flask(__name__, instance_relative_config=True,
                root_path="/Users/ctslater/production-tools/")

    app.register_blueprint(logs.bp)
    app.register_blueprint(errors.bp)


    @app.route("/")
    def index():
        return render_template("index.html", tools=["logs", "errors"])

    return app

__all__  = [logs, errors, create_app]

