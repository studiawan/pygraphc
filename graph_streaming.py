import pygephi
import sys
from time import sleep
from random import uniform

class graph_streaming:
	def __init__(self, graph_clusters, edges, clique_percolation=None, sleep_time = 0.1):
		self.g = graph_clusters		
		self.edges = edges
		self.clique_percolation = clique_percolation
		self.sleep_time = sleep_time		
	
	def set_node_color(self):
		cluster_length = len(self.clique_percolation)
		cluster_color = [[uniform(0.0, 1.0) for _ in range(3)] for _ in range(cluster_length)]			
		return cluster_color
			
	def remove_outcluster(self, gstream, edge_dict):
		# remove edge outside cluster
		print 'Removing unncessary edges'
		for node in self.g.nodes_iter(data=True):					
			neighbors = self.g.neighbors(node[0])
			for neighbor in neighbors:
				if neighbor != 'cluster':
					if self.g[node[0]]['cluster'] != self.g[neighbor]['cluster']:						
						try:
							gstream.delete_edge(edge_dict[(node[0], neighbor)])
						except KeyError:
							gstream.delete_edge(edge_dict[(neighbor, node[0])])
	
	def change_color(self, gstream):
		# change node color based on cluster
		cluster_color = self.set_node_color()
		for index, cluster in enumerate(self.clique_percolation):			
			node_attributes = {'size':10, 'r':cluster_color[index][0], 'g':cluster_color[index][1], 'b':cluster_color[index][2]}
			for node in cluster:
				gstream.change_node(node, **node_attributes)
	
	def gephi_streaming(self):
		gstream = pygephi.GephiClient('http://localhost:8080/workspace0', autoflush=True)
		gstream.clean()		
		
		# streaming nodes				
		print 'Streaming node'		
		for node in self.g.nodes_iter(data=True):										
			print node
			node_attributes = {'size':10, 'r':0.5, 'g':0.5, 'b':0.5, 'preprocessed_event':node[1]['preprocessed_event'], 'frequency':node[1]['frequency'], 'cluster':self.g[node[0]]['cluster']}
			gstream.add_node(node[0], **node_attributes)
		
		# streaming edges
		edge_index = 0
		edge_dict = {}
		print 'Streaming edge'	
		edges_only = self.edges.keys()			
		for e in edges_only:			
			try:
				weight = self.g[e[0]][e[1]]
			except KeyError:
				weight = self.g[e[0]][e[1]]
			
			gstream.add_edge(edge_index, e[0], e[1], weight=weight[0]['weight'], directed=False)
			edge_dict[(e[0], e[1])] = edge_index
			edge_dict[(e[1], e[0])] = edge_index
			edge_index += 1		
		
		# change cluster color
		# self.change_color(gstream)				
