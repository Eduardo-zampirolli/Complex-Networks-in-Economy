#include <ogdf/basic/Graph.h>
#include <ogdf/basic/GraphAttributes.h>
#include <ogdf/basic/List.h>
#include <ogdf/decomposition/DynamicPlanarSPQRTree.h>
#include <ogdf/planarity/PlanarizationLayout.h>
#include <ogdf/fileformats/GraphIO.h>
#include <vector>
#include <algorithm>
#include <map>
#include <iostream>

using namespace ogdf;

/**
 * @brief Creates a Planar Maximally Filtered Graph (PMFG) from a complete graph with weighted edges
 * 
 * @param G The output graph (will be cleared and filled with PMFG)
 * @param weights Map of edge weights (higher weight = stronger connection)
 * @param n Number of nodes
 */
void createPMFG(Graph& G, std::map<std::pair<int, int>, double>& weights, int n) {
    // Clear the graph and create n nodes
    G.clear();
    
    // Create all nodes
    Array<node> nodes(n);
    for (int i = 0; i < n; i++) {
        nodes[i] = G.newNode();
    }
    
    // Create a complete graph with weighted edges
    std::vector<std::tuple<double, int, int>> edges; // weight, u, v
    
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            double weight = weights[{i, j}];
            edges.push_back({weight, i, j});
        }
    }
    
    // Sort edges by weight in descending order (strongest connections first)
    std::sort(edges.rbegin(), edges.rend());
    
    // Kruskal-like algorithm for PMFG construction
    NodeArray<int> component(G);
    int compCount = 0;
    
    // Initialize each node as its own component
    for (node v : G.nodes) {
        component[v] = compCount++;
    }
    
    // Add edges while maintaining planarity
    for (const auto& [weight, u_idx, v_idx] : edges) {
        node u = nodes[u_idx];
        node v = nodes[v_idx];
        
        // Check if u and v are in different components
        if (component[u] != component[v]) {
            // Temporarily add the edge
            edge e = G.newEdge(u, v);
            
            // Check if the graph remains planar
            DynamicPlanarSPQRTree spqrTree(G);
            bool isPlanar = spqrTree.originalGraph().numberOfNodes() == G.numberOfNodes();
            
            if (isPlanar) {
                // Update components (union-find like operation)
                int oldComp = component[v];
                int newComp = component[u];
                
                for (node w : G.nodes) {
                    if (component[w] == oldComp) {
                        component[w] = newComp;
                    }
                }
                
                std::cout << "Added edge " << u_idx << " - " << v_idx 
                          << " with weight " << weight << std::endl;
            } else {
                // Remove the edge if it makes the graph non-planar
                G.delEdge(e);
            }
        }
        
        // Stop when we have 3n - 6 edges (maximum for planar graph)
        if (G.numberOfEdges() >= 3 * n - 6) {
            break;
        }
    }
}

/**
 * @brief Example usage: Create a PMFG from random weights
 */
Graph createPMFGExample(int n = 10) {
    Graph G;
    std::map<std::pair<int, int>, double> weights;
    
    // Generate random weights for the complete graph
    srand(time(nullptr));
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            // Random weight between 0 and 1
            double weight = static_cast<double>(rand()) / RAND_MAX;
            weights[{i, j}] = weight;
        }
    }
    
    createPMFG(G, weights, n);
    return G;
}

/**
 * @brief Visualize the PMFG using OGDF's layout algorithms
 */
void visualizePMFG(Graph& G, const std::string& filename = "pmfg.gml") {
    GraphAttributes GA(G, 
        GraphAttributes::nodeGraphics | 
        GraphAttributes::edgeGraphics |
        GraphAttributes::nodeLabel |
        GraphAttributes::edgeStyle);
    
    // Add node labels
    for (node v : G.nodes) {
        GA.label(v) = std::to_string(v->index());
    }
    
    // Use planarization layout
    PlanarizationLayout pl;
    pl.call(GA);
    
    // Write to file
    GraphIO::write(GA, filename, GraphIO::writeGML);
    std::cout << "PMFG written to " << filename << std::endl;
}

/**
 * @brief Advanced PMFG with edge weight attributes
 */
class WeightedPMFG {
private:
    Graph m_graph;
    EdgeArray<double> m_edgeWeights;
    
public:
    void create(const std::map<std::pair<int, int>, double>& weights, int n) {
        m_graph.clear();
        
        Array<node> nodes(n);
        for (int i = 0; i < n; i++) {
            nodes[i] = m_graph.newNode();
        }
        
        // Initialize edge weights array
        m_edgeWeights.init(m_graph, 0.0);
        
        std::vector<std::tuple<double, int, int>> edges;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                double weight = weights.at({i, j});
                edges.push_back({weight, i, j});
            }
        }
        
        std::sort(edges.rbegin(), edges.rend());
        
        NodeArray<int> component(m_graph);
        int compCount = 0;
        for (node v : m_graph.nodes) {
            component[v] = compCount++;
        }
        
        for (const auto& [weight, u_idx, v_idx] : edges) {
            node u = nodes[u_idx];
            node v = nodes[v_idx];
            
            if (component[u] != component[v]) {
                edge e = m_graph.newEdge(u, v);
                
                DynamicPlanarSPQRTree spqrTree(m_graph);
                bool isPlanar = spqrTree.originalGraph().numberOfNodes() == m_graph.numberOfNodes();
                
                if (isPlanar) {
                    m_edgeWeights[e] = weight;
                    
                    int oldComp = component[v];
                    int newComp = component[u];
                    for (node w : m_graph.nodes) {
                        if (component[w] == oldComp) {
                            component[w] = newComp;
                        }
                    }
                } else {
                    m_graph.delEdge(e);
                }
            }
            
            if (m_graph.numberOfEdges() >= 3 * n - 6) {
                break;
            }
        }
    }
    
    const Graph& graph() const { return m_graph; }
    const EdgeArray<double>& edgeWeights() const { return m_edgeWeights; }
    
    void printInfo() const {
        std::cout << "PMFG Graph Info:" << std::endl;
        std::cout << "  Nodes: " << m_graph.numberOfNodes() << std::endl;
        std::cout << "  Edges: " << m_graph.numberOfEdges() << std::endl;
        std::cout << "  Maximum possible edges for planar graph: " 
                  << 3 * m_graph.numberOfNodes() - 6 << std::endl;
    }
};

// Main function to test the PMFG implementation
int main() {
    std::cout << "Creating PMFG example..." << std::endl;
    
    // Method 1: Simple function approach
    Graph G = createPMFGExample(12);
    visualizePMFG(G, "simple_pmfg.gml");
    
    // Method 2: Class-based approach with weights
    WeightedPMFG pmfg;
    
    // Create example weights
    std::map<std::pair<int, int>, double> weights;
    int n = 15;
    
    srand(time(nullptr));
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            weights[{i, j}] = static_cast<double>(rand()) / RAND_MAX;
        }
    }
    
    pmfg.create(weights, n);
    pmfg.printInfo();
    
    // Visualize the weighted PMFG
    GraphAttributes GA(pmfg.graph(), 
        GraphAttributes::nodeGraphics | 
        GraphAttributes::edgeGraphics |
        GraphAttributes::nodeLabel |
        GraphAttributes::edgeLabel |
        GraphAttributes::edgeStyle);
    
    // Add node labels and edge weights as labels
    for (node v : pmfg.graph().nodes) {
        GA.label(v) = std::to_string(v->index());
    }
    
    for (edge e : pmfg.graph().edges) {
        GA.label(e) = std::to_string(pmfg.edgeWeights()[e]);
    }
    
    PlanarizationLayout pl;
    pl.call(GA);
    GraphIO::write(GA, "weighted_pmfg.gml", GraphIO::writeGML);
    
    std::cout << "PMFG creation completed successfully!" << std::endl;
    return 0;
}

