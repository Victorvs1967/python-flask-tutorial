from curses import flash
from bson import ObjectId
from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from app.db import get_db
from app.auth import login_required
from app.models import Post


blog = Blueprint('blog', __name__, static_folder='static', template_folder='templates')

@blog.route('/')
def index():
  db = get_db()

  posts = []
  _posts = db.post.find({})

  for post in _posts:
    post['_id'] = str(post['_id'])
    posts.append(post)

  return render_template('index.html', posts=posts)

@blog.route('/create', methods=['GET', 'POST'])
@login_required
def create():
  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    error = None

    if not title:
      error = 'Title is required.'

    if error is not None:
      flash(error)
    else:
      post = Post(
        title=title,
        body=body,
        author_id=g.user['_id'],
        username=g.user['username']
      )
      db = get_db()
      db.post.insert_one(post.__dict__)
      return redirect(url_for('index'))

  return render_template('create.html')

@blog.route('/<id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
  post = get_post(id)

  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    error = None

    if not title:
      error = 'Title is required.'

    if error is not None:
      flash(error)
    else:
      db = get_db()
      db.post.update_one({'_id': ObjectId(id)}, {'$set': {'title': title, 'body': body}})
      return redirect(url_for('index'))

  return render_template('update.html', post=post)

@blog.route('/<id>/delete', methods=['POST'])
@login_required
def delete(id):
  get_post(id)
  db = get_db()
  db.post.delete_one({'_id': ObjectId(id)})

  return redirect(url_for('index'))

def get_post(id):
  post = get_db().post.find_one({'_id': ObjectId(id)})
  if post is None:
    abort(404, f'Post id {id} does not exist.')
  if post['author_id'] != g.user['_id']:
    abort(403)
  return post