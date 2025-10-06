#include <ogdf/basic/Graph.h>
#include <ogdf/planarity/BoyerMyrvold.h>
#include <ogdf/decomposition/DynamicPlanarSPQRTree.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <sstream>
#include <queue>

using namespace ogdf;
using namespace std;

struct Edge {
    int source, dest;
    double weight;
    bool operator<(const Edge& other) const { return weight < other.weight; }
};

int main() {
    cout << "Loading proximity matrix..." << endl;
    
    // Load matrix
    ifstream file("Data/location_proximity_matrix.csv");
    string line;
    vector<string> nodeNames;
    
    // Read header
    getline(file, line);
    stringstream ss(line);
    string cell;
    getline(ss, cell, ',');
    while (getline(ss, cell, ',')) {
        nodeNames.push_back(cell);
    }
    
    int n = nodeNames.size();
    cout << "Found " << n << " nodes" << endl;
    
    // Use priority queue to keep only top edges (memory efficient)
    int maxEdges = 3 * (n - 2);
    int bufferSize = min(maxEdges * 10, 100000); // Keep 10x target or 100k max
    priority_queue<Edge> topEdges; // Min-heap to keep strongest edges
    
    // Read matrix and filter edges on-the-fly
    int row = 0;
    while (getline(file, line) && row < n) {
        stringstream ss(line);
        getline(ss, cell, ','); // skip row name
        
        int col = 0;
        while (getline(ss, cell, ',') && col < n) {
            if (col > row) { // Only upper triangle
                try {
                    double weight = stod(cell);
                    if (!isnan(weight) && isfinite(weight)) {
                        Edge edge = {row, col, weight};
                        
                        if ((int)topEdges.size() < bufferSize) {
                            topEdges.push(edge);
                        } else if (weight > topEdges.top().weight) {
                            topEdges.pop();
                            topEdges.push(edge);
                        }
                    }
                } catch (...) {
                    // Skip invalid values
                }
            }
            col++;
        }
        row++;
        
        if (row % 1000 == 0) {
            cout << "Processed " << row << " rows" << endl;
        }
    }
    file.close();
    
    // Convert priority queue to vector and sort (strongest first)
    vector<Edge> edges;
    while (!topEdges.empty()) {
        edges.push_back(topEdges.top());
        topEdges.pop();
    }
    reverse(edges.begin(), edges.end()); // Strongest first
    
    cout << "Using top " << edges.size() << " edges for PMFG construction" << endl;
    //TODO...
    // Initialize graph
    Graph graph;
    vector<node> nodes(n);
    for (int i = 0; i < n; i++) {
        nodes[i] = graph.newNode();
    }
    //create a loop to add the 5 strongest edges on the graph
    for (int i = 0; i < 5 && i < edges.size(); i++) {
        const Edge& e = edges[i];
        graph.newEdge(nodes[e.source], nodes[e.dest]);
    }
    DynamicPlanarSPQRTree spqrTree(graph);
    

    // First, create a spanning tree to ensure the graph is connected and planar
    // Start with the strongest edges that form a tree
    UnionFind uf(n);
    int edgesAdded = 0;

    // Add edges that maintain connectivity without breaking planarity
    for (int i = 0; i < edges.size() && edgesAdded < n-1; i++) {
        const Edge& e = edges[i];
        if (uf.find(e.source) != uf.find(e.dest)) {
            graph.newEdge(nodes[e.source], nodes[e.dest]);
            uf.unionBlocks(e.source, e.dest);
            edgesAdded++;
        }
    }

    // NOW create the DynamicPlanarSPQRTree with the initial planar graph
    DynamicPlanarSPQRTree spqrTree(graph, false); // false = don't verify planarity

    // Continue adding the strongest edges that maintain planarity
    for (int i = 0; i < edges.size() && graph.numberOfEdges() < (3*n - 6); i++) {
        const Edge& e = edges[i];
        
        // Skip if edge already exists
        bool exists = false;
        for(edge existing : graph.edges) {
            if ((existing->source() == nodes[e.source] && existing->target() == nodes[e.dest]) ||
                (existing->source() == nodes[e.dest] && existing->target() == nodes[e.source])) {
                exists = true;
                break;
            }
        }
        if (exists) continue;
        
        // Check if we can insert this edge without losing planarity
        if (spqrTree.checkInsertion(nodes[e.source], nodes[e.dest])) {
            edge newEdge = spqrTree.insertEdge(nodes[e.source], nodes[e.dest]);
            cout << "Added edge: " << e.source << " - " << e.dest << endl;
        }
    }





    /*
    // Build PMFG using static planarity testing
    BoyerMyrvold planarityTest;
    int edgesAdded = 0;
    vector<vector<double>> filtered(n, vector<double>(n, 0.0));
    
    cout << "Building PMFG (target: " << maxEdges << " edges)..." << endl;
    
    for (size_t i = 0; i < edges.size() && edgesAdded < maxEdges; i++) {
        const Edge& e = edges[i];
        
        // Add edge temporarily
        edge graphEdge = graph.newEdge(nodes[e.source], nodes[e.dest]);
        
        // Test planarity
        if (planarityTest.isPlanar(graph)) {
            // Keep edge
            filtered[e.source][e.dest] = e.weight;
            filtered[e.dest][e.source] = e.weight;
            edgesAdded++;
        } else {
            // Remove edge
            graph.delEdge(graphEdge);
        }
        
        // Progress report
        if (i % 1000 == 0 || edgesAdded == maxEdges) {
            cout << "Progress: " << i << "/" << edges.size() 
                 << " processed, " << edgesAdded << " edges added" << endl;
        }
    }
    
    cout << "\nPMFG construction complete!" << endl;
    cout << "Final graph: " << graph.numberOfNodes() << " nodes, " 
         << graph.numberOfEdges() << " edges" << endl;
    
    // Optional: SPQR tree analysis (only if graph has enough structure)
    DynamicPlanarSPQRTree* spqrTree = nullptr;
    if (graph.numberOfEdges() >= graph.numberOfNodes() && graph.numberOfEdges() >= 3) {
        try {
            spqrTree = new DynamicPlanarSPQRTree(graph, false);
            cout << "\nSPQR Tree Analysis:" << endl;
            cout << "S-nodes: " << spqrTree->numberOfSNodes() << endl;
            cout << "P-nodes: " << spqrTree->numberOfPNodes() << endl;
            cout << "R-nodes: " << spqrTree->numberOfRNodes() << endl;
            delete spqrTree;
        } catch (...) {
            cout << "SPQR tree analysis not available for this graph structure" << endl;
        }
    } else {
        cout << "Skipping SPQR analysis (insufficient edges for biconnected components)" << endl;
    }
    
    // Output filtered matrix
    cout << "\nSaving filtered matrix..." << endl;
    ofstream out("filtered_matrix.csv");
    
    // Write header
    out << "";
    for (const auto& name : nodeNames) {
        out << "," << name;
    }
    out << "\n";
    
    // Write matrix
    for (int i = 0; i < n; i++) {
        out << nodeNames[i];
        for (int j = 0; j < n; j++) {
            out << "," << filtered[i][j];
        }
        out << "\n";
    }
    out.close();
    
    cout << "Filtered matrix saved to filtered_matrix.csv" << endl;
    cout << "PMFG complete: " << edgesAdded << "/" << maxEdges << " edges" << endl;
    */
    return 0;
}

