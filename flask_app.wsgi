#!/bin/python3
import web_app
application = web_app.create_app()

activate_this = "/var/www/flask_app/venv/bin/activate"
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

