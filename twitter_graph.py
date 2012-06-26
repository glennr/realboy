from igraph import *
from database import *

class TwitterGraph(object): 
  """TwitterGraph is a helper object for adding Twitter users to a igraph Graph."""
  
  list_of_colors = ["blue", "red", "green", "yellow", "mediumvioletred", "indigo", "chocolate", "cornflowerblue", "crimson", "goldenrod", "lightslategray", "mediumspringgreen", "orchid", "paleturquoise", "peachpuff", "salmon", "plum"]
  
  def __init__(self):
    self.vertex_labels = list() # a list of usernames
    self.vertex_index = dict() # a reverse index of self.vertex_labels
    self.vertex_colors = list()
    self.vertex_sizes = list()
    
    self.edges = list() # a list of tuples
    self.edge_colors = list()
    self.discarded_edges = 0 # how many edges did we discard?
    
    self.graph = None # will eventually hold igraph.Graph
    self.communities = None # will eventually hold igraph subgroups

  def addUserWithGroupColor(self, user):
    self.vertex_labels.append(user.username)
    self.vertex_sizes.append(5 + (user.edge_count)**0.5)
    self.vertex_colors.append(self.list_of_colors[user.group])
    self.vertex_index[user.id] = len(self.vertex_labels) - 1

  def addUser(self, user):
    self.vertex_labels.append(user.username)
    self.vertex_sizes.append(5 + (user.edge_count)**0.5)
    if user.exhausted_friends:
      self.vertex_colors.append("yellow")
    elif user.explored_friends:
      self.vertex_colors.append("cadetblue")
    else:
      self.vertex_colors.append("maroon")
    self.vertex_index[user.id] = len(self.vertex_labels) - 1

  def addEdge(self, edge):
    if (edge.user1_id in self.vertex_index and edge.user2_id in self.vertex_index):
      self.edges.append((self.vertex_index[edge.user1_id],
                         self.vertex_index[edge.user2_id]))
      self.edge_colors.append("darkgray")
    else:
      self.discarded_edges += 1
  
  def generateGraph(self):
    """set up and generate the igraph.Graph object for this TwitterGraph."""
    vertex_attrs = dict()
    vertex_attrs["label"] = self.vertex_labels
    vertex_attrs["color"] = self.vertex_colors
    vertex_attrs["size"] = self.vertex_sizes
    
    edge_attrs = dict()
    edge_attrs["color"] = self.edge_colors
    
    directed = False
    self.graph = Graph(edges=self.edges, directed=directed, vertex_attrs=vertex_attrs, edge_attrs=edge_attrs)
    print self.graph.summary()
    print "Edges discarded: %s" % self.discarded_edges
  
  def drawBigGraph(self, filename, height=10240, width=7680):
    self.drawGraph(filename, self.graph, height=height, width=width)
  
  def drawGraph(self, filename, graph, height=2048, width=1536):
    try:
      fig = Plot(bbox=(height,width))
      fig.add(graph, layout="kk", margin=(50,50,50,50))
      fig.save(filename+".png")
      del fig
    except MemoryError:
      print "Out of memory for community in %s.png! This graph aborted!" % (filename)
  
  def findCommunities(self):
    #self.communities = self.graph.clusters()
    self.graph.simplify()
    self.communities = self.graph.community_fastgreedy()
    print "Clustered with q of %s" % self.communities.q
    print "Clustered with modularity of %s" % self.communities.modularity
    for i in xrange(len(self.communities)):
      sg = self.graph.subgraph(self.communities[i])
      print "Community %s is %s members with %s edges" % (i, sg.vcount(), sg.ecount())
      for v in sg.vs:
        user = database.findByUsername(v["label"])
        user.setGroup(i)
      database.flush()
      del sg


  def drawCommunities(self, filename, height=2048, width=1536):
    for i in xrange(len(self.communities)):
      sg = self.graph.subgraph(self.communities[i])
      print "Drawing community %s" % (i)
      if len(sg.vs) > 500:
        height *= 4
        width *= 4
      if len(sg.vs) < 3000:
        self.drawGraph(filename+str(i), graph=sg, height=height, width=width)
      else:
        print "aww hell no. community is %s users." % len(sg.vs) 
      del sg
  
  def findSubcommunities(self, draw=False):
    for j in xrange(len(self.communities)):
      subcomms = self.graph.subgraph(self.communities[j]).community_fastgreedy()
      print "Clustered with q of %s" % subcomms.q
      print "Clustered with modularity of %s" % subcomms.modularity
      for i in xrange(len(subcomms)):
        sc = self.graph.subgraph(self.communities[j]).subgraph(subcomms[i])
        print "SubCommunity %s-%s is %s members with %s edges" % (j, i, sc.vcount(), sc.ecount())
        for v in sc.vs:
          user = database.findByUsername(v["label"])
          user.setGroup((j*1000)+i)
        database.flush()
        if draw:
          self.drawGraph("community%s-%s" % (j, i), graph=sc)
        del sc
      del subcomms