from bson import ObjectId
from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for, flash

from app.db import get_db
from app.auth import login_required
from app.models import Post


blog = Blueprint('blog', __name__, static_folder='static', template_folder='templates')

@blog.route('/')
def index():
  db = get_db()

  _posts = db.post.find({})
  posts = []

  for post in _posts:
    post['_id'] = str(post['_id'])
    _post_likes = post['likes']
    post['likes'] = len([post for post in _post_likes if 1 in post.values()])
    post['unlikes'] = len([post for post in _post_likes if 0 in post.values()])
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

@blog.route('/<id>/show')
def show(id):
  post = get_post(id, check_author=False)
  _post_likes = post['likes']
  post['likes'] = len([post for post in _post_likes if 1 in post.values()])
  post['unlikes'] = len([post for post in _post_likes if 0 in post.values()])
  return render_template('show.html', post=post)

@blog.route('/<id>/show_like', endpoint='show_like')
@blog.route('/<id>/like')
@login_required
def like(id):

  post = get_post(id, check_author=False)
  user_id = session.get('user_id')

  if len(post.get('likes')) > 0 and get_value(user_id, post.get('likes')) is not None and get_value(user_id, post.get('likes')) != 0:
    flash('You already liked this post.')
  elif len(post.get('likes')) > 0 and get_value(user_id, post.get('likes')) is not None and get_value(user_id, post.get('likes')) == 0:
    post.get('likes').remove(get_item(user_id, post.get('likes')))
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  else:
    post.get('likes').append({user_id: 1})
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  if 'show_like' in request.endpoint:
    return redirect(url_for('blog.show', id=id))
  else:
    return redirect(url_for('index'))
  # return redirect(url_for('index'))


@blog.route('/<id>/show_unlike', endpoint='show_unlike')
@blog.route('/<id>/unlike')
@login_required
def unlike(id):
  post = get_post(id, check_author=False)
  user_id = session.get('user_id')

  if len(post.get('likes')) > 0 and get_value(user_id, post.get('likes')) is not None and get_value(user_id, post.get('likes')) == 0:
    flash('You already unliked this post.')
  elif len(post.get('likes')) > 0 and get_value(user_id, post.get('likes')) is not None and get_value(user_id, post.get('likes')) != 0:
    post.get('likes').remove(get_item(user_id, post.get('likes')))
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post['likes']}})
  else:
    post.get('likes').append({user_id: 0})
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  if 'show_unlike' in request.endpoint:
    return redirect(url_for('blog.show', id=id))
  else:
    return redirect(url_for('index'))
  # return redirect(url_for('index'))


def get_post(id, check_author=True) -> Post:
  post: Post = get_db().post.find_one({'_id': ObjectId(id)})
  if post is None:
    abort(404, f'Post id {id} does not exist.')
  if check_author and post['author_id'] != g.user['_id']:
    abort(403)
  return post

def get_value(key, arr):
  for _, item in enumerate(arr):
    if key in item:
      return item[key]
  return None

def get_item(key, arr):
  for item in arr:
    if key in item:
      return item
  return None
