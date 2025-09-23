#include "csv.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ogdf/decomposition/DynamicPlanarSPQRTree.h>
#include <ogdf/basic/Graph.h>
#include <ogdf/basic/GraphAttributes.h>

typedef struct {
    int i, j;
    double weight;
} Edge;

// Comparison for sorting edges
int compare_edges_desc(const void *a, const void *b) {
    Edge *edgeA = (Edge *)a;
    Edge *edgeB = (Edge *)b;
    if (edgeA->weight < edgeB->weight) return 1;
    if (edgeA->weight > edgeB->weight) return -1;
    return 0;
}

// Function to check if adding an edge maintains planarity
int is_planar_with_edge(ogdf::Graph &G, ogdf::node u, ogdf::node v) {
    // Add the edge temporarily
    ogdf::edge e = G.newEdge(u, v);
    
    // Check planarity using OGDF's planarity test
    bool isPlanar = ogdf::isPlanar(G);
    
    // Remove the edge
    G.delEdge(e);
    
    return isPlanar ? 1 : 0;
}

// Main PMFG algorithm implementation
ogdf::Graph* create_pmfg(double **proximity_matrix, int n) {
    // Step 1: Create ordered list of edges (φ_pp' in descending order)
    int total_edges = (n * (n - 1)) / 2;
    Edge *edges = (Edge *)malloc(total_edges * sizeof(Edge));
    int edge_count = 0;
    
    // Extract all edges with their proximity values
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            edges[edge_count].i = i;
            edges[edge_count].j = j;
            edges[edge_count].weight = proximity_matrix[i][j];
            edge_count++;
        }
    }
    
    // Sort edges in descending order of proximity (φ_pp')
    qsort(edges, edge_count, sizeof(Edge), compare_edges_desc);
    
    // Step 2: Initialize OGDF graph and nodes
    ogdf::Graph *pmfg = new ogdf::Graph();
    ogdf::node *nodes = new ogdf::node[n];
    
    // Create nodes
    for (int i = 0; i < n; i++) {
        nodes[i] = pmfg->newNode();
    }
    
    // Step 3: Add edges maintaining planarity constraint
    int added_edges = 0;
    int max_edges = 3 * (n - 2); // Maximum edges in a planar graph
    
    printf("Starting PMFG construction with %d nodes...\n", n);
    printf("Maximum edges for planarity: %d\n", max_edges);
    
    for (int k = 0; k < edge_count && added_edges < max_edges; k++) {
        int i = edges[k].i;
        int j = edges[k].j;
        double weight = edges[k].weight;
        
        // Check if adding this edge maintains planarity
        if (is_planar_with_edge(*pmfg, nodes[i], nodes[j])) {
            // Add the edge permanently
            ogdf::edge e = pmfg->newEdge(nodes[i], nodes[j]);
            added_edges++;
            
            printf("Added edge (%d, %d) with weight %.6f [%d/%d]\n", 
                   i, j, weight, added_edges, max_edges);
        }
        
        // Progress indicator
        if (k % 100 == 0) {
            printf("Progress: %d/%d edges processed, %d added\n", 
                   k, edge_count, added_edges);
        }
    }
    
    printf("PMFG construction completed. Added %d edges.\n", added_edges);
    
    // Cleanup
    free(edges);
    delete[] nodes;
    
    return pmfg;
}

// Alternative implementation using DynamicPlanarSPQRTree for efficiency
ogdf::Graph* create_pmfg_optimized(double **proximity_matrix, int n) {
    // Create ordered edge list
    int total_edges = (n * (n - 1)) / 2;
    Edge *edges = (Edge *)malloc(total_edges * sizeof(Edge));
    int edge_count = 0;
    
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            edges[edge_count].i = i;
            edges[edge_count].j = j;
            edges[edge_count].weight = proximity_matrix[i][j];
            edge_count++;
        }
    }
    
    qsort(edges, edge_count, sizeof(Edge), compare_edges_desc);
    
    // Initialize graph and SPQR tree
    ogdf::Graph *pmfg = new ogdf::Graph();
    ogdf::node *nodes = new ogdf::node[n];
    
    for (int i = 0; i < n; i++) {
        nodes[i] = pmfg->newNode();
    }
    
    // Use DynamicPlanarSPQRTree for efficient planarity maintenance
    ogdf::DynamicPlanarSPQRTree spqr_tree(*pmfg);
    
    int added_edges = 0;
    int max_edges = 3 * (n - 2);
    
    for (int k = 0; k < edge_count && added_edges < max_edges; k++) {
        int i = edges[k].i;
        int j = edges[k].j;
        
        // Try to add edge using SPQR tree
        try {
            ogdf::edge e = spqr_tree.addEdgeFixedEmbedding(nodes[i], nodes[j]);
            if (e != nullptr) {
                added_edges++;
                printf("Added edge (%d, %d) with weight %.6f\n", 
                       i, j, edges[k].weight);
            }
        } catch (...) {
            // Edge would violate planarity, skip it
            continue;
        }
    }
    
    free(edges);
    delete[] nodes;
    
    return pmfg;
}

// Utility function to print graph statistics
void print_pmfg_stats(ogdf::Graph *G, int n) {
    int num_edges = G->numberOfEdges();
    int num_nodes = G->numberOfNodes();
    int max_planar_edges = 3 * (n - 2);
    
    printf("\n=== PMFG Statistics ===\n");
    printf("Nodes: %d\n", num_nodes);
    printf("Edges: %d\n", num_edges);
  in descending order by weight   printf("Maximum planar edges: %d\n", max_planar_edges);
    printf("Planarity utilization: %.2f%%\n", 
           (double)num_edges / max_planar_edges * 100.0);
    printf("Graph density: %.4f\n", 
           (double)num_edges / (n * (n - 1) / 2.0));
}

int main(){
    int n;
    double **proximity_matrix = read_csv_matrix("Data/prox/location_proximity_matrix.csv", &n);
    if (!proximity_matrix) {
        fprintf(stderr, "Failed to load matrix from CSV\n");
        return 1;
    }
    printf("Loaded %dx%d proximity matrix from CSV.\n", n, n);

    // Create PMFG (pick your preferred function)
    ogdf::Graph *pmfg = create_pmfg(proximity_matrix, n);
    print_pmfg_stats(pmfg, n);

    // ... cleanup ...
    delete pmfg;
    for (int i = 0; i < n; i++) free(proximity_matrix[i]);
    free(proximity_matrix);

    return 0;
}
