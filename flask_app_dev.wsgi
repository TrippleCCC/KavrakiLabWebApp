#!/bin/python3
import os
import web_app

os.environ["FLASK_ENV"] = "development"

application = web_app.create_app()
