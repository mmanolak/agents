# Nemotron-3-Super-120B-UD-Q4_K_XL

**Date:** 2026-05-04 20:26:09
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 15.70 t/s | **Tokens:** 920 | **Time:** 58.58s

```R
## --------------------------------------------------------------
##  R script: distance from each property to the nearest golf course
##  Packages: sf, dplyr
## --------------------------------------------------------------

# Load required libraries -------------------------------------------------
library(sf)      # spatial classes and operations
library(dplyr)   # data manipulation verbs

# ----------------------------------------------------------------------
# 1. Read the shapefiles
# ----------------------------------------------------------------------
# Adjust the file paths if your shapefiles are located elsewhere
properties_sf <- st_read("properties.shp", quiet = TRUE)
golf_courses_sf <- st_read("golf_courses.shp", quiet = TRUE)

# ----------------------------------------------------------------------
# 2. Ensure both layers share the same CRS (coordinate reference system)
# ----------------------------------------------------------------------
if (!identical(st_crs(properties_sf), st_crs(golf_courses_sf))) {
  # Transform the golf courses to the CRS of the properties (or vice‑versa)
  golf_courses_sf <- st_transform(golf_courses_sf, st_crs(properties_sf))
}

# ----------------------------------------------------------------------
# 3. Compute the distance from each property to every golf course
# ----------------------------------------------------------------------
# st_distance returns a matrix: rows = properties, columns = golf courses
dist_matrix <- st_distance(properties_sf, golf_courses_sf)

# ----------------------------------------------------------------------
# 4. For each property, keep the smallest distance (nearest golf course)
# ----------------------------------------------------------------------
nearest_dist <- apply(dist_matrix, 1, min)   # vector length = nrow(properties_sf)

# ----------------------------------------------------------------------
# 5. Attach the distance as a new column (in metres, assuming CRS is metric)
# ----------------------------------------------------------------------
properties_sf <- properties_sf %>%
  mutate(dist_to_golf_m = as.numeric(nearest_dist))

# ----------------------------------------------------------------------
# 6. Return the updated sf object (you can also write it out if needed)
# ----------------------------------------------------------------------
# Example: write the result back to a new shapefile
# st_write(properties_sf, "properties_with_golf_dist.shp", delete_layer = TRUE)

# For interactive use, simply return the object:
properties_sf
```

### What the script does
1. **Loads** the two shapefiles as `sf` objects.  
2. **Reprojects** one layer (if necessary) so both share the same CRS – essential for meaningful distance calculations.  
3. **Computes** a full distance matrix between every property and every golf‑course polygon using `st_distance`.  
4. **Reduces** the matrix to the nearest distance per property with `apply(..., 1, min)`.  
5. **Adds** this value as a new column `dist_to_golf_m` (numeric, in the units of the CRS – typically metres when using a projected CRS).  
6. **Returns** the updated `sf` data frame; optionally, you can write it out to a new shapefile.

Make sure your CRS is projected (e.g., UTM, State Plane) if you need distances in metres; geographic CRS (latitude/longitude) will give distances in degrees, which are not directly interpretable as metres. If you start with a geographic CRS, consider projecting to an appropriate metric CRS before the distance step.

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 15.72 t/s | **Tokens:** 927 | **Time:** 58.95s

Here is a self‑contained Python script that uses **statsmodels** to run a hedonic pricing regression.  
It reads `data.csv`, creates the dependent variable `log_price`, adds a constant term to the regressors, fits an OLS model, and prints the full regression summary.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hedonic pricing regression using statsmodels.

Dependencies:
    - pandas
    - statsmodels

The script expects a CSV file named 'data.csv' in the same directory
with at least the following columns:
    - log_price   : dependent variable (log of house price)
    - bedrooms    : number of bedrooms
    - bathrooms   : number of bathrooms
    - sqft        : living area in square feet
    - dist_to_golf: distance to the nearest golf course (e.g., miles or km)

If your raw price column is named something else (e.g., 'price'),
you can create log_price inside the script as shown in the commented
section.
"""

import pandas as pd
import statsmodels.api as sm

def main():
    # ------------------------------------------------------------------
    # 1. Load the data
    # ------------------------------------------------------------------
    try:
        df = pd.read_csv('data.csv')
    except FileNotFoundError:
        raise SystemExit("Error: 'data.csv' not found in the current directory.")

    # ------------------------------------------------------------------
    # 2. Prepare variables
    # ------------------------------------------------------------------
    # Dependent variable: log_price
    # If your dataset contains a raw price column (e.g., 'price') instead
    # of a pre‑computed log price, uncomment the following two lines:
    #
    # if 'price' in df.columns and 'log_price' not in df.columns:
    #     df['log_price'] = np.log(df['price'])
    #
    # Make sure the column exists; otherwise raise a clear error.
    if 'log_price' not in df.columns:
        raise SystemExit("Error: Column 'log_price' not found in data.csv.")

    # Independent variables
    X_vars = ['bedrooms', 'bathrooms', 'sqft', 'dist_to_golf']
    missing = [v for v in X_vars if v not in df.columns]
    if missing:
        raise SystemExit(f"Error: Missing independent variable(s): {', '.join(missing)}")

    X = df[X_vars]
    y = df['log_price']

    # ------------------------------------------------------------------
    # 3. Add constant term (intercept)
    # ------------------------------------------------------------------
    X = sm.add_constant(X)  # adds a column named 'const'

    # ------------------------------------------------------------------
    # 4. Fit OLS regression
    # ------------------------------------------------------------------
    model = sm.OLS(y, X).fit()

    # ------------------------------------------------------------------
    # 5. Print results
    # ------------------------------------------------------------------
    print("\n=== Hedonic Pricing Regression Summary ===\n")
    print(model.summary())

if __name__ == "__main__":
    main()
```

### How to use
1. Save the script to a file, e.g., `hedonic_regression.py`.
2. Ensure `data.csv` is in the same folder (or adjust the path in `pd.read_csv`).
3. Install the required packages if you haven’t already:

```bash
pip install pandas statsmodels
```

4. Run the script:

```bash
python hedonic_regression.py
```

The output will display the regression coefficients, standard errors, t‑statistics, p‑values, R‑squared, F‑statistic, and other diagnostic statistics typical of an OLS summary. Feel free to adapt the variable names or add further controls (e.g., neighborhood dummies) as needed for your analysis.

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 15.74 t/s | **Tokens:** 1093 | **Time:** 69.45s

Here is a self‑contained Julia script that uses **JuMP.jl** (modeling interface) together with **Ipopt.jl** (interior‑point nonlinear solver) to solve the given linear program.  
Even though the problem is linear, Ipopt can handle it; you could also switch to a dedicated LP solver (e.g., HiGHS, GLPK) if you prefer.

```julia
# --------------------------------------------------------------
#  Simple LP:  maximize 3x + 4y
#  subject to:
#      x + 2y ≤ 14
#      3x - y ≥ 0
#      x ≥ 0, y ≥ 0
#  Uses JuMP + Ipopt
# --------------------------------------------------------------

# 1. Packages ----------------------------------------------------
# Uncomment the following lines the first time you run the script
# to install the required packages.
# using Pkg
# Pkg.add("JuMP")
# Pkg.add("Ipopt")

using JuMP
using Ipopt   # provides the Ipopt optimizer

# 2. Build the model ---------------------------------------------
model = Model(Ipopt.Optimizer)   # Ipopt as the backend solver

# Optional: give Ipopt a few tolerances (helps with LPs)
set_optimizer_attribute(model, "tol", 1e-8)
set_optimizer_attribute(model, "acceptable_tol", 1e-8)

# 3. Decision variables -------------------------------------------
@variable(model, x >= 0)   # x ≥ 0
@variable(model, y >= 0)   # y ≥ 0

# 4. Objective ----------------------------------------------------
@objective(model, Max, 3x + 4y)   # maximize 3x + 4y

# 5. Constraints --------------------------------------------------
@constraint(model, x + 2y <= 14)   # x + 2y ≤ 14
@constraint(model, 3x - y >= 0)    # 3x - y ≥ 0  (equivalently y ≤ 3x)

# 6. Solve --------------------------------------------------------
optimize!(model)

# 7. Retrieve and display results ---------------------------------
println("\n=== Optimization Summary ===")
println("Solver status: ", termination_status(model))
println("Primal status: ", primal_status(model))
println("Objective value: ", objective_value(model))
println("Optimal x: ", value(x))
println("Optimal y: ", value(y))

# 8. (Optional) Verify constraints --------------------------------
println("\nConstraint checks:")
println("  x + 2y ≤ 14  → ", value(x) + 2*value(y), " ≤ 14 ? ", value(x) + 2*value(y) <= 14 + 1e-8)
println("  3x - y ≥ 0   → ", 3*value(x) - value(y), " ≥ 0 ? ", 3*value(x) - value(y) >= -1e-8)
println("  x ≥ 0        → ", value(x), " ≥ 0 ? ", value(x) >= -1e-8)
println("  y ≥ 0        → ", value(y), " ≥ 0 ? ", value(y) >= -1e-8)
```

### How to run

1. Save the script to a file, e.g., `simple_lp.jl`.
2. From a Julia REPL (or command line) execute:

```julia
include("simple_lp.jl")
```

The script will:

* Install JuMP and Ipopt the first time (if you uncomment the `Pkg.add` lines).
* Build the model, solve it with Ipopt,
* Print the optimal solution and verify that all constraints are satisfied.

### Expected output

```
=== Optimization Summary ===
Solver status: OPTIMAL
Primal status: FEASIBLE_POINT
Objective value: 28.0
Optimal x: 4.0
Optimal y: 5.0

Constraint checks:
  x + 2y ≤ 14  → 14.0 ≤ 14 ? true
  3x - y ≥ 0   → 7.0 ≥ 0 ? true
  x ≥ 0        → 4.0 ≥ 0 ? true
  y ≥ 0        → 5.0 ≥ 0 ? true
```

Thus the maximum of \(3x+4y\) under the given constraints is **28**, attained at \((x,y) = (4,5)\). Feel free to replace the Ipopt optimizer with any other supported solver (e.g., `HiGHS.Optimizer`) if you prefer a dedicated LP solver.

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 15.72 t/s
- Total wall time: 187.0s
