# StarCoder2-15B-Instruct

**Date:** 2026-04-24 23:53:56
**Context:** 32768 tokens | **GPU layers:** 999

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 12.57 t/s | **Tokens:** 261 | **Time:** 20.76s

Here is an R script using the 'sf' and 'dplyr' packages to perform the spatial join and add the distance column:
```R
# Load the required packages
library(sf)
library(dplyr)
# Load the shapefiles
properties <- st_read("properties.shp")
golf_courses <- st_read("golf_courses.shp")
# Perform the spatial join
joined_df <- st_join(properties, golf_courses)
# Calculate the distance from each property to the nearest golf course boundary
dist_to_golf <- st_distance(joined_df)
# Add the distance as a new column called 'dist_to_golf_m'
joined_df <- mutate(joined_df, dist_to_golf_m = as.numeric(dist_to_golf))
# Return the updated dataframe
joined_df
```
Note that this script assumes that the 'properties.shp' and 'golf_courses.shp' files are in the same coordinate reference system (CRS). If they are in different CRS, you may need to convert one of them to match the other before performing the spatial join and distance calculation.

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 12.59 t/s | **Tokens:** 331 | **Time:** 26.30s

Here's a Python script that performs a hedonic pricing regression using the 'statsmodels' package. 
First, we need to import the necessary packages and load the data from the 'data.csv' file. 
```python
import pandas as pd
import statsmodels.api as sm
# Load the data
data = pd.read_csv('data.csv')
```
Next, we define the dependent variable and independent variables. In this case, the dependent variable is 'log_price', and the independent variables are 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf'. We also include a constant term.
```python
# Define the dependent variable and independent variables
X = sm.add_constant(data[['bedrooms', 'bathrooms', 'sqft', 'dist_to_golf']])
y = data['log_price']
```
Now, we can fit the regression model and print the summary statistics.
```python
# Fit the regression model
model = sm.OLS(y, X)
results = model.fit()
# Print the summary statistics
print(results.summary())
```
This script will perform a hedonic pricing regression using the 'statsmodels' package, using 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables and 'log_price' as the dependent variable. The output will include summary statistics such as coefficients, p-values, and R-squared.

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 12.55 t/s | **Tokens:** 232 | **Time:** 18.48s

Here is an example of how you can write the Julia script using the JuMP and Ipopt packages to solve the optimization problem:
```julia
using JuMP
using Ipopt
m = Model(solver=IpoptSolver())
@variable(m, x >= 0)
@variable(m, y >= 0)
@constraint(m, x + 2y <= 14)
@constraint(m, 3x - y >= 0)
@objective(m, Max, 3x + 4y)
status = solve(m)
println("Solution:")
println("x = ", value(x))
println("y = ", value(y))
```
This script creates a model using the Ipopt solver, defines the variables x and y as non-negative, adds the constraints, and sets the objective function to maximize f(x, y) = 3x + 4y. The solve function is called to solve the optimization problem, and the values of x and y are printed as the solution.

---

## Run statistics

- Prompts completed: 3/3
- Average speed: 12.57 t/s
- Total wall time: 65.5s
