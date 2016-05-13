import networkx as nx

class connected_components:
	def __init__(self, g):
		self.g = g
	
	def get_connected_components(self):		
		clusters = []
		for components in nx.connected_components(self.g):
			clusters.append(components)
		
		return clusters
