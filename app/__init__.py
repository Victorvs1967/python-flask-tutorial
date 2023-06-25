import os
from flask import Flask, g, render_template

from .auth import auth
from .blog import blog


def create_app(test_config=None):
  app = Flask(__name__, instance_relative_config=True)
  app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE='blog_db',
  )

  if test_config is None:
    app.config.from_pyfile('config.py', silent=True)
  else:
    app.config.from_mapping(test_config)

  try:
    os.makedirs(app.instance_path)
  except OSError:
    pass

  app.register_blueprint(auth)
  app.register_blueprint(blog)
  app.add_url_rule('/', endpoint='index')

  return app