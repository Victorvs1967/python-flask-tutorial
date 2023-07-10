from math import ceil
from bson import ObjectId
from flask import abort, g, request, render_template

from app.db import get_db
from app.models import Post, User


POSTS_PER_PAGE = 4
ALLOWED_EXTENTIONS = [ 'png', 'jpg', 'jpeg', 'gif', 'tif', 'tiff' ]

def get_posts(tag_name=None):

  if tag_name is None:
    db_posts = get_db().post.find({})
  else:
    db_posts = [post for post in get_db().post.find({}) if get_tags(post['_id'], tag_name)]

  posts: list(Post) = []

  for post in db_posts:
    post['_id'] = str(post.get('_id'))
    all_post_likes = post.get('likes')
    post['likes'] = len([like for like in all_post_likes if like.get('value') == 1])
    post['unlikes'] = len([like for like in all_post_likes if like.get('value') == 0])
    post['comments'] = len([post for post in post.get('comments')])
    posts.append(post)

  return posts

def get_post(id, check_author=True) -> Post:
  post: Post = get_db().post.find_one({'_id': ObjectId(id)})
  if post is None:
    abort(404, f'Post id {id} does not exist.')
  if check_author and g.user and post['author_id'] is g.user['_id']:
    abort(403)
  return post

def get_user(id) -> User:
  user: User = get_db().user.find_one({'_id': ObjectId(id)})
  if user is None:
    abort(404, f'User id {id} does not exist.')
  return user

def get_like(post, user_id):
  for like in post.get('likes'):
    if like.get('userId') == user_id:
      return like
  return None

def get_comments(post_id, comment_id=None):
  post = get_post(post_id)
  if post.get('comments'):
    if comment_id == None:
      comments = [comment for comment in post.get('comments')]
    else:
      comments = [comment for comment in post.get('comments') if comment.get('_id') == comment_id]
    for comment in comments:
      comment['username'] = get_user(comment['userId']).get('username')
  else:
    comments = []
  return comments

def get_tags(post_id, tag_name=None):
  post = get_post(post_id, check_author=False)
  if post.get('tags'):
    if tag_name is None:
      tags = [tag for tag in post.get('tags')]
    else:
      tags = [tag for tag in post.get('tags') if tag['name'] == tag_name]
  else:
    tags = []
  return tags

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

def paginate(tag_name=None, search=None):
  total_posts = len([post for post in get_posts()])
  pages = ceil(total_posts / POSTS_PER_PAGE)
  page = int(request.args.get('page', default=1))

  if page > pages:
    page = pages

  limit = POSTS_PER_PAGE
  offset = (page - 1) * POSTS_PER_PAGE

  if tag_name is None:
    if search is None:
      posts = [post for post in get_posts()][offset:page*limit]
    else:
      posts = [post for post in get_posts() if search in post['title']][offset:page*limit]
  else:
    posts = [post for post in get_posts(tag_name)][offset:page*limit]

  return render_template('index.html', posts=posts, tag_name=tag_name, pages=pages, page=page)

def allowed_file(filename):
  return '.' in filename and filename.split('.', 1)[-1].lower() in ALLOWED_EXTENTIONS