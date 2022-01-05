
from flask import Flask

from . import logs


def create_app():
    app = Flask(__name__, instance_relative_config=True,
                root_path="/Users/ctslater/production-tools/")

    app.register_blueprint(logs.bp)

    return app

__all__  = [logs, create_app]

