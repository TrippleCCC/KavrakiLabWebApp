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

    @app.route('/')
    def hello():
        return render_template('base.html')
    
    return app	
