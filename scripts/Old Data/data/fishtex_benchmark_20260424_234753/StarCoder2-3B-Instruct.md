# StarCoder2-3B-Instruct

**Date:** 2026-04-24 23:48:29
**Context:** 32768 tokens | **GPU layers:** 999

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 53.76 t/s | **Tokens:** 143 | **Time:** 2.66s


# Load necessary packages
library(sf)
library(dplyr)

# Load shapefiles
properties <- st_read('properties.shp')
golf_courses <- st_read('golf_courses.shp')

# Calculate distance
properties <- properties %>%
  st_join(golf_courses, join = st_nearest_feature) %>%
  st_distance(golf_courses)

# Add distance to new column
properties <- properties %>%
  mutate(dist_to_golf_m = as.numeric(dist_to_golf_m))

# Return updated dataframe
properties
<|im_end|>

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 54.15 t/s | **Tokens:** 145 | **Time:** 2.68s

import pandas as pd
import statsmodels.api as sm

# Load data
data = pd.read_csv('data.csv')

# Define dependent variable
data['log_price'] = np.log(data['price'])

# Define independent variables
X = data[['bedrooms', 'bathrooms', 'sqft', 'dist_to_golf']]

# Add constant term
X = sm.add_constant(X)

# Fit the model
model = sm.OLS(data['log_price'], X).fit()

# Print the summary
print(model.summary())
<|im_end|>

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 54.31 t/s | **Tokens:** 180 | **Time:** 3.31s

using JuMP, Ipopt

# Define the problem
@model

# Define the objective function
@objective(Max, "Max", 3*x + 4*y)

# Define the constraints
@constraint(x + 2*y <= 14)
@constraint(3*x - y >= 0)
@constraint(x >= 0)
@constraint(y >= 0)

# Solve the problem
solver = Ipopt.Solver(solver_name="ipopt")
status = solver.solve(model, solver)

# Print the solution
println("Optimal value: ", solver.objective_value)
println("Optimal x: ", x.value)
println("Optimal y: ", y.value)
<|im_end|>

---

## Run statistics

- Prompts completed: 3/3
- Average speed: 54.07 t/s
- Total wall time: 8.7s
