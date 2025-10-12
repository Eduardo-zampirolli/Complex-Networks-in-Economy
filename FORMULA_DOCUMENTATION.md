# Economic Complexity Calculation - Formula Documentation

This document explains the mathematical formulas used in the economic complexity analysis and how they are implemented in the code.

## 1. Specialization Matrix (RCA - Revealed Comparative Advantage)

### Formula
```
RCA_cp = (m_cp / Σ_p m_cp) / (Σ_c m_cp / Σ_c Σ_p m_cp)
```

This can be simplified to:
```
RCA_cp = (m_cp × X) / (X_c × X_p)
```

Where:
- `m_cp`: Raw value (workers, establishments, etc.) at location c, sector/product p
- `X = Σ_c Σ_p m_cp`: Grand total (sum of all values)
- `X_c = Σ_p m_cp`: Total for location c (row sum)
- `X_p = Σ_c m_cp`: Total for sector/product p (column sum)

### Implementation
**Files:** `UF.py`, `brutos.py`, `cbo.py`

```python
# Calculate totals
X = np.sum(m)          # Grand total
X_c = np.sum(m, axis=1, keepdims=True)  # Location totals
X_p = np.sum(m, axis=0, keepdims=True)  # Sector totals

# Calculate RCA with zero division handling
with np.errstate(divide='ignore', invalid='ignore'):
    R = (m * X) / (X_c * X_p)
    R[~np.isfinite(R)] = 0  # Replace inf/nan with 0
```

### Interpretation
- RCA > 1: Location is specialized in that sector (comparative advantage)
- RCA < 1: Location is not specialized in that sector
- RCA = 1: Location has average specialization

## 2. Binary Matrix

### Formula
```
M_cp = 1  if RCA_cp ≥ 1
       0  otherwise
```

### Implementation
**File:** `bin.py`

```python
# Create binary matrix (1 if RCA >= 1, else 0)
binary_matrix = (df >= 1.0).astype(int)
```

### Metrics from Binary Matrix
- **Diversity (k_c)**: Number of sectors in which location c is specialized
  ```python
  diversity = binary_matrix.sum(axis=1)  # Sum over columns (sectors)
  ```

- **Ubiquity (k_p)**: Number of locations specialized in sector p
  ```python
  ubiquity = binary_matrix.sum(axis=0)   # Sum over rows (locations)
  ```

## 3. M̃ Matrix (Tilde Matrix)

### Formula (Equation 3.6)
```
M̃_pp' = Σ_i (M_pi × M_p'i) / (k_p,0 × k_i,0)
```

Where:
- `M_pi`: Binary matrix element (location p, industry i)
- `k_p,0`: Diversity of location p (number of industries = Σ_i M_pi)
- `k_i,0`: Ubiquity of industry i (number of locations = Σ_p M_pi)

This can be rewritten as:
```
M̃_pp' = (1/k_p,0) × Σ_i [(M_pi × M_p'i) / k_i,0]
```

### Vectorized Implementation
**File:** `index/ice.py`

```python
# Calculate diversity and ubiquity
k_p = M_np.sum(axis=1)  # diversity: number of products per location
k_i = M_np.sum(axis=0)  # ubiquity: number of locations per product

# Avoid division by zero
k_p_safe = np.where(k_p == 0, 1, k_p)
k_i_safe = np.where(k_i == 0, 1, k_i)

# Normalize M by diversity (rows) and ubiquity (columns)
M_div_kp = M_np / k_p_safe.reshape(-1, 1)
M_div_ki = M_np / k_i_safe.reshape(1, -1)

# Calculate M̃ = (M / k_p) @ (M / k_i)^T
M_tilde = M_div_kp @ M_div_ki.T
```

### Properties
- M̃ is a square matrix (n_locations × n_locations)
- M̃ is symmetric: M̃_pp' = M̃_p'p
- M̃ is positive semi-definite

## 4. Economic Complexity Index (ICE)

### Formula
Based on Hidalgo & Hausmann (2009), using the Method of Reflections:

```
ICE = (K_2 - mean(K_2)) / std(K_2)
```

Where:
- `K_2`: Second eigenvector of M̃ (corresponding to second-largest eigenvalue)
- The first eigenvector (largest eigenvalue) has all components equal to 1
- The standardization (z-score) normalizes the index

### Implementation
**File:** `index/ice.py`

```python
# Eigendecomposition of M̃
eigenvalues, eigenvectors = np.linalg.eig(M_tilde)

# Sort by eigenvalue magnitude
sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
eigenvalues_sorted = eigenvalues[sorted_idx]
eigenvectors_sorted = eigenvectors[:, sorted_idx]

# Extract the second eigenvector (real part only)
K_2 = np.real(eigenvectors_sorted[:, 1])

# Calculate ICE (z-score normalization)
ice = (K_2 - np.mean(K_2)) / np.std(K_2)
```

### Interpretation
- Higher ICE values indicate higher economic complexity
- ICE mean = 0 (by construction)
- ICE standard deviation = 1 (by construction)
- Positive values: Above-average complexity
- Negative values: Below-average complexity

## 5. Calculation Workflow

1. **Raw Data → Specialization Matrix**
   - Input: Raw counts (workers, establishments) matrix
   - Process: Calculate RCA using the formula in section 1
   - Output: Specialization matrix (normalized values)
   - Files: `UF.py`, `brutos.py`, `cbo.py`

2. **Specialization Matrix → Binary Matrix**
   - Input: Specialization matrix (RCA values)
   - Process: Apply threshold (RCA ≥ 1)
   - Output: Binary matrix (0/1 values)
   - File: `bin.py`

3. **Binary Matrix → M̃ Matrix**
   - Input: Binary matrix
   - Process: Calculate M̃ using equation 3.6
   - Output: M̃ matrix (symmetric, positive semi-definite)
   - File: `index/ice.py`

4. **M̃ Matrix → ICE Values**
   - Input: M̃ matrix
   - Process: Eigendecomposition, extract 2nd eigenvector, normalize
   - Output: ICE values for each location
   - File: `index/ice.py`

## References

- Hidalgo, C. A., & Hausmann, R. (2009). The building blocks of economic complexity. *Proceedings of the National Academy of Sciences*, 106(26), 10570-10575.
- Mealy, P., Farmer, J. D., & Teytelboym, A. (2018). Interpreting economic complexity. *Science Advances*, 5(1), eaau1705.

## Testing

Unit tests are provided in `test_ice_calculation.py` to verify:
- M̃ matrix calculation matches the mathematical definition
- Matrix is symmetric
- Eigendecomposition works correctly
- ICE normalization is correct

Run tests with:
```bash
python3 test_ice_calculation.py
```
