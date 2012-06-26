from igraph import *
from database import *
from twitter_graph import *
from optparse import OptionParser

def main():
  parser = OptionParser()
  parser.add_option("-g", action="store_true", dest="graphs", 
                    help="Output graphs for communities.")
  parser.add_option("-s", action="store_true", dest="subcomms",
                    help="Do sub-communities and output graphs. This sets users 'group' column to a subcomm number.")
  parser.add_option("-m", "--max_users", type="int", default=30000,
                    help="Maximum number of users to attempt to cluster/graph.")
  parser.add_option("-c", action="store_true", dest="color_by_group",
                    help="Color users by group.")
  options, args = parser.parse_args()
  
  twit_graph = TwitterGraph()

  print "Adding users to igraph.Graph"
  users = database.findAllExploredUsers(limit=options.max_users)
  if options.color_by_group:
    [twit_graph.addUserWithGroupColor(u) for u in users]
  else:
    [twit_graph.addUser(u) for u in users]
  del users
  
  print "Adding edges to igraph.Graph"
  NUM_EDGES_PER_BATCH = 100000
  results = NUM_EDGES_PER_BATCH
  page = 0
  while results == NUM_EDGES_PER_BATCH:
    edges = database.findAllEdgesBatched(NUM_EDGES_PER_BATCH, page) # Need to paginate getting edges
    results = len(edges)
    [twit_graph.addEdge(e) for e in edges]
    print "Added %s edges" % (results)
    del edges
    page += 1
  
  print "Database objects retreived"

  # We (may) need to filter out super-users that have too many friends. 
  # They don't do us any good at finding relationships between real people. 
  # They may provide insight into topics, but I am pretty sure they screw up clustering.

  print "\n".join(["","=== Generating Graph ===",""])
  twit_graph.generateGraph()
  print "\n".join(["","=== Finding Communities ===",""])
  twit_graph.findCommunities()
  if (options.subcomms):
    twit_graph.findSubcommunities(draw=True)
  if (options.graphs):
    print "\n".join(["","=== Drawing Communities ===",""])
    twit_graph.drawCommunities("community", height=1500, width=1000)
    print "\n".join(["","=== Drawing World Graph ===",""])
    twit_graph.drawBigGraph("world", height=3000, width=2000)

if __name__ == '__main__':
  main()