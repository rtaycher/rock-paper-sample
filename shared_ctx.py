import os
from pathlib import Path

import flask
from flask_sqlalchemy import SQLAlchemy

_dir = Path(__file__).resolve().parent
os.chdir(_dir)

db_path = 'rock-paper-sample.db'
app = flask.Flask('rock-paper-sample')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///' + str(db_path).replace('\\', '/')
# app.config['SQLALCHEMY_ECHO'] = True  # For debug
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
DB = SQLAlchemy(app)
