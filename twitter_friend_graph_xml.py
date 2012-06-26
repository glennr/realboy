from __future__ import with_statement # This isn't required in Python 2.6
from database import *
from optparse import OptionParser
import xml.dom.minidom

# http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        xml.dom.minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))
# replace minidom's function with ours
xml.dom.minidom.Element.writexml = fixed_writexml

def main():
  parser = OptionParser()
  parser.add_option("-m", "--max_nodes", type="int", default=100,
                    help="Maximum number of output nodes.")
  parser.add_option("-o", "--output_file", type="string", default="twitter_friend_graph.xml",
                    help="File to output results to.")
  options, args = parser.parse_args()

  doc = xml.dom.minidom.Document()
  graphml_element = doc.createElement("graphml")
  graphml_element.setAttribute("xmlns", "http://graphml.graphdrawing.org/xmlns")
  doc.appendChild(graphml_element)
  graph_element = doc.createElement("graph")
  graph_element.setAttribute("edgedefault", "undirected")
  graphml_element.appendChild(graph_element)

  key_element = doc.createElement("key")
  key_element.setAttribute("id","username")
  key_element.setAttribute("for","node")
  key_element.setAttribute("attr.name","username")
  key_element.setAttribute("attr.type","string")
  graph_element.appendChild(key_element)

  users = database.findAllExploredUsers()[:options.max_nodes]
  for user in users:
    node_element = doc.createElement("node")
    node_element.setAttribute("id", str(user.id))
    data_element = doc.createElement("data")
    data_element.setAttribute("key","username")
    text_element = doc.createTextNode(user.username)
    data_element.appendChild(text_element)
    node_element.appendChild(data_element)
    graph_element.appendChild(node_element)
  for user in users:
    for edge in user.getFollowers():
      if edge in users:
        edge_element = doc.createElement("edge")
        edge_element.setAttribute("source", str(user.id))
        edge_element.setAttribute("target", str(edge.id))
        graph_element.appendChild(edge_element)
    for edge in user.getFollows():
      if edge in users:
        edge_element = doc.createElement("edge")
        edge_element.setAttribute("source", str(edge.id))
        edge_element.setAttribute("target", str(user.id))
        graph_element.appendChild(edge_element)
  
  with open(options.output_file, "w+") as f:
    f.write(doc.toprettyxml(indent="  "))

if __name__ == '__main__':
  main()
