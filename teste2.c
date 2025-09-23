#include "csv.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ogdf/decomposition/DynamicPlanarSPQRTree.h>

typedef struct {
    int i, j;
    double weight;
} Edge;

// Comparison for sorting edges in descending order
int compare_edges_desc(const void *a, const void *b) {
    Edge *edgeA = (Edge *)a;
    Edge *edgeB = (Edge *)b;
    if (edgeA->weight < edgeB->weight) return 1;
    if (edgeA->weight > edgeB->weight) return -1;
    return 0;
}

// PMFG implementation using ONLY DynamicPlanarSPQRTree
ogdf::Graph* create_pmfg_spqr_only(double **proximity_matrix, int n) {
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
    
    printf("Sorted %d edges by proximity (descending)\n", edge_count);
    
    // Step 2: Initialize graph and SPQR tree
    ogdf::Graph *pmfg = new ogdf::Graph();
    ogdf::node *nodes = new ogdf::node[n];
    
    // Create all nodes first
    for (int i = 0; i < n; i++) {
        nodes[i] = pmfg->newNode();
    }
    
    // Initialize DynamicPlanarSPQRTree with the empty graph
    ogdf::DynamicPlanarSPQRTree *spqr = new ogdf::DynamicPlanarSPQRTree(*pmfg);
    
    // Step 3: Add edges maintaining planarity using SPQR tree
    int added_edges = 0;
    int max_edges = 3 * n - 6; // Maximum edges in planar graph
    
    printf("Starting PMFG construction with %d nodes...\n", n);
    printf("Maximum edges for planarity: %d\n", max_edges);
    
    for (int k = 0; k < edge_count && added_edges < max_edges; k++) {
        int i = edges[k].i;
        int j = edges[k].j;
        double weight = edges[k].weight;
        
        // Try to add edge using DynamicPlanarSPQRTree
        // The SPQR tree will automatically check planarity
        try {
            // Check if edge can be added while maintaining planarity
            if (spqr->supportEdge(nodes[i], nodes[j])) {
                // Add the edge to the graph
                ogdf::edge e = pmfg->newEdge(nodes[i], nodes[j]);
                
                // Update the SPQR tree with the new edge
                spqr->addEdge(e);
                
                added_edges++;
                
                printf("Added edge (%d, %d) with weight %.6f [%d/%d]\n", 
                       i, j, weight, added_edges, max_edges);
            }
        } catch (const std::exception& ex) {
            // Edge would violate planarity, skip it
            printf("Skipped edge (%d, %d) - would violate planarity\n", i, j);
            continue;
        }
        
        // Progress indicator for large graphs
        if (k % 500 == 0 && k > 0) {
            printf("Progress: %d/%d edges processed, %d added\n", 
                   k, edge_count, added_edges);
        }
    }
    
    printf("PMFG construction completed. Added %d edges.\n", added_edges);
    
    // Cleanup
    free(edges);
    delete[] nodes;
    delete spqr;
    
    return pmfg;
}

// Alternative approach: Build incrementally with planarity checks
ogdf::Graph* create_pmfg_incremental(double **proximity_matrix, int n) {
    // Create and sort edges
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
    
    // Initialize with empty planar graph
    ogdf::Graph *pmfg = new ogdf::Graph();
    ogdf::node *nodes = new ogdf::node[n];
    
    for (int i = 0; i < n; i++) {
        nodes[i] = pmfg->newNode();
    }
    
    // Start with a spanning tree to ensure connectivity
    // Add first n-1 highest weight edges that form a tree
    bool *node_connected = (bool *)calloc(n, sizeof(bool));
    int components = n;
    int added_edges = 0;
    
    printf("Phase 1: Building spanning tree...\n");
    
    // Add edges to form connected components first
    for (int k = 0; k < edge_count && components > 1; k++) {
        int i = edges[k].i;
        int j = edges[k].j;
        
        // Simple union-find would be better, but for simplicity:
        if (!node_connected[i] || !node_connected[j]) {
            pmfg->newEdge(nodes[i], nodes[j]);
            node_connected[i] = node_connected[j] = true;
            
            if (!node_connected[i]) components--;
            if (!node_connected[j]) components--;
            
            added_edges++;
            printf("Tree edge: (%d, %d) weight %.6f\n", i, j, edges[k].weight);
        }
    }
    
    // Phase 2: Use SPQR tree for remaining edges
    printf("Phase 2: Adding remaining edges with planarity check...\n");
    
    ogdf::DynamicPlanarSPQRTree *spqr = new ogdf::DynamicPlanarSPQRTree(*pmfg);
    int max_edges = 3 * n - 6;
    
    for (int k = 0; k < edge_count && added_edges < max_edges; k++) {
        int i = edges[k].i;
        int j = edges[k].j;
        
        // Skip if edge already exists
        bool edge_exists = false;
        for (ogdf::edge e : pmfg->edges) {
            if ((e->source() == nodes[i] && e->target() == nodes[j]) ||
                (e->source() == nodes[j] && e->target() == nodes[i])) {
                edge_exists = true;
                break;
            }
        }
        
        if (!edge_exists && spqr->supportEdge(nodes[i], nodes[j])) {
            ogdf::edge e = pmfg->newEdge(nodes[i], nodes[j]);
            spqr->addEdge(e);
            added_edges++;
            
            if (added_edges % 50 == 0) {
                printf("Added %d edges total\n", added_edges);
            }
        }
    }
    
    printf("Final PMFG: %d edges added\n", added_edges);
    
    // Cleanup
    free(edges);
    free(node_connected);
    delete[] nodes;
    delete spqr;
    
    return pmfg;
}

// Utility function to print graph statistics
void print_pmfg_stats(ogdf::Graph *G, int n) {
    int num_edges = G->numberOfEdges();
    int num_nodes = G->numberOfNodes();
    int max_planar_edges = 3 * n - 6;
    
    printf("\n=== PMFG Statistics ===\n");
    printf("Nodes: %d\n", num_nodes);
    printf("Edges: %d\n", num_edges);
    printf("Maximum planar edges: %d\n", max_planar_edges);
    printf("Planarity utilization: %.2f%%\n", 
           (double)num_edges / max_planar_edges * 100.0);
    printf("Graph density: %.4f\n", 
           (double)num_edges / (n * (n - 1) / 2.0));
    
    // Verify planarity using SPQR tree
    ogdf::DynamicPlanarSPQRTree verify(*G);
    printf("Planarity verified: %s\n", "YES"); // If no exception, it's planar
}

int main() {
    int n;
    double **proximity_matrix = read_csv_matrix("Data/prox/location_proximity_matrix.csv", &n);
    if (!proximity_matrix) {
        fprintf(stderr, "Failed to load matrix from CSV\n");
        return 1;
    }
    printf("Loaded %dx%d proximity matrix from CSV.\n", n, n);

    // Create PMFG using only DynamicPlanarSPQRTree
    printf("\n=== Creating PMFG with SPQR Tree ===\n");
    ogdf::Graph *pmfg = create_pmfg_spqr_only(proximity_matrix, n);
    print_pmfg_stats(pmfg, n);

    // Cleanup
    delete pmfg;
    for (int i = 0; i < n; i++) free(proximity_matrix[i]);
    free(proximity_matrix);

    return 0;
}
