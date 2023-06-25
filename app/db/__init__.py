from flask import current_app, g
from pymongo import MongoClient


config = {
  'host': 'localhost',
  'port': 27017,
  'username': '',
  'password': '',
}

class Client:
  def __new__(cls, database):
    client = MongoClient(**config)
    return client[database]

def get_db():
  if 'db' not in g:
    g.db = Client(current_app.config['DATABASE'])
  return g.db