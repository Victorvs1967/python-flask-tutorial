import pytest

from app import create_app
from app.db import get_db
from app.models import User, Post


@pytest.fixture
def app():

  app = create_app({
    'TESTING': True,
    'DATABASE': 'test_db',
  })

  with app.app_context():
    # create test users and store then to test database
    users: list(User) = []
    users.append(User('test', 'password', 'test@mail.me'))
    users.append(User('other', 'password_other', 'other@mail.me'))
    [get_db().user.insert_one(user.__dict__) for user in users]

    # create test post and store it to test database
    author = get_db().user.find_one({ 'username': 'test' })
    post = Post('test title', 'body', str(author.get('_id')), 'test')
    get_db().post.insert_one(post.__dict__)

    # drop test database
    get_db().drop_collection('user')
    get_db().drop_collection('post')

  yield app


@pytest.fixture
def client(app):
  return app.test_client()

@pytest.fixture
def runner():
  return app.test_cli_runner()

class AuthActions(object):
  def __init__(self, client):
    self._client = client

  def login(self, username='test', password='password'):
    return self._client.post('/auth/login', data={ 'username': username, 'password': password })

  def logout(self):
    return self._client.get('/auth/logout')

@pytest.fixture
def auth(client):
  return AuthActions(client)