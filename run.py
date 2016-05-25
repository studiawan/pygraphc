from optparse import OptionParser
from preprocess_log import preprocess_log
from create_graph import create_graph
from kclique_percolation_bruteforce import kclique_percolation_bruteforce
from graph_streaming import graph_streaming

def main():
	parser = OptionParser(usage='usage: %prog [options] ')
	parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=['connected_components', 'maxclique_percolation', 'maxclique_percolation_weighted', 'kclique_percolation_bruteforce',],
                      default='kclique_percolation_bruteforce',
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
	parser.add_option("-t", "--threshold", 
					  action="store", 
					  dest="t", 
					  default=0.00001, 
					  help="Threshold of geometric mean for weighted k-clique percolation")
                      
	(options, args) = parser.parse_args()
	logfile = options.logfile
	k = options.k
	t = options.t
	
	# preprocess log file
	p = preprocess_log(logfile)	
	p.do_preprocess()
	events_unique = p.get_eventsunique()
	
	# create graph
	g = create_graph(events_unique)
	g.do_create()
	graph = g.get_graph()	
	edges = g.get_edges_dict()
	edges_weight = g.get_edges_weight()
	
	# k-clique percolation
	kcpb = kclique_percolation_bruteforce(graph, edges_weight, k, t)
	clusters = kcpb.get_kclique_percolation()	
	
	# graph streaming
	stream = graph_streaming(graph, edges, clusters)
	stream.gephi_streaming()

if __name__ == '__main__':
	main()	
