import twitter
from database import *
from optparse import OptionParser
import urllib2

class TweetFinder(object):
  
  def __init__(self, re_explore=False):
    self._setApi()
    self.re_explore = re_explore
  
  def _setApi(self):
    """Grab a login from the database to authenticate an API instance as."""
    self.login = database.findFreshestLogin()
    self.api = twitter.Api(username=self.login.username, password=self.login.password)
  
  def _getUserTimeline(self, username):
    """Use Twitter API to retreive statuses, handle error conditions."""
    try:
      statuses = self.api.GetUserTimeline(username)
      return statuses
    except urllib2.HTTPError, details:
      print details
      if "404" in str(details):
        print "User %s doesn't appear to exist anymore." % (username)
        return list() # nothing happening
      if "401" in str(details):
        print "User %s seems to have private tweets." % (username)
        return list() # private tweets
      else: #particularly 400 errors that indicate that the API account we're using is over quota.
        self.login.setJustExpired()
        database.flush() # commit the expiration to the db.
        self._setApi()
        print "\n".join([""," !! Login Expired, Refreshing as %s !!" % (self.login.username),""])
        return self._getUserTimeline(username)
    except urllib2.URLError, details: # URLError has to be second. I think HTTPError inherits from URLError, and we want to handle those differently. A URLError happens when the internet connection times out.
      return self._getUserTimeline(username)
  
  def getTweetsFrom(self, user):
    """Retreive a user's tweets."""
    if (user.explored_tweets is not True) or self.re_explore==True:
      print "Getting tweets for %s" % (user.username)
      statuses = self._getUserTimeline(user.username)
      for status in statuses:
        user.findOrCreateByTid(status.id, status.text, status.created_at_in_seconds)
      user.explored_tweets = True
      database.flush()
    else:
      return user.tweets
      
  def getTweetsFromRecursive(self, user, depth=1):
    """Friends of Friends of Friends"""
    self.getTweetsFrom(user)
    if depth > 1:
      friends = user.getFollowers() + user.getFollows()
      [self.getTweetsFromRecursive(f, depth-1) for f in friends]


def main():
  parser = OptionParser()
  parser.add_option("-s", "--seeduser",
                    help="user to seed tweet finding from.")
  parser.add_option("-d", "--depth", type="int", default=2,
                    help="depth to search.")
  parser.add_option("-g", "--group", type="int", default=-1,
                    help="group to search. supercedes other options.")
  parser.add_option("-r", action="store_true", dest="re_explore", 
                    help="Force re-explore all users.")
  options, args = parser.parse_args()
  
  tweet_finder = TweetFinder(options.re_explore)

  if options.group > -1:
    users = database.findUsersInGroup(options.group)
    [tweet_finder.getTweetsFrom(user) for user in users]
  else:
    user = database.findByUsername(options.seeduser)
    tweet_finder.getTweetsFromRecursive(user, options.depth)

  
if __name__ == "__main__":
  main()
