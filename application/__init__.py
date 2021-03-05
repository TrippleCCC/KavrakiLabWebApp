import os
from flask import Flask
from flask import render_template


def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'index.db')
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except:
        pass

    from . import home
    app.register_blueprint(home.bp)

    return app	
