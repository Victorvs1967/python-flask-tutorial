from bson import ObjectId
from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for, flash

from app.db import get_db
from app.auth import login_required
from app.models import Comment, Like, Post


blog = Blueprint('blog', __name__, static_folder='static', template_folder='templates')

@blog.route('/')
def index():
  db = get_db()

  _posts = db.post.find({})
  posts = []

  for post in _posts:
    post['_id'] = str(post.get('_id'))
    _post_likes = post.get('likes')
    post['likes'] = len([like for like in _post_likes if like.get('value') == 1])
    post['unlikes'] = len([like for like in _post_likes if like.get('value') == 0])
    post['comments'] = len(post.get('comments'))
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

@blog.route('/<id>/show', methods=['GET', 'POST'])
def show(id):
  post = get_post(id, check_author=False)
  comments = get_comments(id)

  if request.method == 'POST':
    body = request.form['body']
    error = None

    if not body:
      error = 'No comment to send.'
    if error is not None:
      flash(error)
    else:
      comment = Comment(
        g.user['_id'],
        body
      )
      comments.append(comment.__dict__)
      get_db().post.update_one({ '_id': ObjectId(id) }, {'$set': { 'comments': comments}})

    return redirect(url_for('blog.show', id=id))

  post_likes = post['likes']
  post['likes'] = len([post for post in post_likes if 1 in post.values()])
  post['unlikes'] = len([post for post in post_likes if 0 in post.values()])

  return render_template('show.html', post=post, comments=comments)

@blog.route('/<id>/show_like', endpoint='show_like')
@blog.route('/<id>/like')
@login_required
def like(id):
  post = get_post(id, check_author=False)
  user_id = session.get('user_id')

  if len(post.get('likes')) > 0 and is_liked(post, user_id):
    flash('You already liked this post.')
  elif len(post.get('likes')) > 0 and is_unliked(post, user_id):
    post.get('likes').remove(get_like(post, user_id))
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  else:
    post.get('likes').append(Like(user_id, 1).__dict__)
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  if 'show_like' in request.endpoint:
    return redirect(url_for('blog.show', id=id))
  else:
    return redirect(url_for('index'))

@blog.route('/<id>/show_unlike', endpoint='show_unlike')
@blog.route('/<id>/unlike')
@login_required
def unlike(id):
  post = get_post(id, check_author=False)
  user_id = session.get('user_id')

  if len(post.get('likes')) > 0 and is_unliked(post, user_id):
    flash('You already unliked this post.')
  elif len(post.get('likes')) > 0 and is_liked(post, user_id):
    post.get('likes').remove(get_like(post, user_id))
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  else:
    post.get('likes').append(Like(user_id, 0).__dict__)
    get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'likes': post.get('likes')}})
  if 'show_unlike' in request.endpoint:
    return redirect(url_for('blog.show', id=id))
  else:
    return redirect(url_for('index'))

@blog.route('/<id>/comment_update', methods=['GET', 'POST'])
def comment_update(id):
  post = get_post(id, check_author=False)
  comment_id = request.args.get('comment_id')
  comments = get_comments(id)
  comment = get_comments(id, comment_id)[0]

  post_likes = post['likes']
  post['likes'] = len([post for post in post_likes if 1 in post.values()])
  post['unlikes'] = len([post for post in post_likes if 0 in post.values()])
  post['comments'] = len([comment for comment in comments])

  comments.remove(comment)


  if comment.get('userId') != g.user['_id']:
    abort(403)

  if request.method == 'GET':
    return render_template('update_comment.html', post=post, comments=comment)

  if request.method == 'POST':
    body = request.form['body']
    error = None

    if not body:
      error = 'Comment is empty, consider deleting your comment.'

    if error is not None:
      flash(error)
    else:
      db = get_db()
      comments.append(comment)
      db.post.update_one({'_id': ObjectId(id)}, {'$set': {'comments': comments}})

    print(id)

    return redirect('blog.show', id=id)


@blog.route('/<id>/comment_delete', methods=['GET'])
def comment_delete(id):
  pass

def get_post(id, check_author=True) -> Post:
  post: Post = get_db().post.find_one({'_id': ObjectId(id)})
  if post is None:
    abort(404, f'Post id {id} does not exist.')
  if check_author and post['author_id'] != g.user['_id']:
    abort(403)
  return post

def is_liked(post, user_id) -> bool:
  for like in post.get('likes'):
    if like.get('userId') == user_id and like.get('value') == 1:
      return True
  return False

def is_unliked(post, user_id) -> bool:
  for like in post.get('likes'):
    if like.get('userId') == user_id and like.get('value') == 0:
      return True
  return False

def get_like(post, user_id):
  for like in post.get('likes'):
    if like.get('userId') == user_id:
      return like
  return None

def get_comments(post_id, comment_id=None):
  post = get_db().post.find_one({'_id': ObjectId(post_id)})
  if comment_id == None:
    comments = [comment for comment in post.get('comments')]
  else:
    comments = [comment for comment in post.get('comments') if comment.get('_id') == comment_id]
  return comments