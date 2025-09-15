import pandas as pd
import numpy as np
import networkx as nx
from numba import jit, prange
import scipy.sparse as sp
from sklearn.preprocessing import StandardScaler
import gc
import psutil

@jit(nopython=True)
def fast_gain_calculation(proximity_matrix, node_to_add, triangles_array):
    """
    Numba-optimized gain calculation
    """
    gains = np.zeros(triangles_array.shape[0])
    for i in prange(triangles_array.shape[0]):
        v1, v2, v3 = triangles_array[i]
        gains[i] = (proximity_matrix[node_to_add, v1] + 
                   proximity_matrix[node_to_add, v2] + 
                   proximity_matrix[node_to_add, v3])
    return gains

class OptimizedTMFG:
    def __init__(self, chunk_size=1000, memory_limit_gb=8):
        self.chunk_size = chunk_size
        self.memory_limit_gb = memory_limit_gb
        
    def construct_tmfg_optimized(self, proximity_matrix, progress_callback=None):
        """
        Optimized TMFG construction for large matrices
        """
        # Memory optimization: convert to float32 if possible
        if proximity_matrix.dtype == np.float64:
            proximity_matrix = proximity_matrix.astype(np.float32)
            
        n = proximity_matrix.shape[0]
        print(f"Constructing TMFG for {n} nodes...")
        
        if n < 4:
            return nx.from_numpy_array(proximity_matrix)

        # Step 1: Optimized initial tetrahedron selection
        sum_proximities = self._fast_sum_proximities(proximity_matrix)
        initial_nodes = np.argpartition(sum_proximities, -4)[-4:]
        
        # Initialize graph efficiently
        G = nx.Graph()
        
        # Add initial tetrahedron edges
        for i in range(4):
            for j in range(i+1, 4):
                node_i, node_j = initial_nodes[i], initial_nodes[j]
                G.add_edge(node_i, node_j, weight=float(proximity_matrix[node_i, node_j]))
        
        # Efficient triangle tracking using sets
        triangles = set()
        for i in range(4):
            for j in range(i+1, 4):
                for k in range(j+1, 4):
                    triangle = tuple(sorted([initial_nodes[i], initial_nodes[j], initial_nodes[k]]))
                    triangles.add(triangle)
        
        remaining_nodes = [i for i in range(n) if i not in initial_nodes]
        
        # Main optimization: batch processing and early termination
        batch_size = min(self.chunk_size, len(remaining_nodes))
        
        while remaining_nodes:
            if progress_callback:
                progress = (n - len(remaining_nodes) - 4) / (n - 4)
                progress_callback(progress)
            
            # Memory management
            if self._check_memory_usage():
                gc.collect()
            
            # Process in batches for very large graphs
            batch_nodes = remaining_nodes[:batch_size]
            
            best_gain = -np.inf
            best_node = None
            best_triangle = None
            
            # Vectorized gain calculation
            triangles_array = np.array(list(triangles))
            
            for node in batch_nodes:
                gains = fast_gain_calculation(proximity_matrix, node, triangles_array)
                max_idx = np.argmax(gains)
                
                if gains[max_idx] > best_gain:
                    best_gain = gains[max_idx]
                    best_node = node
                    best_triangle = tuple(triangles_array[max_idx])
            
            # Update graph
            self._add_node_to_triangle(G, best_node, best_triangle, proximity_matrix)
            
            # Update triangles efficiently
            triangles.remove(best_triangle)
            v1, v2, v3 = best_triangle
            
            new_triangles = [
                tuple(sorted([best_node, v1, v2])),
                tuple(sorted([best_node, v1, v3])),
                tuple(sorted([best_node, v2, v3]))
            ]
            triangles.update(new_triangles)
            
            remaining_nodes.remove(best_node)
        
        return G
    
    @staticmethod
    @jit(nopython=True)
    def _fast_sum_proximities(matrix):
        """Fast proximity sum calculation"""
        return np.sum(matrix, axis=1)
    
    def _add_node_to_triangle(self, G, node, triangle, proximity_matrix):
        """Add node and edges efficiently"""
        v1, v2, v3 = triangle
        G.add_edge(node, v1, weight=float(proximity_matrix[node, v1]))
        G.add_edge(node, v2, weight=float(proximity_matrix[node, v2]))
        G.add_edge(node, v3, weight=float(proximity_matrix[node, v3]))
    
    def _check_memory_usage(self):
        """Check if memory usage is getting high"""
        memory_percent = psutil.virtual_memory().percent
        return memory_percent > (self.memory_limit_gb / 16) * 100  # Rough estimate

def load_large_csv_optimized(filepath, chunk_size=10000):
    """
    Load large CSV files efficiently
    """
    print(f"Loading large CSV file: {filepath}")
    
    # Try to load in chunks if file is very large
    file_size = os.path.getsize(filepath) / (1024**3)  # Size in GB
    print(f"File size: {file_size:.2f} GB")
    
    if file_size > 2:  # If larger than 2GB, use chunked loading
        print("Using chunked loading for large file...")
        chunks = []
        for chunk in pd.read_csv(filepath, index_col=0, chunksize=chunk_size):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=False)
    else:
        df = pd.read_csv(filepath, index_col=0)
    
    # Convert to optimal data type
    if df.dtypes.iloc[0] == 'float64':
        df = df.astype('float32')
    
    return df

def prefilter_matrix(proximity_matrix, threshold_percentile=90):
    """
    Pre-filter the matrix to keep only strongest connections
    This dramatically reduces computational complexity
    """
    print("Pre-filtering matrix to reduce size...")
    
    # Calculate threshold
    upper_triangle = np.triu(proximity_matrix.values, k=1)
    threshold = np.percentile(upper_triangle[upper_triangle != 0], threshold_percentile)
    
    # Create filtered matrix
    filtered_matrix = proximity_matrix.copy()
    filtered_matrix[filtered_matrix < threshold] = 0
    
    print(f"Reduced matrix density from {np.count_nonzero(proximity_matrix)} to {np.count_nonzero(filtered_matrix)} connections")
    
    return filtered_matrix

# Progress callback function
def progress_callback(progress):
    """Simple progress indicator"""
    print(f"\rProgress: {progress*100:.1f}%", end='', flush=True)

# Optimized usage example
if __name__ == "__main__":
    import os
    import time
    
    # Initialize optimized TMFG
    tmfg_optimizer = OptimizedTMFG(chunk_size=500, memory_limit_gb=8)
    
    start_time = time.time()
    
    # Load large CSV efficiently
    proximity_matrix = load_large_csv_optimized('Data/prox/location_proximity_matrix.csv')
    
    print(f"Matrix shape: {proximity_matrix.shape}")
    
    # Optional: Pre-filter to reduce complexity
    if proximity_matrix.shape[0] > 1000:
        proximity_matrix = prefilter_matrix(proximity_matrix, threshold_percentile=95)
    
    # Construct TMFG with optimizations
    print("Starting TMFG construction...")
    tmfg = tmfg_optimizer.construct_tmfg_optimized(
        proximity_matrix.values, 
        progress_callback=progress_callback
    )
    
    end_time = time.time()
    
    print(f"\nTMFG construction completed in {(end_time - start_time)/60:.2f} minutes")
    print(f"Graph has {tmfg.number_of_nodes()} nodes and {tmfg.number_of_edges()} edges")
    
    print("Saving graph...")
    # Save efficiently
    nx.write_graphml(tmfg, "2023_loc_tmfg.graphml")
    nx.to_pandas_edgelist(tmfg).to_csv("2023_loc_tmfg.csv", index=False)
 
    
    print("Done!")
