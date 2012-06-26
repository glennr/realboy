import simplejson
import urllib
import urllib2
import urlparse
import twitter
import operator
import re
import random
import twitter
from operator import itemgetter
from database import *
from igraph import *
from twitter_graph import *

twitter = twitter.Api()

class TwitterTweet():
  """TwitterTweet is a helper class for generating realistic tweets."""

  def __init__(self):
    self.stopwords = open("stopwords.txt").read().lower().split("\n")

  def tweet(self,user,tweet):
    twitter.SetCredentials(user.username, user.password)
    twitter.PostUpdate(tweet)
    twitter.ClearCredentials()

  def friend(self,user,user_to_friend):
    twitter.SetCredentials(user.username, user.password)
    try:
      twitter.CreateFriendship(user_to_friend.username, True)
    except:
      print "Friendship to %s failed. Skipping permanently." % (user_to_friend.username)
    twitter.ClearCredentials()

  def generateTweetFromUser1(self,user):
    outsiders = self.immediateOutsiders(user)
    return self.randomTweetFromCommunity(outsiders)

  def immediateOutsiders(self,user):
    """returns users who are just outside the given user's immediate connections"""
    d1_users = user.getFollowersAndFollows()
    d1_users.append(user)
    d3_users = []
    for d1_user in d1_users:
      d2_users = d1_user.getFollowersAndFollows()
      for d2_user in d2_users:
        if d2_user not in d1_users:
          d3_users.append(d2_user)
    return d3_users

  def keywordsFromCommunity(self,users_list):
    """takes a list of users and returns the keywords that community uses, in order of popularity"""
    words = {}
    for user in users_list:
      for tweet in user.tweets:
        if not re.compile('[@#]').search(tweet.text):
          for word in tweet.text.split(" "):
            word = word.lower()
            if word not in self.stopwords and not re.compile("[^a-z]").search(word):
              words[word] = words.setdefault(word,0) + 1
    words = sorted(words.items(), key=itemgetter(1))
    words.reverse()
    return [word for word,num in words]

  def randomTweetFromQuery(self,query):
    """finds a random tweet from Twitter search based on the given query"""
    tweets = [tweet for tweet in twitter.Search(query) if not re.compile('[@#]').search(tweet.text)]
    if len(tweets)>0:
      return tweets[random.randint(0,len(tweets)-1)]
    else:
      return None

  def randomTweetFromWords(self,words,wordcount=10):
    """finds a random tweet from Twitter search based on the given list of words"""
    words = words[0:wordcount]
    query_words = []
    for i in range(0,2):
      if len(words)>0:
        query_words.append(words[random.randint(0,len(words)-1)])
    query = "+".join(query_words)
    if query:
      return self.randomTweetFromQuery(query)
    else:
      return None
  
  def randomTweetFromCommunity(self,users_list):
    """Based on tweets we have in the database, get a random tweet from a list of users."""
    tweets = []
    for user in users_list:
      for tweet in user.tweets:
        if not re.compile('[@#]').search(tweet.text):
          tweets.append(tweet.text)
    if len(tweets)>0:
      return tweets[random.randint(0,len(tweets)-1)]
    return None

  def similarKeywords(self,keyword):
    """Use the tweetag API to get keywords related to a keyword."""
    url = 'http://api.tweetag.com/tagcloud/%s' % keyword
    print url
    json = twitter._FetchUrl(url)
    print json
    data = simplejson.loads(json)
    l = sorted([[str(d['name']),d['weight']] for d in data if (type(d['weight'])==int)],key=operator.itemgetter(1))
    l.reverse()
    return l

twitter_tweet = TwitterTweet()
