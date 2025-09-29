import networkx as nx
import matplotlib.pyplot as plt
G = nx.read_graphml('2023_loc_tmfg_lib.graphml')
a = G.number_of_edges()
print(a)
plt.figure(figsize=(12, 10))
nx.draw(G,node_size=20, with_labels=False, alpha=0.7)
plt.title("Network Visualization")
plt.axis('off')
plt.tight_layout()
plt.show()