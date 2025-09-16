# Simple TMFG script - minimal version
library(NetworkToolbox)

# Read data
prox <- as.matrix(read.csv('Data/prox/location_proximity_matrix.csv', row.names = 1))

# Apply TMFG
tmfg <- TMFG(prox)

# Save result
write.csv(tmfg, "tmfg_result.csv", row.names = TRUE)

print("TMFG result saved to tmfg_result.csv")
print(paste("Nodes:", nrow(tmfg), "Edges:", sum(tmfg)/2))
