import os
from flask import Flask
from flask import render_template


def create_app(dev=False):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, "index.db")
    )

    # Set development enviornment
    if dev:
        app.config["FLASK_ENV"] = "development"

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except:
        pass

    from . import db
    db.init_app(app)

    # Add paths for home ("/")
    from . import home
    app.register_blueprint(home.bp)

    return app	

if __name__ == "__main__":
    app = create_app()
