from bson import ObjectId
from flask import abort, g

from app.db import get_db
from app.models import Comment, Like, Post


def get_posts():

  db_posts = get_db().post.find({})
  posts = []

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
  if check_author and post['author_id'] != g.user['_id']:
    abort(403)
  return post

def get_like(post, user_id):
  for like in post.get('likes'):
    if like.get('userId') == user_id:
      return like
  return None

def get_comments(post_id, comment_id=None):
  post: Post = get_db().post.find_one({'_id': ObjectId(post_id)})

  if post.get('comments'):
    if comment_id == None:
      comments = [comment for comment in post.get('comments')]
    else:
      comments = [comment for comment in post.get('comments') if comment.get('_id') == comment_id]
    for comment in comments:
      comment['username'] = get_db().user.find_one({ '_id': ObjectId(comment['userId'])}).get('username')
  else:
    comments = []

  return comments

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
