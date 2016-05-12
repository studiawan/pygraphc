import networkx as nx
from itertools import combinations

class create_graph:
	def __init__(self, events_unique):
		self.events_unique = events_unique
		self.g = nx.MultiGraph()	
		self.edges_dict = {}
	
	def get_graph(self):
		return self.g
	
	def create_nodes(self):
		self.g.add_nodes_from(self.events_unique)
	
	def get_cosine_similarity(self, tfidf1, tfidf2, length1, length2):
		vector_products = 0
		for ti1 in tfidf1:
			for ti2 in tfidf2:
				if ti1[0] == ti2[0]:
					vector_products += ti1[1] * ti2[1]

		try:
			cosine_similarity = vector_products / (length1 * length2)
		except ZeroDivisionError:
			cosine_similarity = 0

		return cosine_similarity		
	
	def create_edges(self):
		edges_combinations = [eu[0] for eu in self.events_unique]
		edge_index = 0
		edges = {}
		for ec in combinations(edges_combinations, 2):			
			# get cosine similarity between two nodes
			tfidf1, tfidf2 = self.g.node[ec[0]]['tf-idf'], self.g.node[ec[1]]['tf-idf']			 
			length1, length2 = self.g.node[ec[0]]['length'], self.g.node[ec[1]]['length']
			cosine_similarity = self.get_cosine_similarity(tfidf1, tfidf2, length1, length2)			
			
			# create edge
			if cosine_similarity > 0.1:
				self.g.add_edge(ec[0], ec[1], weight=cosine_similarity)
				edges[(ec[0], ec[1])] = edge_index
				edge_index += 1
		
		self.edges_dict = edges
	
	def get_edges_dict(self):
		return self.edges_dict
		
	def do_create(self):
		self.create_nodes()
		self.create_edges()			
