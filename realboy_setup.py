# Realboy Setup
# 12/4/2008
# Set up Realboys

from database import *
from optparse import OptionParser
from twitter_tweet import *
from tweet_finder import *

def main():
  parser = OptionParser()
  parser.add_option("-g", "--group", type="int", dest="group",
                    help="Group to set up")
  options, args = parser.parse_args()

  twitter_tweet = TwitterTweet()
  tweet_finder = TweetFinder()
  
  users = database.findUsersInGroup(options.group)

  keywords = twitter_tweet.keywordsFromCommunity(users)
  
  print "Group %s" % options.group
  print "%s total users" % len(users), "\n"
  print "Users: %s" % [str(user.username) for user in users], "\n"
  print "Keywords: %s" % [str(keyword) for keyword in keywords[:20]], "\n"

  realboys = database.findAllRealboys()
  print "Realboys: %s" % [str(realboy.username) for realboy in realboys]
  realboy_username = raw_input("Please enter a Realboy username: ")
  if realboy_username:
    realboy = database.findOrCreateRealboy(realboy_username)
    if not realboy.password:
      realboy_password = raw_input("Please enter a Realboy password: ")
      realboy.password = realboy_password
    realboy.linkToGroup(options.group)
    
if __name__ == "__main__":
  main()
