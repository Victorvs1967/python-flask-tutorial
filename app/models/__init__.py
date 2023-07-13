import datetime
from uuid import uuid1
from werkzeug.security import generate_password_hash


class User:
  def __init__(self, username: str, password: str, email: str):
    self.username = username
    self.password = generate_password_hash(password)
    self.email = email

class Post:
  def __init__(self, title: str, body: str, author_id: str, username: str):
    self.title = title
    self.body = body
    self.author_id = author_id
    self.username = username
    self.image = ''
    self.html = ''
    self.tags: list(Tag) = []
    self.likes: list(Like) = []
    self.comments: list(Comment) = []
    self.created = datetime.datetime.now()

  def addLike(self, userId):
    if len(self.likes) > 0:
      for like in self.likes:
        if like.userId == userId:
          like.value = 1
          break
    else:
      self.likes.append(Like(userId, 1))

  def addUnlike(self, userId):
    if len(self.likes) > 0:
      for like in self.likes:
        if like.userId == userId:
          like.value = 0
          break
    else:
      self.likes.append(Like(userId, 0))

class Like:
  def __init__(self, userId: str, value: 0 | 1 ):
    self.userId = userId
    self.value = value

class Comment:
  def __init__(self, userId: str, postId: str, body: str):
    self._id = str(uuid1().hex)
    self.userId = userId
    self.postId = postId
    self.body = body
    self.created = datetime.datetime.now()

class Tag:
  def __init__(self, name):
    self._id = str(uuid1().hex)
    self.name = name
