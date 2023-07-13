import os
from flask import Flask


def create_app(test_config=None):

  app = Flask(__name__, instance_relative_config=True)
  app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE='blog_db',
    UPLOAD_FOLDER=os.path.join(app.instance_path, 'images'),
  )

  if test_config is None:
    app.config.from_pyfile('config.py', silent=True)
  else:
    app.config.from_mapping(test_config)

  try:
    os.makedirs(os.path.join(app.instance_path, 'images'))
  except OSError:
    pass

  @app.route("/hello")
  def hello():
    return 'Hello, World!'


  from .auth import auth
  from .blog import blog

  app.register_blueprint(auth)
  app.register_blueprint(blog)
  app.add_url_rule('/', endpoint='routes.index')

  return app