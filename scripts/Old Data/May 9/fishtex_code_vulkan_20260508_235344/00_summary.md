# FishTex Coding Benchmark — Vulkan Summary

**Date:** 2026-05-08 23:53:44
**System:** AMD Ryzen AI Max+ 395 | 128GB LPDDR5 @ 8000MHz | Fedora 43 Server
**Engine:** Vulkan — `~/llama.cpp/build-vulkan/bin/llama-server`
**KV Cache:** F16 uncompressed (lightweight — `-ctk`/`-ctv` removed)
**Batch:** `--ubatch-size 1024 --batch-size 2048`
**Models queued:** 6

| Model | Prompts run | Avg t/s | Total time |
|-------|-------------|---------|------------|
| Kimi-Linear-48B-Q6_K | 3/3 | 53.52 | 13.8s |
| Kimi-Linear-48B-Q6_K_L | 3/3 | 52.89 | 15.3s |
| Kimi-Linear-48B-Q8_0 | 3/3 | 48.47 | 16.5s |
| Llama4-Scout-UD-Q5_K_XL | FAILED — server did not start | — | — |
| Llama4-Scout-Q6_K | FAILED — server did not start | — | — |

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


# Kimi-Linear-48B-Q8_0

**Date:** 2026-05-08 23:59:08
**Engine:** Vulkan
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 48.68 t/s | **Tokens:** 279 | **Time:** 5.73s

```r
# Load required packages ----------------------------------------------------
library(sf)
library(dplyr)

# 1) Read the shapefiles -----------------------------------------------------
properties <- st_read("properties.shp")   # must be in the working directory or give full path
golf_courses <- st_read("golf_courses.shp")

# 2) Ensure both objects are in the same CRS --------------------------------
# If they are not, re-project one (here: WGS84 = EPSG:4326)
if (!st_crs(properties)@proj4string == st_crs(golf_courses)@proj4string) {
  properties <- st_transform(properties, st_crs(golf_courses))
}

# 3) Spatial join – find the nearest golf-course boundary for every property
#    st_nearest_feature returns the index of the closest feature in B for each feature in A
nearest_idx <- st_nearest_feature(properties, golf_courses)

# 4) Calculate exact distance between the two geometries ---------------------
distances <- st_distance(
                properties[nearest_idx, ],   # geometry from properties
                golf_courses                 # geometry from golf_courses
              )

# 5) Add the distance as a new column ---------------------------------------
properties <- properties %>%
  mutate(dist_to_golf_m = distances)

# 6) Return the updated dataframe -------------------------------------------
properties
```

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 47.95 t/s | **Tokens:** 215 | **Time:** 4.48s

```python
"""
Hedonic pricing regression with statsmodels
------------------------------------------
Load data.csv, regress log_price on bedrooms, bathrooms,
sqft and dist_to_golf (plus an intercept).

Usage:
    python hedonic.py
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
        "dist_to_golf"]]                 # independent variables

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

**Speed:** 48.78 t/s | **Tokens:** 308 | **Time:** 6.31s

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
@objective(model, Max, 3*x + 4*y)

# Add constraints
@constraint(model, x + 2*y <= 14)   # Constraint 1
@constraint(model, 3*x - y >= 0)    # Constraint 2

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
- `Ipopt.Optimizer` is used as the solver.
- The `@variable` macro ensures `x` and `y` are non-negative.
- The `@objective` macro sets the objective function to maximize.
- Constraints are added using `@constraint`.
- After solving, it checks if an optimal solution was found and prints the results.

You can run this script in a Julia environment with both packages installed.

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 48.47 t/s
- Total wall time: 16.5s


# Kimi-Linear-48B-Q6_K_L

**Date:** 2026-05-08 23:56:48
**Engine:** Vulkan
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 52.74 t/s | **Tokens:** 268 | **Time:** 5.08s

```r
# Load required packages ----------------------------------------------------
library(sf)
library(dplyr)

# 1. Read the shapefiles ----------------------------------------------------
properties <- st_read("properties.shp")   # must be in the working directory or give full path
golf_courses <- st_read("golf_courses.shp")

# 2. Ensure both objects are valid simple-features --------------------------
st_is_valid(properties)
st_is_valid(golf_courses)

# 3. Spatial join: find the nearest golf-course boundary for every property #
#    st_nearest_feature returns the index of the closest feature in B for each
#    feature in A; we then pull the geometry and compute the exact distance.
nearest_idx <- st_nearest_feature(properties, golf_courses)

# Extract the geometry of the nearest golf-course boundary
golf_boundary <- golf_courses[nearest_idx, ]

# Compute the exact (ellipsoidal) distance between each property and its
# nearest golf-course boundary.  Units are metres by default.
dist_to_golf_m <- st_distance(properties, golf_boundary)

# 4. Add the distance as a new column ---------------------------------------
properties_with_dist <- properties %>%
  mutate(dist_to_golf_m = dist_to_golf_m)

# 5. Return the updated dataframe -------------------------------------------
properties_with_dist
```

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 52.40 t/s | **Tokens:** 227 | **Time:** 4.33s

```python
"""
Hedonic pricing regression using statsmodels.
-------------------------------------------------
The script:
1. Loads data.csv
2. Defines log_price as the dependent variable
3. Uses bedrooms, bathrooms, sqft, and dist_to_golf as independent variables
4. Includes a constant term (intercept)
5. Prints the OLS regression summary
"""

import pandas as pd
import statsmodels.api as sm

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------
df = pd.read_csv("data.csv")

# ------------------------------------------------------------------
# 2. Define dependent and independent variables
# ------------------------------------------------------------------
y = df["log_price"]                       # Dependent variable
X = df[["bedrooms", "bathrooms", "sqft", "dist_to_golf"]]  # Independent vars

# Add a constant (intercept) to the design matrix
X = sm.add_constant(X)

# ------------------------------------------------------------------
# 3. Fit OLS regression
# ------------------------------------------------------------------
model = sm.OLS(y, X).fit()

# ------------------------------------------------------------------
# 4. Print regression summary
# ------------------------------------------------------------------
print(model.summary())
```

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 53.54 t/s | **Tokens:** 314 | **Time:** 5.86s

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
    println("Maximum value of objective function: ", objective_value(model))
else
    println("Optimization failed to find an optimal solution.")
end
```

### Notes:
- `Ipopt.Optimizer` is used as the solver.
- The `@variable` macro ensures `x` and `y` are non-negative.
- The `@objective` macro sets the goal to **maximize** the function.
- Constraints are added using `@constraint`.
- After solving, it checks if an optimal solution was found and prints the results.

You can run this script in a Julia environment with both packages installed.

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 52.89 t/s
- Total wall time: 15.3s
