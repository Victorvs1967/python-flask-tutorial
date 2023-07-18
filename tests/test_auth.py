import pytest
from flask import g, session

from app.db import get_db


def test_signup(client, app):
  assert client.get('/auth/signup').status_code == 200
  response = client.post('/auth/signup', data={ 'username': 'u', 'password': 'p', 'email': 'u@mail.me' })
  assert response.headers['Location'] == '/auth/login'

  with app.app_context():
    assert get_db().user.find_one({ 'username': 'u' }) is not None

@pytest.mark.parametrize(
  ('username', 'password', 'email', 'message'),
  (('', '', '', b'Username is required.'),
  ('u', '', '', b'Password is required.'),
  ('u', 'p', '', b'Email is required.'),
  ('test', 'password', 'test@mail.me', b'User test already exist...')),
)
def test_singup_validate_input(client, username, password, email, message):
  response = client.post('/auth/signup', data={'username': username, 'password': password, 'email': email})
  assert message in response.data

def test_login(client, auth):
  assert client.get('/auth/login').status_code == 200
  response = auth.login()
  assert response.headers['Location'] == '/'

  with client:
    client.get('/')
    user = get_db().user.find_one({ 'username': 'test' })
    assert session['user_id'] == str(user.get('_id'))
    assert g.user['username'] == 'test'

@pytest.mark.parametrize(
  ('username', 'password', 'message'),
  (('u', 'password', b'Incorrect username.'),
  ('test', 'p', b'Incorrect password.')),
)
def test_login_validate_input(auth, username,  password, message):
  response = auth.login(username, password)
  assert message in response.data

def test_logout(client, auth):
  auth.login()

  with client:
    auth.logout()
    assert 'user_id' not in session
