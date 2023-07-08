from bson import ObjectId
from flask import abort, g, redirect, render_template, request, session, url_for, flash

from app.db import get_db
from app.auth import login_required
from app.models import Comment, Like, Post, Tag

from .services import *
from . import blog


@blog.route('/')
def index():
  posts = get_posts()
  return render_template('index.html', posts=posts)

@blog.route('/create', methods=['GET', 'POST'])
@login_required
def create():
  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    tags = request.form['tags']
    error = None

    if not title:
      error = 'Title is required.'

    forbidden_chars = set('#[]()`?$%/\<>*')
    forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
    if any((c in forbidden_chars) for c in tags):
      error = f'This characters {forbidden_chars_nicetxt} are not allowed in tags, please remove then'

    if error is not None:
      flash(error)
    else:
      post = Post(
        title=title,
        body=body,
        author_id=g.user['_id'],
        username=g.user['username'],
        tags=[Tag(x.strip()).__dict__ for x in tags.split(',')],
      )
      get_db().post.insert_one(post.__dict__)
      return redirect(url_for('blog.index'))

  return render_template('create.html')

@blog.route('/<id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
  post = get_post(id)
  tag_list = [tag['name'] for tag in get_tags(id)]

  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    tags = request.form['tags']
    error = None

    if not title:
      error = 'Title is required.'

    forbidden_chars = set('#[]()`?$%/\<>*')
    forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
    if any((c in forbidden_chars) for c in tags):
      error = f'This characters {forbidden_chars_nicetxt} are not allowed in tags, please remove then'

    if error is not None:
      flash(error)
    else:
      tags = [Tag(x.strip()).__dict__ for x in tags.split(',')]
      get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'title': title, 'body': body, 'tags': tags}})

      return redirect(url_for('blog.index'))


  tags_string = ', '.join(tag_list)
  return render_template('update.html', post=post, tags=tags_string)

@blog.route('/<id>/delete', methods=['POST'])
@login_required
def delete(id):

  get_post(id)
  db = get_db()
  db.post.delete_one({'_id': ObjectId(id)})

  return redirect(url_for('index'))

@blog.route('/<id>/show', methods=['GET', 'POST'])
def show(id):

  post = get_post(id, False)
  comments = get_comments(id)
  tags = get_tags(id)

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
        id,
        body
      )
      comments.append(comment.__dict__)
      get_db().post.update_one({ '_id': ObjectId(id) }, {'$set': { 'comments': comments}})

    return redirect(url_for('blog.show', id=id))

  post_likes = post['likes']
  post['likes'] = len([post for post in post_likes if 1 in post.values()])
  post['unlikes'] = len([post for post in post_likes if 0 in post.values()])

  return render_template('show.html', post=post, comments=comments, tags=tags)

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
    return redirect(url_for('blog.index'))

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
    return redirect(url_for('blog.index'))

@blog.route('/<id>/comment_update', methods=['GET', 'POST'])
@login_required
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
      comment['body'] = body
      comments.append(comment)
      get_db().post.update_one({'_id': ObjectId(id)}, {'$set': {'comments': comments}})

  return redirect(url_for('blog.show', id=id))

@blog.route('/<id>/comment_delete', methods=['GET'])
@login_required
def comment_delete(id):

  post = get_post(id)
  comment_id = request.args.get('comment_id')
  comments = get_comments(id)
  comment = get_comments(id, comment_id)[0]

  comments.remove(comment)

  get_db().post.update_one({ '_id': post['_id'] }, { '$set': { 'comments': comments }})

  return redirect(url_for('blog.show', id=id))

@blog.route('/<tag_name>/show_tag', methods=['GET'])
def show_tag(tag_name):
  posts = get_posts(tag_name)
  return render_template('index.html', posts=posts)
