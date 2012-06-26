# FriendFinder
# 11/23/2008
# FriendFinder will crawl around Twitter based on a seed user, or in a spider-daemon mode.

import twitter
import urllib2
import time
from database import *
from optparse import OptionParser

class FriendFinder(object):
  
  def __init__(self, maxfriends=500):
    self._setApi()
    self.maxfriends = maxfriends
  
  def _setApi(self):
    """Grab a login from the database to authenticate an API instance as."""
    self.login = database.findFreshestLogin()
    self.api = twitter.Api(username=self.login.username, password=self.login.password)
  
  def _getFollowersOf(self, user):
    self.api.SetCredentials(user.username, user.password)
    friends = self.api.GetFollowers()
    return friends

  def _getFriendsOf(self, username, page):
    """Use Twitter API to retreive friends, handle error conditions."""
    try:
      friends = self.api.GetFriends(username,page)
      return friends
    except urllib2.HTTPError, details:
      print details
      if "404" in str(details):
        print "User %s doesn't appear to exist anymore." % (username)
        return list() # The user is gone. Send back an empty list so we can all move on with our lives.
      else: #particularly 400 errors that indicate that the API account we're using is over quota.
        self.login.setJustExpired()
        database.flush() # commit the expiration to the db.
        self._setApi()
        print "\n".join([""," !! Login Expired, Refreshing as %s !!" % (self.login.username),""])
        return self._getFriendsOf(username, page)
    except urllib2.URLError, details: # URLError has to be second. I think HTTPError inherits from URLError, and we want to handle those differently. A URLError happens when the internet connection times out.
      print details
      time.sleep(15)
      return self._getFriendsOf(username, page)
  
  def addUserAsFriendOf(self, new_screen_name, old_user):
    new_user = database.findOrCreateByUsername(new_screen_name)
    database.findOrCreateEdge(new_user,old_user)
    print "%s is now friends with %s" % (old_user.username, new_user.username)
    return new_user

  def addFriendsOf(self, user):
    """Adds friends of a user, up to self.maxfriends, or return friends already in DB if we've explored them already."""
    db_friends = list()
    if user.exhausted_friends is not True:
      page = 1
      done_finding_friends = False
      while not done_finding_friends:
        friends = self._getFriendsOf(user.username,page)
        db_friends.extend([self.addUserAsFriendOf(f.screen_name, user) for f in friends if hasattr(f, "screen_name")])
        page += 1
        if len(friends) < 100:
          done_finding_friends = True
          user.exhausted_friends = True
        if page > ((self.maxfriends/100)- 1):
          done_finding_friends = True
        database.flush()
      
      user.explored_friends = True
      return db_friends
    else:
      user.explored_friends = True
      database.flush()
      return user.getFollowersAndFollows()

  def addFriendsOfRecursive(self, user, depth=1):
    """Friends of Friends of Friends"""
    friends = self.addFriendsOf(user)
    if depth > 1:
      [self.addFriendsOfRecursive(f, depth-1) for f in friends]


def main():
  parser = OptionParser()
  parser.add_option("-s", "--seeduser",
                    help="user to seed friend finding from.")
  parser.add_option("-d", "--depth", type="int", default=2,
                    help="depth to search for user's friends.")
  parser.add_option("-m", "--maxfriends", type="int", default=500,
                    help="maximum number of friends to find per user.")
  parser.add_option("-f", action="store_true", dest="forever", 
                    help="Spider forever. Ignores -s.")
  options, args = parser.parse_args()
  
  friender = FriendFinder(options.maxfriends)

  if options.forever:
    while True:
      user = database.findLeastConnectedUnexploredUser()
      print "\n".join([""," == adding friends of %s == " % user.username,""])
      friender.addFriendsOfRecursive(user, options.depth)
  else:
    user = database.findOrCreateByUsername(options.seeduser)
    friender.addFriendsOfRecursive(user, options.depth)


if __name__ == "__main__":
    main()
