import datetime
from werkzeug.security import generate_password_hash


class User:
  def __init__(self, username: str, password: str, email: str):
    self._id = None
    self.username = username
    self.password = generate_password_hash(password)
    self.email = email

class Post:
  def __init__(self, title: str, body: str, author_id: str, username: str):
    self._id = None
    self.title = title
    self.body = body
    self.author_id = author_id
    self.username = username
    self.created = datetime.datetime.now()
    self.likes = []
