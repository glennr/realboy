from sqlalchemy import *
from sqlalchemy.ext.declarative import *
from sqlalchemy.orm import *
from sqlalchemy.databases import mysql
from datetime import datetime
import logging
from operator import itemgetter
from collections import deque

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

#meta = MetaData('sqlite:///database.sqlite3')
f = open("db.txt", "r") # db.txt should contain text like "mysql://realboy@localhost/realboy?charset=utf8&use_unicode=0"
db_path = f.read()
f.close()

db = create_engine(db_path)
meta = MetaData(db)

users = Table('users', meta,
  Column("id", Integer, primary_key=True),
  Column("username", String(100), unique=True),
  Column("password", String(100)),
  Column("explored_friends", Boolean, default=False),
  Column("exhausted_friends", Boolean, default=False),
  Column("explored_tweets", Boolean, default=False),
  Column("edge_count", Integer, default=0),
  Column("group", Integer, default=-1),
  mysql_charset='utf8'
)

tweets = Table('tweets', meta,
  Column("id", Integer, primary_key=True),
  Column("user_id", Integer, ForeignKey('users.id')),
  Column("text", String(200)),
  Column("tid", Integer),
  Column("created_at_in_seconds", Integer),
  mysql_charset='utf8'
)

edges = Table('edges', meta,
  Column("user1_id", Integer, ForeignKey('users.id'), primary_key=True), #a user
  Column("user2_id", Integer, ForeignKey('users.id'), primary_key=True), #someone he follows
  Column("kind", Integer), #1 = user1 is followed by user2, 2 = user1 follows user2, 3 = both directions
  mysql_charset='utf8')

logins = Table('logins', meta,
  Column("id", Integer, primary_key=True),
  Column("username", String(100), unique=True),
  Column("password", String(100)),
  Column("last_expired", DateTime), #When did this account go over API limits last?
  mysql_charset='utf8')

realboys = Table('realboys', meta,
  Column("id", Integer, primary_key=True),
  Column("username", String(100), unique=True),
  Column("password", String(100)),
  Column("last_tweet", DateTime),
  Column("group", Integer, default=-1),
  Column("tweet_count", Integer, default=0),
  mysql_charset='utf8'
)

realboy_friends = Table('realboy_friends', meta,
  Column("realboy", Integer, ForeignKey('realboys.id'), primary_key=True), # a login ("realboy")
  Column("user", Integer, ForeignKey('users.id'), primary_key=True), # a user
  Column("friended", Boolean, default=False),
  Column("friendedback", Boolean, default=False),
  Column("last_friended", DateTime),
  mysql_charset='utf8'
)

meta.create_all()

class DBUser(object):
  def __init__(self, username, password):
      self.username = username
      self.password = password

  def setGroup(self, group):
    self.group = group

  def otherUser(self, user1, user2):
    if self.id==user1.id:
      return user2
    else:
      return user1

  def distanceFromUser(self, target, maximum_breadth = 10):
    if maximum_breadth==0:
      #Dijkstra wrote this
      source = self
      dist = {}
      previous = {}
      users = database.findAllUsers()
      for v in users:
        dist[v] = 999999
        previous[v] = 0
      dist[source] = 0
      q = users
      while len(q)>0:
        for user,d in sorted(dist.items(), key=itemgetter(1)):
          if user in q:
            u = user
            break
        q.remove(u)
        if u==target:
          return dist[target]
        for v in u.getFollowersAndFollows():
          if v in q:
            alt = dist[u] + 1
            if alt < dist[v]:
              dist[v] = alt
              previous[v] = u
      return dist[target]
    else:
      #this one is based on breadth first search, so it doesn't take forever
      visited = set()
      queue = deque([self])
      dist = {}
      parent = {}
      while queue:
        curr_node = queue.popleft()
        if curr_node==self:
          parent[curr_node] = curr_node
          dist[curr_node] = 0
        if curr_node in visited: continue
        visited.add(curr_node)
        if dist.has_key(curr_node):
          dist[curr_node] = min(dist[parent[curr_node]] + 1, dist[curr_node])
        else:
          dist[curr_node] = dist[parent[curr_node]] + 1
        if dist[curr_node]>maximum_breadth:
          return 999999
        if curr_node==target:
          return dist[curr_node]
        children = curr_node.getFollowersAndFollows()
        for child in children:
          if not parent.has_key(child): parent[child] = curr_node
        queue.extend(children)
      return 999999

  def getTweets(self):
    return self.tweets

  def findOrCreateByTid(self, tid, text, created_at_in_seconds):
    return database.findOrCreateByTid(tid,text,self,created_at_in_seconds)

  def getFollowers(self):
    edges = session.query(DBEdge).filter(or_(and_(DBEdge.user1_id==self.id, or_(DBEdge.kind==1,DBEdge.kind==3)), and_(DBEdge.user2_id==self.id, or_(DBEdge.kind==2,DBEdge.kind==3)))).all()
    return [self.otherUser(edge.user1,edge.user2) for edge in edges]

  def getEdges(self):
    return session.query(DBEdge).filter(or_(DBEdge.user1_id==self.id, DBEdge.user2_id==self.id)).all()

  def getFollowersAndFollows(self):
    edges = self.getEdges()
    return [self.otherUser(edge.user1,edge.user2) for edge in edges]  

  def getFollows(self):
    edges = session.query(DBEdge).filter(or_(and_(DBEdge.user1_id==self.id, or_(DBEdge.kind==2,DBEdge.kind==3)), and_(DBEdge.user2_id==self.id, or_(DBEdge.kind==1,DBEdge.kind==3)))).all()
    return [self.otherUser(edge.user1,edge.user2) for edge in edges]

  def getId(self):
    return self.id

  def getUsername(self):
    return self.username

  def getPassword(self):
    return self.password


class DBEdge(object):
  def __init__(self, user1, user2):
    self.user1 = user1
    self.user2 = user2

  def getUser1(self):
    return self.user1

  def getUser2(self):
    return self.user2


class DBTweet(object):
  def __init__(self, tid, text, user, created_at_in_seconds):
    self.user = user
    self.text = text
    self.tid = tid
    self.created_at_in_seconds = created_at_in_seconds

  def getCreatedAt(self):
    return self.created_at_in_seconds

  def getUser(self):
    return self.user

  def getText(self):
    return self.text

  def getTid(self):
    return self.tid


class DBLogin(object):
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.last_expired = datetime.now()
    self.last_tweet = datetime.now()

  def getUsername(self):
    return self.username

  def getPassword(self):
    return self.password

  def getLastExpired(self):
    return self.last_expired
  
  def setJustExpired(self):
    self.last_expired = datetime.now()
  
  
class DBRealboy(object):
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.last_tweet = datetime.now()

  def getUsername(self):
    return self.username

  def getPassword(self):
    return self.password

  def getLastTweet(self):
    return self.last_tweet
  
  def getTweetCount(self):
    return self.tweet_count
  
  def setJustTweeted(self):
    self.last_tweet = datetime.now()
    self.tweet_count += 1
    database.flush()
  
  def linkToGroup(self, group):
    users = database.findUsersInGroup(group)
    for user in users:
      database.findOrCreateRealboyFriend(self.id, user.id)
    database.flush()
  
  def getRealboyFriends(self):
    realboy_friends = session.query(DBRealboyFriend).filter(DBRealboyFriend.realboy==self.id).all()
    return realboy_friends

  def getFriends(self):
    realboy_friends = session.query(DBRealboyFriend).filter(DBRealboyFriend.realboy==self.id).all()
    users = [database.findByUserId(realboy_friend.user) for realboy_friend in realboy_friends]
    return users
  
  def getUnfriendedFriends(self):
    return session.query(DBRealboyFriend).filter(DBRealboyFriend.realboy==self.id).filter(DBRealboyFriend.friended==False).all()


class DBRealboyFriend(object):
  def __init__(self, realboy, user):
    self.realboy = realboy
    self.user = user
  
  def getRealboy(self):
    return database.findByRealboyID(self.realboy)
  
  def getUser(self):
    return database.findByUserId(self.user)

  def getUsername(self):
    u = database.findByUserId(self.user)
    return u.username
  
  def getFriended(self):
    return self.friended
  
  def setFriended(self):
    self.friended = True

  def getFriendedBack(self):
    return self.friendedback
  
  def setFriendedBack(self):
    self.friendedback = True

class Database():
  def findAllRealboys(self):
    return session.query(DBRealboy).all()  

  def findAllUsers(self, minimum_edges=0, maximum_edges=500):
    return session.query(DBUser).filter(DBUser.edge_count>=minimum_edges).filter(DBUser.edge_count<=maximum_edges).all()
  
  def findUsersInGroup(self, group):
    return session.query(DBUser).filter(DBUser.group==group).all()
  
  def findAllExploredUsers(self, minimum_edges=0, maximum_edges=9999999, limit=9999999999):
    return session.query(DBUser).filter(DBUser.explored_friends==True).filter(DBUser.edge_count>=minimum_edges).filter(DBUser.edge_count<=maximum_edges).limit(limit).all()
  
  def findAllEdges(self):
    return session.query(DBEdge).all()
  
  def findAllEdgesBatched(self, number, page):
    return session.query(DBEdge).limit(number).offset(number*page).all()

  def findMostConnectedUnexploredUser(self):
    return session.query(DBUser).filter(DBUser.explored_friends!=True).order_by(desc(DBUser.edge_count)).first()

  def findLeastConnectedUnexploredUser(self):
    return session.query(DBUser).filter(DBUser.explored_friends!=True).order_by(asc(DBUser.edge_count)).first()
  
  def findByUserId(self,user_id):
    q = session.query(DBUser).filter(DBUser.id==user_id)
    if q.count()==1:
      return q.one()
    return False

  def findByUsername(self,username):
    q = session.query(DBUser).filter(DBUser.username==username)
    if q.count()==1:
      return q.one()
    return False
  
  def findOrCreateLogin(self, username, password):
    login = self.findLogin(username)
    if login:
      return login
    else:
      login = DBLogin(username,password)
      session.save(login)
      return login
  
  def findLogin(self, username):
    login = session.query(DBLogin).filter(DBLogin.username==username)
    if login.count()==1:
      return login.one()
    return False
  
  def findByLoginID(self, login_id):
    login = session.query(DBLogin).filter(DBLogin.id==login_id)
    if login.count()==1:
      return login.one()
    return False

  def findFreshestLogin(self):
    login =  session.query(DBLogin).order_by(asc(DBLogin.last_expired)).first()
    return login
  
  def findByTid(self,tid):
    q = session.query(DBTweet).filter(DBTweet.tid==tid)
    if q.count()==1:
      return q.one()
    return False

  def findOrCreateByTid(self,tid,text,user,created_at_in_seconds):
    tweet = self.findByTid(tid)
    if tweet:
      return tweet
    else:
      tweet = DBTweet(tid,text,user,created_at_in_seconds)
      session.save(tweet)
      return tweet
    
  def findOrCreateByUsername(self,username,password=''):
    user = self.findByUsername(username)
    if user:
      return user
    else:
      user = DBUser(username,password)
      session.save(user)
      self.flush()
      return user
      
  def findEdge(self,user1,user2): #order doesn't matter
    if user1.id>user2.id:
      user1, user2 = user2, user1
    q = session.query(DBEdge).filter(DBEdge.user1==user1).filter(DBEdge.user2==user2)
    if q.count()>=1:
      return q.one()
    return False
    
  def findOrCreateEdge(self,user1,user2): #user1 is followed by user2
    if user1.id>user2.id:
      user1, user2 = user2, user1
      kind = 2
    else:
      kind = 1
    edge = self.findEdge(user1,user2)
    if edge:
      if edge.kind==1 and kind==2:
        edge.kind = 3
      if edge.kind==2 and kind==1:
        edge.kind = 3
      return edge
    else:
      edge = DBEdge(user1,user2)
      edge.kind = kind
      user1.edge_count = user1.edge_count + 1
      user2.edge_count = user2.edge_count + 1
      session.save(edge) # we don't flush edges here, because it gives us a huge speedup to do a bunch at once then flush.
      return edge
  
  def findRealboyByUsername(self, username):
    q = session.query(DBRealboy).filter(DBRealboy.username==username)
    if q.count()>=1:
      return q.one()
    return False
  
  def findRealboyByGroup(self, group):
    q = session.query(DBRealboy).filter(DBRealboy.group==group)
    if q.count()>=1:
      return q.one()
    return False

  def findOrCreateRealboy(self, username, password=''):
      realboy = self.findRealboyByUsername(username)
      if realboy:
        return realboy
      else:
        realboy = DBRealboy(username,password)
        session.save(realboy)
        self.flush()
        return realboy
  
  def findRealboyFriend(self, realboy, user):
    q = session.query(DBRealboyFriend).filter(DBRealboyFriend.realboy==realboy).filter(DBRealboyFriend.user==user)
    if q.count()>=1:
      return q.one()
    return False
  
  def findOrCreateRealboyFriend(self, realboy, user):
    realboy_friend = self.findRealboyFriend(realboy, user)
    if realboy_friend:
      return realboy_friend
    else:
      realboy_friend = DBRealboyFriend(realboy,user)
      session.save(realboy_friend)
      return realboy_friend
      
  def flush(self):
    """saves everything from the current session."""
    session.flush()


mapper(DBUser, users)
mapper(DBEdge, edges, properties={
  'user1':   relation(DBUser,primaryjoin=edges.c.user1_id==users.c.id, backref='user1s'),
  'user2': relation(DBUser,primaryjoin=edges.c.user2_id==users.c.id, backref='user2s')
  }
)
mapper(DBTweet, tweets, properties={
    'user': relation(DBUser, backref='tweets')
})
mapper(DBLogin, logins)
mapper(DBRealboy, realboys)
mapper(DBRealboyFriend, realboy_friends)

session = create_session()
database = Database()
