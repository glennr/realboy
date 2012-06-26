#This file is run by a daemon

from optparse import OptionParser
from twitter_tweet import *
from tweet_finder import *
from friend_finder import *
import time

class RealboyHelper(object):
  def __init__(self, realboy):
    self.realboy = realboy
    self.username = self.realboy.username
    self.password = self.realboy.password

  def getFriendBacks(self):
    friend_finder = FriendFinder()
    friends = friend_finder._getFollowersOf(self.realboy)
    friends = [friend.screen_name for friend in friends]
    realboy_friends = self.realboy.getRealboyFriends()
    realboy_friend_usernames = [realboy_friend.getUsername() for realboy_friend in realboy_friends]
    for realboy_friend in realboy_friends:
      if realboy_friend.getUsername() in friends:
        realboy_friend.setFriendedBack()
    for friend in friends:
      if friend not in realboy_friend_usernames:
        #this is someone that followed us unexpectedly
        user = database.findOrCreateByUsername(friend)
        realboyfriend = database.findOrCreateRealboyFriend(self.realboy.id, user.id)
    realboy_friends = self.realboy.getRealboyFriends()
    return realboy_friends

  def getFriends(self):
    return self.realboy.getFriends()
  
  def getUnfriendedFriends(self):
    return self.realboy.getUnfriendedFriends()
  
  def getFriendsTweets(self):
    tweet_finder = TweetFinder()
    for friend in self.getFriends():
      tweet_finder.getTweetsFrom(friend)
  
  def getTweetCount(self):
    return self.realboy.getTweetCount()
  
  def linkToGroup(self, group):
    self.realboy.linkToGroup(group)
  
  def getFriendsKeywords(self):
    twitter_tweet = TwitterTweet()
    return twitter_tweet.keywordsFromCommunity(self.getFriends())
  
  def randomTweetFromFriendsKeywords(self,wordcount=10):
    twitter_tweet = TwitterTweet()
    return twitter_tweet.randomTweetFromWords(self.getFriendsKeywords(),wordcount)
  
  def tweet(self, tweet_text, armed=False):
    twitter_tweet = TwitterTweet()
    if armed==True:
      print "Tweeting: %s" % (tweet_text)
      twitter_tweet.tweet(self.realboy, tweet_text)
      self.realboy.setJustTweeted()
  
  def friendPeople(self, new_friends, armed=False):
    twitter_tweet = TwitterTweet()
    for realboyfriend in self.getUnfriendedFriends():
      new_friends = new_friends - 1
      if new_friends>=0:
        print "Friending %s" % (realboyfriend.getUser().getUsername())
        if armed==True:
          twitter_tweet.friend(self.realboy, realboyfriend.getUser())
          realboyfriend.setFriended()
          realboyfriend.last_friended = datetime.now()
          time.sleep(15)

  def refreshGroup(self):
    self.linkToGroup(self.realboy.group)


def main():
  parser = OptionParser()
  parser.add_option("-r", "--realboy", type="string", default='',
                    help="Realboy to use")
  parser.add_option("-a", action="store_true", dest="armed",
                  help="Armed. Allowed to write to Twitter")
  parser.add_option("-x", action="store_true", dest="dont_tweet",
                  help="Disable Tweeting. Only Friend.")
  parser.add_option("-t", "--min_tweet_count", type="int", dest="min_tweet_count", default=10,
                    help="Minimum tweet count before friending")
  parser.add_option("-f", "--friends_to_friend", type="int", dest="friends_to_friend", default=5,
                    help="Friends to friend per tweet")
  options, args = parser.parse_args()
    
  # Who am I?
  realboy = database.findRealboyByUsername(options.realboy)
  if realboy:
    realboy = RealboyHelper(database.findRealboyByUsername(options.realboy))
    print "Real boy:", realboy.username, "\n"

    # Who are my friends?
    users = realboy.getFriends()
    print "Users:", [user.username for user in users], "\n"

    # What have they written?
    realboy.getFriendsTweets()

    # What do they write about?
    keywords = realboy.getFriendsKeywords()
    print "Keywords:", keywords[:10], "\n"

    # Me too!
    if options.dont_tweet != True:
      try_count = 20
      while try_count>0:
        try_count = try_count - 1
        tweet = realboy.randomTweetFromFriendsKeywords(10+20-try_count)
        if tweet:
          try_count = 0
          print "Tweet: %s (from %s)" % (tweet.text, tweet.GetUser()), "\n"
          # Tweet it!
          realboy.tweet(tweet.text, armed=options.armed)
          if options.armed:
            realboy.realboy.tweet_count = realboy.realboy.tweet_count + 1
        else:
          print "No tweets found!", "\n"
          if try_count>0:
            print "Trying again...", "\n"
      
    #friend some people!
    if realboy.getTweetCount() > options.min_tweet_count:
      print "Going to Friend People!", "\n"
      realboy.friendPeople(options.friends_to_friend, armed=options.armed)
      database.flush()

    #figure out who has friended us back -- note that these people become realboy friends.
    realboy_friends = realboy.getFriendBacks()
    for realboyfriend in realboy_friends:
      if realboyfriend.getFriended()==False and realboyfriend.getFriendedBack()==True:
        if options.armed:
          twitter_tweet = TwitterTweet()
          twitter_tweet.friend(realboy.realboy, realboyfriend.getUser())
          realboyfriend.setFriended()
          realboyfriend.last_friended = datetime.now()
    database.flush()
    print "Friend backs:", [realboy_friend.getUsername() for realboy_friend in realboy_friends if realboy_friend.getFriendedBack()], "\n"

if __name__ == "__main__":
  main()
