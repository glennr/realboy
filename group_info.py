# GroupInfo
# 12/3/2008
# Get information about a group.

from database import *
from optparse import OptionParser
from twitter_tweet import *
from tweet_finder import *


def main():
  parser = OptionParser()
  parser.add_option("-g", "--group", type="int", default=0,
                    help="Group to get info on.")
  parser.add_option("-t", action="store_true", dest="get_tweets", 
                    help="Get tweets")
  options, args = parser.parse_args()
  
  
  users = database.findUsersInGroup(options.group)
  
  if options.get_tweets:
    tweet_finder = TweetFinder()
    for user in users:
      tweet_finder.getTweetsFrom(user)

  keywords = twitter_tweet.keywordsFromCommunity(users)
  
  print "%s total users" % len(users), "\n"
  print "Users: %s" % [user.username for user in users], "\n"
  print "Keywords: %s" % [keyword for keyword in keywords[:20]], "\n"


if __name__ == "__main__":
  main()