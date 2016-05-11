from optparse import OptionParser
from preprocess_log import preprocess_log
from create_graph import create_graph
from maxclique_percolation import maxclique_percolation_weighted
from graph_streaming import graph_streaming

def main():
	parser = OptionParser(usage='usage: %prog [options] ')
	parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=['maxclique_percolation', 'maxclique_percolation_weighted', 'kclique_percolation',],
                      default='maxclique_percolation_weighted',
                      help='Graph clustering method to run',)
	parser.add_option("-l", "--logfile",
                      action="store", 
                      dest="logfile",
                      default="nov-30.log",
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
	
	# find weighted maximal clique percolation
	mpw = maxclique_percolation_weighted(graph, k)	
	clusters, percolation_dict = mpw.get_non_overlap()	
	graph_clusters = mpw.get_graph_cluster(percolation_dict)	
	
	# graph streaming
	stream = graph_streaming(graph_clusters, edges, clusters)
	stream.gephi_streaming()

if __name__ == '__main__':
	main()	
