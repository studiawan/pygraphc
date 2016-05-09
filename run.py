from preprocess_log import preprocess_log
from create_graph import create_graph
from kclique_percolation_bruteforce import kclique_percolation_bruteforce
from graph_streaming import graph_streaming
from maxclique_percolation import maxclique_percolation_weighted

if __name__ == '__main__':
	logfile = '/home/hudan/Git/secrepo-auth-log/nov-30.log'
	k = 3
	threshold = 0.00001
	
	# preprocess log file
	p = preprocess_log(logfile)	
	p.do_preprocess()
	events_unique = p.get_eventsunique()
	
	# create graph
	g = create_graph(events_unique)
	g.do_create()
	graph = g.get_graph()		
	edges = g.get_edges_dict()

	# find k-clique percolation		
	# cp = kclique_percolation_bruteforce(graph, k, threshold)
	# clusters = cp.get_kclique_percolation()	
	mcp = maxclique_percolation_weighted(graph, k)	
	clusters, percolation_dict = mcp.get_non_overlap()	
	graph_clusters = mcp.get_graph_cluster(percolation_dict)	
	
	# graph streaming
	stream = graph_streaming(graph_clusters, edges, clusters)
	stream.gephi_streaming()
