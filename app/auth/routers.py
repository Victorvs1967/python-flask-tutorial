import functools
from bson import ObjectId
from flask import flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.db import get_db
from app.models import User

from . import auth


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
    elif db.user.find_one({'username': username}) is not None:
      error =  f'User {username} already exist...'

    if error is None:
      user = User(username, password, email)
      db.user.insert_one(user.__dict__)
      return redirect(url_for('auth.login'))

    flash(error)

  return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    error = None
    user = get_db().user.find_one({'username': username})

    if user is None:
      error = 'Incorrect username.'
    elif not check_password_hash(user.get('password'), password):
      error = 'Incorrect password.'

    if error is None:
      session.clear()
      session['user_id'] = str(user.get('_id'))

      return redirect(url_for('blog.index'))

    flash(error)

  return render_template('login.html')

@auth.before_app_request
def load_logged_in_user():
  user_id = session.get('user_id')
  if user_id is None or ObjectId(user_id) is None:
    g.user = None
  else:
    g.user = get_db().user.find_one({ '_id': ObjectId(user_id) })

@auth.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('blog.index'))

def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      return redirect(url_for('auth.login'))
    return view(**kwargs)

  return wrapped_view