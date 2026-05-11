# Kimi-Linear-48B-Q6_K

**Date:** 2026-05-08 23:55:00
**Engine:** Vulkan
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 53.32 t/s | **Tokens:** 239 | **Time:** 4.48s

```r
# Load required packages ----------------------------------------------------
library(sf)
library(dplyr)

# 1. Read the shapefiles -----------------------------------------------------
properties <- st_read("properties.shp")   # must be in the working directory
golf_courses <- st_read("golf_courses.shp")

# 2. Ensure both layers are in a projected CRS (e.g., UTM) -------------------
# If they are not already, re-project them to a common UTM zone:
properties <- st_transform(properties, crs = st_crs(golf_courses))

# 3. Spatial join: for every property find the nearest golf-course boundary --
nearest_gc <- st_nearest_feature(properties, golf_courses)   # index of nearest course

# Join the geometry of that nearest golf course to each property
joined <- properties %>%
  mutate(
    gc_geom = st_geometry(golf_courses[nearest_gc, ]),
    dist_to_golf_m = st_distance(., golf_courses[nearest_gc, ])
  )

# 4. Return the updated dataframe -------------------------------------------
# The 'dist_to_golf_m' column is already in metres (same CRS units)
joined
```

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 53.11 t/s | **Tokens:** 208 | **Time:** 3.92s

```python
"""
Hedonic pricing regression with statsmodels
------------------------------------------
Load data.csv, regress log_price on bedrooms, bathrooms,
sqft, and dist_to_golf (plus an intercept).
"""

import pandas as pd
import statsmodels.api as sm

# ------------------------------------------------------------------
# 1. Load the data
# ------------------------------------------------------------------
df = pd.read_csv("data.csv")

# ------------------------------------------------------------------
# 2. Prepare the regression specification
#    log_price ~ bedrooms + bathrooms + sqft + dist_to_golf + const
# ------------------------------------------------------------------
y = df["log_price"]                       # dependent variable
X = df[["bedrooms", "bathrooms", "sqft",
        "dist_to_golf"]]                  # independent variables

X = sm.add_constant(X)                    # add intercept (const)

# ------------------------------------------------------------------
# 3. Fit the model
# ------------------------------------------------------------------
model = sm.OLS(y, X).fit()

# ------------------------------------------------------------------
# 4. Display results
# ------------------------------------------------------------------
print(model.summary())
```

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 54.14 t/s | **Tokens:** 291 | **Time:** 5.37s

Here's a Julia script that uses **JuMP.jl** and **Ipopt.jl** to solve the optimization problem:

```julia
using JuMP
using Ipopt

# Create a model
model = Model(Ipopt.Optimizer)

# Define variables (non-negative)
@variable(model, x >= 0)
@variable(model, y >= 0)

# Set objective: maximize 3x + 4y
@objective(model, Max, 3x + 4y)

# Add constraints
@constraint(model, x + 2y <= 14)   # Constraint 1
@constraint(model, 3x - y >= 0)    # Constraint 2

# Solve the model
optimize!(model)

# Print results
if termination_status(model) == MOI.OPTIMAL
    println("Optimal solution found:")
    println("x = ", value(x))
    println("y = ", value(y))
    println("Maximum objective value = ", objective_value(model))
else
    println("Optimization failed to find an optimal solution.")
end
```

### Notes:
- `Ipopt.Optimizer()` is used as the solver backend.
- The `@variable` macro ensures both variables are non-negative.
- Constraints are added using `@constraint`.
- The result is printed only if a feasible and optimal solution is found.

You can run this script in a Julia environment with JuMP and Ipopt installed.

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 53.52 t/s
- Total wall time: 13.8s
