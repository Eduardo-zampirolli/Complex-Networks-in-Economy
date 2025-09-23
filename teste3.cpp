#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <unordered_map>
#include <unordered_set>
#include <memory>
#include <stdexcept>
#include <chrono>
#include <iomanip>
#include <ogdf/decomposition/DynamicPlanarSPQRTree.h>
#include <ogdf/basic/Graph.h>

namespace PMFGGenerator {

// Modern C++ edge structure with better encapsulation
struct Edge {
    int source;
    int target;
    double weight;
    
    Edge(int src, int tgt, double w) : source(src), target(tgt), weight(w) {}
    
    // Comparator for sorting by weight (descending)
    bool operator<(const Edge& other) const {
        return weight > other.weight; // Descending order
    }
};

// Adjacency node structure using modern C++ containers
class AdjacencyNode {
public:
    int nodeId;
    std::vector<std::pair<int, double>> neighbors; // neighbor_id, weight
    
    AdjacencyNode(int id) : nodeId(id) {}
    
    void addNeighbor(int neighborId, double weight) {
        neighbors.emplace_back(neighborId, weight);
    }
    
    size_t getDegree() const { return neighbors.size(); }
};

// RAII-based CSV reader class
class CSVEdgeListReader {
private:
    std::string filename;
    std::vector<Edge> edges;
    int maxNodeId;
    
    // Helper function to trim whitespace
    std::string trim(const std::string& str) {
        size_t first = str.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) return "";
        size_t last = str.find_last_not_of(" \t\r\n");
        return str.substr(first, (last - first + 1));
    }
    
    // Check if line contains header keywords
    bool isHeaderLine(const std::string& line) const {
        std::string lowerLine = line;
        std::transform(lowerLine.begin(), lowerLine.end(), lowerLine.begin(), ::tolower);
        return lowerLine.find("source") != std::string::npos ||
               lowerLine.find("from") != std::string::npos ||
               lowerLine.find("node") != std::string::npos ||
               lowerLine.find("target") != std::string::npos;
    }
    
public:
    explicit CSVEdgeListReader(const std::string& file) : filename(file), maxNodeId(-1) {}
    
    // Load edges from CSV with error handling
    bool loadEdges() {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Cannot open file: " << filename << std::endl;
            return false;
        }
        
        edges.clear();
        edges.reserve(10000); // Reserve space for better performance
        
        std::string line;
        bool skipHeader = false;
        
        // Check for header
        if (std::getline(file, line)) {
            if (isHeaderLine(line)) {
                skipHeader = true;
                std::cout << "Header detected, skipping first line" << std::endl;
            } else {
                // Process this line as data
                file.seekg(0); // Reset to beginning
            }
        }
        
        // Skip header if detected
        if (skipHeader && !std::getline(file, line)) {
            std::cerr << "File appears to be empty after header" << std::endl;
            return false;
        }
        
        // Process data lines
        int lineNumber = skipHeader ? 2 : 1;
        while (std::getline(file, line)) {
            std::stringstream ss(trim(line));
            std::string token;
            std::vector<std::string> tokens;
            
            // Split by comma
            while (std::getline(ss, token, ',')) {
                tokens.push_back(trim(token));
            }
            
            if (tokens.size() >= 3) {
                try {
                    int source = std::stoi(tokens[0]);
                    int target = std::stoi(tokens[1]);
                    double weight = std::stod(tokens[2]);
                    
                    // Skip self-loops during loading
                    if (source != target) {
                        edges.emplace_back(source, target, weight);
                        maxNodeId = std::max({maxNodeId, source, target});
                    }
                } catch (const std::exception& e) {
                    std::cerr << "Warning: Invalid data at line " << lineNumber 
                              << ": " << line << std::endl;
                }
            }
            lineNumber++;
        }
        
        std::cout << "Loaded " << edges.size() << " edges with max node ID: " 
                  << maxNodeId << std::endl;
        return !edges.empty();
    }
    
    // Getters
    const std::vector<Edge>& getEdges() const { return edges; }
    int getNumNodes() const { return maxNodeId + 1; }
    size_t getNumEdges() const { return edges.size(); }
    
    // Sort edges by weight (descending)
    void sortEdgesByWeight() {
        std::sort(edges.begin(), edges.end());
        std::cout << "Sorted " << edges.size() << " edges by weight (descending)" << std::endl;
        
        // Print top 5 edges
        std::cout << "Top 5 edges:" << std::endl;
        for (size_t i = 0; i < std::min(size_t(5), edges.size()); ++i) {
            std::cout << "  (" << edges[i].source << ", " << edges[i].target 
                      << ") weight: " << std::fixed << std::setprecision(6) 
                      << edges[i].weight << std::endl;
        }
    }
};

// Modern C++ PMFG generator class
class PMFGGenerator {
private:
    std::unique_ptr<ogdf::Graph> graph;
    std::vector<ogdf::node> nodeMapping;
    std::unique_ptr<ogdf::DynamicPlanarSPQRTree> spqrTree;
    int numNodes;
    
    // Hash function for edge pair (for duplicate detection)
    struct EdgeHash {
        std::size_t operator()(const std::pair<int, int>& edge) const {
            return std::hash<long long>()((long long)edge.first << 32 | edge.second);
        }
    };
    
    std::unordered_set<std::pair<int, int>, EdgeHash> addedEdges;
    
    // Normalize edge pair for consistent lookup
    std::pair<int, int> normalizeEdge(int src, int tgt) const {
        return src < tgt ? std::make_pair(src, tgt) : std::make_pair(tgt, src);
    }
    
public:
    explicit PMFGGenerator(int nodes) : numNodes(nodes) {
        initializeGraph();
    }
    
    void initializeGraph() {
        graph = std::make_unique<ogdf::Graph>();
        nodeMapping.reserve(numNodes);
        
        // Create all nodes
        for (int i = 0; i < numNodes; ++i) {
            nodeMapping.push_back(graph->newNode());
        }
        
        // Initialize SPQR tree
        spqrTree = std::make_unique<ogdf::DynamicPlanarSPQRTree>(*graph);
        
        std::cout << "Initialized graph with " << numNodes << " nodes" << std::endl;
    }
    
    // Create PMFG from sorted edge list
    std::unique_ptr<ogdf::Graph> createPMFG(const std::vector<Edge>& sortedEdges) {
        const int maxEdges = 3 * numNodes - 6; // Maximum edges in planar graph
        int addedEdgeCount = 0;
        
        std::cout << "Starting PMFG construction..." << std::endl;
        std::cout << "Maximum edges for planarity: " << maxEdges << std::endl;
        
        auto startTime = std::chrono::high_resolution_clock::now();
        
        for (size_t k = 0; k < sortedEdges.size() && addedEdgeCount < maxEdges; ++k) {
            const Edge& edge = sortedEdges[k];
            
            // Validate node indices
            if (edge.source >= numNodes || edge.target >= numNodes || 
                edge.source < 0 || edge.target < 0) {
                continue;
            }
            
            // Check for duplicate edges
            auto normalizedEdge = normalizeEdge(edge.source, edge.target);
            if (addedEdges.find(normalizedEdge) != addedEdges.end()) {
                continue;
            }
            
            try {
                // Check planarity before adding edge
                if (spqrTree->supportEdge(nodeMapping[edge.source], nodeMapping[edge.target])) {
                    // Add edge to graph
                    ogdf::edge e = graph->newEdge(nodeMapping[edge.source], nodeMapping[edge.target]);
                    
                    // Update SPQR tree
                    spqrTree->addEdge(e);
                    
                    // Track added edge
                    addedEdges.insert(normalizedEdge);
                    addedEdgeCount++;
                    
                    // Progress reporting
                    if (addedEdgeCount <= 10 || addedEdgeCount % 100 == 0) {
                        std::cout << "Added edge (" << edge.source << ", " << edge.target 
                                  << ") weight " << std::fixed << std::setprecision(6) 
                                  << edge.weight << " [" << addedEdgeCount << "/" 
                                  << maxEdges << "]" << std::endl;
                    }
                }
            } catch (const std::exception& ex) {
                // Edge would violate planarity, skip it
                continue;
            }
            
            // Progress indicator
            if (k % 1000 == 0 && k > 0) {
                std::cout << "Progress: " << k << "/" << sortedEdges.size() 
                          << " edges processed, " << addedEdgeCount << " added" << std::endl;
            }
        }
        
        auto endTime = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime);
        
        std::cout << "PMFG construction completed in " << duration.count() 
                  << " ms. Added " << addedEdgeCount << " edges." << std::endl;
        
        return std::move(graph);
    }
    
    // Print statistics
    static void printPMFGStats(const ogdf::Graph& G, int totalNodes) {
        int numEdges = G.numberOfEdges();
        int numNodes = G.numberOfNodes();
        int maxPlanarEdges = 3 * totalNodes - 6;
        
        std::cout << "\n=== PMFG Statistics ===" << std::endl;
        std::cout << "Nodes: " << numNodes << std::endl;
        std::cout << "Edges: " << numEdges << std::endl;
        std::cout << "Maximum planar edges: " << maxPlanarEdges << std::endl;
        std::cout << "Planarity utilization: " << std::fixed << std::setprecision(2)
                  << (double)numEdges / maxPlanarEdges * 100.0 << "%" << std::endl;
        std::cout << "Average degree: " << std::fixed << std::setprecision(2)
                  << (double)(2 * numEdges) / numNodes << std::endl;
    }
};

// Alternative: Adjacency list reader (modernized)
class CSVAdjacencyReader {
private:
    std::string filename;
    std::vector<AdjacencyNode> adjacencyList;
    
public:
    explicit CSVAdjacencyReader(const std::string& file) : filename(file) {}
    
    bool loadAdjacencyList() {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Cannot open file: " << filename << std::endl;
            return false;
        }
        
        std::string line;
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            
            std::stringstream ss(line);
            std::string token;
            
            // Get node ID (first token)
            if (!std::getline(ss, token, ',')) continue;
            
            try {
                int nodeId = std::stoi(token);
                AdjacencyNode adjNode(nodeId);
                
                // Parse neighbors in format "neighbor:weight"
                while (std::getline(ss, token, ',')) {
                    size_t colonPos = token.find(':');
                    if (colonPos != std::string::npos) {
                        int neighborId = std::stoi(token.substr(0, colonPos));
                        double weight = std::stod(token.substr(colonPos + 1));
                        adjNode.addNeighbor(neighborId, weight);
                    }
                }
                
                adjacencyList.push_back(std::move(adjNode));
            } catch (const std::exception& e) {
                std::cerr << "Warning: Invalid adjacency data: " << line << std::endl;
            }
        }
        
        std::cout << "Loaded adjacency list with " << adjacencyList.size() << " nodes" << std::endl;
        return !adjacencyList.empty();
    }
    
    const std::vector<AdjacencyNode>& getAdjacencyList() const { return adjacencyList; }
};

} // namespace PMFGGenerator

// Main function demonstrating usage
int main() {
    try {
        using namespace PMFGGenerator;
        
        std::cout << "=== Modern C++ PMFG Generator ===" << std::endl;
        
        // Read edge list from CSV
        CSVEdgeListReader reader("Data/prox/location_proximity_matrix.csv");
        if (!reader.loadEdges()) {
            std::cerr << "Failed to load edge list from CSV" << std::endl;
            return 1;
        }
        
        // Sort edges by weight
        auto edges = reader.getEdges(); // Copy for sorting
        std::sort(edges.begin(), edges.end());
        
        std::cout << "\nSorted " << edges.size() << " edges by weight (descending)" << std::endl;
        
        // Create PMFG
        std::cout << "\n=== Creating PMFG from Edge List ===" << std::endl;
        PMFGGenerator generator(reader.getNumNodes());
        auto pmfg = generator.createPMFG(edges);
        
        // Print statistics
        PMFGGenerator::printPMFGStats(*pmfg, reader.getNumNodes());
        
        std::cout << "\nPMFG generation completed successfully!" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}

