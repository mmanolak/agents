# Granite-3.1-8B-Instruct

**Date:** 2026-04-24 23:50:59
**Context:** 32768 tokens | **GPU layers:** 999

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 27.85 t/s | **Tokens:** 422 | **Time:** 15.15s

Here's an R script that accomplishes the task using the 'sf' and 'dplyr' packages:

```R
# Load required libraries
library(sf)
library(dplyr)

# Load the shapefiles
properties <- st_read("properties.shp")
golf_courses <- st_read("golf_courses.shp")

# Perform a spatial join to find the nearest golf course for each property
spatial_join <- st_join(properties, golf_courses, join = st_nearest_feature, return_list = TRUE)

# Extract the distance from the spatial join result
spatial_join$dist_to_golf_m <- sapply(spatial_join$., function(x) x$dist_golf_m)

# Remove the unnecessary join columns
spatial_join <- spatial_join[, -which(names(spatial_join) %in% c("dist_golf_m", "golf_course_id"))]

# Return the updated dataframe
return(spatial_join)
```

This script first loads the 'sf' and 'dplyr' packages and the two shapefiles. It then performs a spatial join using the `st_join()` function, specifying `st_nearest_feature` as the join type to find the nearest golf course for each property. The distance to the nearest golf course is extracted from the join result and added as a new column 'dist_to_golf_m'. Finally, the unnecessary join columns are removed, and the updated dataframe is returned.

Please note that this script assumes that the shapefiles have columns named 'dist_golf_m' and 'golf_course_id' in the join result. If the column names are different, you should adjust the script accordingly.

Also, ensure that the shapefiles are in the working directory or provide the full path to the files in the `st_read()` function.

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 27.93 t/s | **Tokens:** 382 | **Time:** 13.68s

Here's a Python script that performs a hedonic pricing regression using the 'statsmodels' library. This script assumes that 'data.csv' is a CSV file with columns 'log_price', 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf'.

```python
import pandas as pd
import statsmodels.api as sm

# Load the data
data = pd.read_csv('data.csv')

# Define the dependent and independent variables
y = data['log_price']
X = data[['bedrooms', 'bathrooms', 'sqft', 'dist_to_golf']]

# Add a constant term to the independent variables
X = sm.add_constant(X)

# Perform the regression
model = sm.OLS(y, X).fit()

# Print the summary statistics
print(model.summary())
```

This script first loads the data from 'data.csv' using pandas. It then defines the dependent variable 'log_price' and the independent variables 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf'. The constant term is added to the independent variables using the `sm.add_constant()` function.

The Ordinary Least Squares (OLS) regression is performed using the `sm.OLS()` function, and the fitted model is stored in the 'model' variable. Finally, the summary statistics of the regression are printed using the `print(model.summary())` statement.

Please ensure that the 'statsmodels' and 'pandas' libraries are installed in your Python environment. If not, you can install them using pip:

```bash
pip install statsmodels pandas
```

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 27.88 t/s | **Tokens:** 465 | **Time:** 16.68s

Here is a Julia script that uses the JuMP.jl and Ipopt.jl packages to solve the given optimization problem:

```julia
# Import necessary packages
using JuMP, Ipopt

# Define the optimization model
model = Model(Ipopt.Optimizer)

# Set the objective function to be maximized
@variable(model, x >= 0)
@variable(model, y >= 0)
@objective(model, Max, 3*x + 4*y)

# Add constraints
@constraint(model, x + 2*y <= 14)
@constraint(model, 3*x - y >= 0)

# Solve the optimization problem
optimize!(model)

# Print the results
println("Optimal solution:")
println("x = ", JuMP.value(x))
println("y = ", JuMP.value(y))
println("Maximum objective function value = ", JuMP.objective_value(model))
```

This script first imports the required packages, JuMP and Ipopt. It then creates a new optimization model using Ipopt as the solver. The objective function is defined as 3x + 4y, and the variables x and y are constrained to be non-negative. The constraints x + 2y <= 14 and 3x - y >= 0 are added to the model. Finally, the model is optimized, and the optimal values of x and y, as well as the maximum value of the objective function, are printed.

Please note that you need to have JuMP and Ipopt installed in your Julia environment. If not, you can install them using the package manager:

```julia
using Pkg
Pkg.add("JuMP")
Pkg.add("Ipopt")
```

Also, ensure that you have a compatible version of Ipopt installed on your system. You can download it from the official website: https://github.com/coin-or/Ipopt/releases. After downloading, follow the installation instructions provided for your specific operating system.

---

## Run statistics

- Prompts completed: 3/3
- Average speed: 27.89 t/s
- Total wall time: 45.5s
