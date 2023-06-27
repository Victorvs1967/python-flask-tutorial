import functools
from bson import ObjectId
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.db import get_db
from app.models import User


auth = Blueprint('auth', __name__, static_folder='static', template_folder='templates', url_prefix='/auth')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    db = get_db()
    error = None

    if not username:
      error = 'Username is required.'
    elif not password:
      error = 'Password is required.'
    elif not email:
      error = 'Email is required.'

    if error is None:
      user = User(username, password, email)
      if not db.user.find_one({'username': username}):
        db.user.insert_one(user.__dict__)
        return redirect(url_for('auth.login'))
      else:
        error =  f'User {username} already exist...'

    flash(error)

  return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    db = get_db()
    error = None

    user = db.user.find_one({'username': username})
    if user is None:
      error = 'Incorrect username.'
    elif not check_password_hash(user.get('password'), password):
      error = 'Incorrect password.'

    if error is None:
      g.user = user
      g.user['_id'] = str(g.user['_id'])

      session.clear()
      session['user_id'] = user.get('_id')
      return redirect(url_for('index'))

    flash(error)

  return render_template('login.html')

@auth.before_app_request
def load_logged_in_user():
  user_id = session.get('user_id')
  if user_id is None:
    g.user = None
  else:
    db = get_db()
    g.user = db.user.find_one({'_id': ObjectId(user_id)})

@auth.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('index'))

def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      return redirect(url_for('auth.login'))
    return view(**kwargs)

  return wrapped_view