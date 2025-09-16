# Install and load required packages
if (!require("NetworkToolbox")) {
    install.packages("NetworkToolbox")
    library(NetworkToolbox)
}

# Read the proximity matrix
cat("Reading proximity matrix...\n")
proximity_matrix <- read.csv('Data/prox/location_proximity_matrix.csv', row.names = 1)

# Convert to matrix format
proximity_mat <- as.matrix(proximity_matrix)

# Ensure the matrix is symmetric
proximity_mat <- (proximity_mat + t(proximity_mat)) / 2

# Fill diagonal with 1s (self-similarity)
diag(proximity_mat) <- 1

# Print matrix information
cat("Proximity matrix shape:", dim(proximity_mat), "\n")
cat("Matrix min value:", min(proximity_mat), "\n")
cat("Matrix max value:", max(proximity_mat), "\n")

# Apply TMFG
cat("Applying TMFG algorithm...\n")
tmfg_result <- TMFG(proximity_mat)

# Convert to data frame with row and column names
tmfg_df <- as.data.frame(tmfg_result)
rownames(tmfg_df) <- rownames(proximity_matrix)
colnames(tmfg_df) <- colnames(proximity_matrix)

# Save the TMFG adjacency matrix
write.csv(tmfg_df, "tmfg_adjacency_matrix.csv", row.names = TRUE)
cat("TMFG adjacency matrix saved to 'tmfg_adjacency_matrix.csv'\n")

# Create edge list from adjacency matrix
edge_list <- data.frame()
node_names <- rownames(tmfg_df)

for (i in 1:nrow(tmfg_result)) {
    for (j in (i+1):ncol(tmfg_result)) {
        if (i < j && tmfg_result[i, j] == 1) {
            edge_list <- rbind(edge_list, data.frame(
                source = node_names[i],
                target = node_names[j],
                weight = proximity_mat[i, j]
            ))
        }
    }
}

# Save edge list
write.csv(edge_list, "tmfg_edge_list.csv", row.names = FALSE)
cat("TMFG edge list saved to 'tmfg_edge_list.csv'\n")

# Print network statistics
num_nodes <- nrow(tmfg_result)
num_edges <- sum(tmfg_result) / 2  # Divide by 2 because matrix is symmetric
density <- num_edges / (num_nodes * (num_nodes - 1) / 2)

cat("\nNetwork Statistics:\n")
cat("Number of nodes:", num_nodes, "\n")
cat("Number of edges:", num_edges, "\n")
cat("Network density:", round(density, 4), "\n")

# Calculate degree for each node
degrees <- rowSums(tmfg_result)
degree_stats <- data.frame(
    node = node_names,
    degree = degrees
)

# Save degree statistics
write.csv(degree_stats, "tmfg_degree_stats.csv", row.names = FALSE)
cat("Degree statistics saved to 'tmfg_degree_stats.csv'\n")

cat("\nScript completed successfully!\n")
cat("Files created:\n")
cat("- tmfg_adjacency_matrix.csv (full adjacency matrix)\n")
cat("- tmfg_edge_list.csv (list of edges with weights)\n")
cat("- tmfg_degree_stats.csv (degree statistics for each node)\n")
