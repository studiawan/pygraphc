from optparse import OptionParser
from preprocess_log import preprocess_log
from create_graph import create_graph
from connected_components import connected_components
from graph_streaming import graph_streaming

def main():
	parser = OptionParser(usage='usage: %prog [options] ')
	parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=['connected_components', 'maxclique_percolation', 'maxclique_percolation_weighted', 'kclique_percolation',],
                      default='connected_components',
                      help='Graph clustering method to run',)
	parser.add_option("-l", "--logfile",
                      action="store", 
                      dest="logfile",
                      default="auth.log.anon.nov.1",
                      help="Log file to analyze",)
	parser.add_option("-k", "--kpercolation",
                      action="store", 
                      dest="k",
                      default=3,
                      help="Number of k for clique percolation",)
                      
	(options, args) = parser.parse_args()
	logfile = options.logfile
	k = options.k
	
	# preprocess log file
	p = preprocess_log(logfile)	
	p.do_preprocess()
	events_unique = p.get_eventsunique()
	
	# create graph
	g = create_graph(events_unique)
	g.do_create()
	graph = g.get_graph()
	edges = g.get_edges_dict()
	
	# connected components
	cc = connected_components(graph)
	clusters = cc.get_connected_components()
	
	# graph streaming
	stream = graph_streaming(graph, edges, clusters)
	stream.gephi_streaming()

if __name__ == '__main__':
	main()	
