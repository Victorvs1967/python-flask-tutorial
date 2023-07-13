import os
import markdown
from uuid import uuid4
from bson import ObjectId
from flask import abort, g, redirect, render_template, request, session, url_for, flash, current_app, send_from_directory

from app.db import get_db
from app.auth import login_required
from app.models import Comment, Like, Post, Tag

from .services import *
from . import blog


@blog.route('/')
def index():
  session['search_string'] = ''
  return paginate()

@blog.route('/create', methods=['GET', 'POST'])
@login_required
def create():

  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    tags = request.form['tags']
    filename = request.args.get('filename')
    error = None

    if not title:
      error = 'Title is required.'

    forbidden_chars = set('#[]()`?$%/\<>*')
    forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
    if any((c in forbidden_chars) for c in tags):
      error = f'This characters {forbidden_chars_nicetxt} are not allowed in tags, please remove then'

    if 'file' in request.files:
      image_file = request.files['file']
      print(f'image_file: {image_file}')
      if image_file.filename == '' and not filename:
        filename = ''
      elif allowed_file(image_file.filename):
        filename = str(f'{uuid4()}_{image_file.filename}')
        image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
      elif not filename:
        error = 'File extention not applowed.'

    if error is not None:
      flash(error)
    else:
      post = Post(
        title=title,
        body=body,
        author_id=g.user['_id'],
        username=g.user['username'],
      )
      post.tags = [Tag(x.strip()).__dict__ for x in tags.split(',')]
      post.html = markdown.markdown(body)
      post.image = filename
      get_db().post.insert_one(post.__dict__)
      return redirect(url_for('blog.index'))

  return render_template('create.html')

@blog.route('/<id>/update_image', endpoint='update_image', methods=['POST', ])
@blog.route('/<id>/delete_image', endpoint='delete_image', methods=['POST', ])
@blog.route('/update_image', endpoint='update_image', methods=['POST', ])
@blog.route('/delete_image', endpoint='delete_image', methods=['POST', ])
@blog.route('/<id>/to_markdown', endpoint='to_markdown', methods=['POST', ])
@blog.route('/<id>/to_html', endpoint='to_html', methods=['POST', ])
@blog.route('/to_markdown', endpoint='to_markdown', methods=['POST', ])
@blog.route('/to_html', endpoint='to_html', methods=['POST', ])
@login_required
def update_while_create_or_update(id=None):

  mode = request.args.get('mode')
  body = request.form['body']
  html = markdown.markdown(body)

  if 'editMode' in request.args:
    editMode = request.args.get('editMode')
  else:
    editMode = 'MD'

  if mode == 'update':
    post = get_post(id)

  if request.method == 'POST':
    tags = request.form['tags']

    tags = get_tags(id)
    error = None

    if mode == 'create':
      filename = request.args.get('filename')
    elif mode == 'update':
      filename = post['image']

    if 'delete_image' in request.endpoint:
      filename = ''

    if 'update_image' in request.endpoint:
      if 'file' in request.files:
        image_file = request.files['file']
        if image_file.filename != '':
          if allowed_file(image_file.filename):
            filename = str(f'{uuid4()}_{image_file.filename}')
            image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
          else:
            error = 'File extention not applowed.'

    if 'to_html' in request.endpoint:
      editMode = 'html'

    if 'to_markdown' in request.endpoint:
      editMode = 'MD'

    if error is not None:
      flash(error)
    else:
      if mode == 'update':
        get_db().post.update_one({ '_id': ObjectId(id) }, { '$set': { 'image': filename } })

        post = get_post(id)

    if mode == 'update':
      return render_template('update.html', post=post, tags=tags, html=html, editMode=editMode)
    if mode == 'create':
      return render_template('create.html', filename=filename, html=html, editMode=editMode)


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

    filename = ''
    if 'image' in post:
      filename = post['image']
    else:
      post['image'] = filename

    if 'file' in request.files:
      image_file = request.files['file']
      if image_file.filename == '' and filename == '':
        filename = ''
      elif allowed_file(image_file.filename):
        filename = str(f'{uuid4()}_{image_file.filename}')
        image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
      elif image_file.filename != '':
        error = 'File extention not applowed.'

    if error is not None:
      flash(error)
    else:
      tags = [Tag(x.strip()).__dict__ for x in tags.split(',')]
      html = markdown.markdown(body)

      fields = {
        'title': title,
        'body': body,
        'html': html,
        'tags': tags,
        'image': filename
      }

      get_db().post.update_one({'_id': ObjectId(id)}, {'$set': fields })

      return redirect(url_for('blog.index'))

  tags_string = ', '.join(tag_list)
  return render_template('update.html', post=post, tags=tags_string)

@blog.route('/<id>/delete', methods=['POST'])
@login_required
def delete(id):

  post = get_post(id)

  if 'image' not in post:
    post['image'] = ''

  if post['image'] != '':
    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], post['image']))

  get_db().post.delete_one({'_id': ObjectId(id)})

  return redirect(url_for('blog.index'))

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
  return paginate(tag_name=tag_name, search=None)

@blog.route('/uploaded_image/<filename>')
def uploaded_image(filename):
  return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@blog.route('/search', methods=['GET', 'POST'])
def search():
  if request.method == 'POST':
    search = request.form['searchbox']
    if search == '':
      return redirect(url_for('blog.index'))
    session['search_string'] = search
  else:
    search = session['search_string']

  return paginate(tag_name=None, search=search)
