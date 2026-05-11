# Granite-4.1-8B

**Date:** 2026-04-24 23:49:15
**Context:** 32768 tokens | **GPU layers:** 999

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 27.02 t/s | **Tokens:** 651 | **Time:** 24.09s

Certainly! Below is an R script that uses the `sf` and `dplyr` packages to load two shapefiles (`properties.shp` and `golf_courses.shp`), perform a spatial join to calculate the distance from each property to the nearest golf course boundary, and add this distance as a new column called `dist_to_golf_m`. The script then returns the updated dataframe.

```r
# Load required libraries
library(sf)
library(dplyr)

# Load the shapefiles
properties <- st_read("properties.shp")
golf_courses <- st_read("golf_courses.shp")

# Ensure both datasets are in the same coordinate reference system (CRS)
# If they are not, you can reproject one of them using st_transform()
# For example, if both should be in WGS 84 (EPSG:4326):
properties <- st_transform(properties, crs = 4326)
golf_courses <- st_transform(golf_courses, crs = 4326)

# Perform a spatial join to find the nearest golf course for each property
# Here, we use st_nearest_feature to find the nearest golf course boundary for each property
properties_with_golf_info <- properties %>%
  mutate(
    nearest_golf_id = st_nearest_feature(geometry, golf_courses$geometry),
    dist_to_golf_m = st_distance(
      geometry,
      golf_courses[nearest_golf_id, ]$geometry,
      by_element = TRUE
    )
  )

# Select and return the updated dataframe with the new distance column
updated_properties_df <- select(properties_with_golf_info, everything(), dist_to_golf_m)
print(updated_properties_df)
```

### Explanation of the Script:

1. **Load Libraries**: The script starts by loading the `sf` and `dplyr` packages, which are essential for handling spatial data and data manipulation, respectively.

2. **Load Shapefiles**: It reads the two shapefiles (`properties.shp` and `golf_courses.shp`) into spatial data frames using `st_read()`.

3. **Coordinate Reference System (CRS) Alignment**: It ensures both spatial data frames are in the same CRS. In this example, both are transformed to WGS 84 (EPSG:4326). If your data is already in the same CRS, you can skip this step.

4. **Spatial Join and Distance Calculation**:
   - `st_nearest_feature()` is used to find the index of the nearest golf course boundary for each property.
   - `st_distance()` calculates the distance from each property to its nearest golf course boundary. The `by_element = TRUE` argument ensures the distance is calculated for each property individually.

5. **Update and Return Dataframe**: The script adds the calculated distances as a new column `dist_to_golf_m` to the `properties` dataframe and returns this updated dataframe.

Make sure to replace `"properties.shp"` and `"golf_courses.shp"` with the actual paths to your shapefiles if they are located in different directories. Also, ensure that the spatial data is correctly projected and that the CRS transformation (if needed) is appropriate for your analysis.

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 27.06 t/s | **Tokens:** 642 | **Time:** 23.73s

To perform a hedonic pricing regression using the `statsmodels` library in Python, you'll need to follow these steps:

1. **Load the data** from a CSV file named `data.csv`.
2. **Define the dependent variable** as `log_price`.
3. **Specify the independent variables** as `bedrooms`, `bathrooms`, `sqft`, and `dist_to_golf`.
4. **Include a constant term** in the regression model.
5. **Fit the regression model** and print the summary statistics.

Below is a Python script that accomplishes these tasks:

```python
import pandas as pd
import statsmodels.api as sm

# Step 1: Load the data from 'data.csv'
data = pd.read_csv('data.csv')

# Step 2: Define the dependent variable and independent variables
# Assuming 'log_price' is already in the dataset as a logarithmic transformation of the price
# If not, you would need to compute it as np.log(data['price']) and rename it to 'log_price'
X = data[['bedrooms', 'bathrooms', 'sqft', 'dist_to_golf']]
y = data['log_price']

# Step 3: Add a constant term to the model
X = sm.add_constant(X)

# Step 4: Fit the regression model
model = sm.OLS(y, X).fit()

# Step 5: Print the summary statistics
print(model.summary())
```

### Explanation of the Script:

- **Importing Libraries**: We import `pandas` for data manipulation and `statsmodels.api` for statistical modeling.
- **Loading Data**: The `pd.read_csv('data.csv')` function reads the CSV file into a DataFrame.
- **Defining Variables**: 
  - `X` is set to the independent variables (`bedrooms`, `bathrooms`, `sqft`, `dist_to_golf`).
  - `y` is set to the dependent variable (`log_price`).
- **Adding a Constant**: `sm.add_constant(X)` adds an intercept term to the model, which is essential for most regression analyses.
- **Fitting the Model**: `sm.OLS(y, X).fit()` fits an Ordinary Least Squares regression model to the data.
- **Printing Summary**: `model.summary()` outputs a detailed summary of the regression results, including coefficients, standard errors, t-statistics, p-values, and R-squared, among other statistics.

### Note:
- Ensure that the `data.csv` file is in the same directory as your script, or provide the correct path to the file.
- The `log_price` column should already be the natural logarithm of the price. If it's not, you would need to compute it using `np.log(data['price'])` and rename the resulting column to `log_price` before running the script.
- The script assumes that all specified columns (`bedrooms`, `bathrooms`, `sqft`, `dist_to_golf`, `log_price`) exist in the `data.csv` file. Adjust column names as necessary to match your dataset.

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 27.06 t/s | **Tokens:** 613 | **Time:** 22.65s

Certainly! Below is a Julia script that uses the `JuMP` package for modeling the optimization problem and `Ipopt` as the solver to find the solution. The problem is to maximize the objective function \( f(x, y) = 3x + 4y \) subject to the given constraints.

First, ensure you have the necessary packages installed. You can install them using Julia's package manager if you haven't already:

```julia
using Pkg
Pkg.add("JuMP")
Pkg.add("Ipopt")
```

Now, here is the script:

```julia
# Import the required packages
using JuMP
using Ipopt

# Create a new optimization model with Ipopt as the solver
model = Model(Ipopt.Optimizer)

# Define the decision variables with non-negativity constraints
@variable(model, x >= 0)
@variable(model, y >= 0)

# Define the objective function to maximize
@objective(model, Max, 3*x + 4*y)

# Add the constraints to the model
@constraint(model, x + 2*y <= 14)
@constraint(model, 3*x - y >= 0)

# Solve the optimization problem
optimize!(model)

# Output the results
println("Optimal value of x: ", value(x))
println("Optimal value of y: ", value(y))
println("Maximum objective value: ", objective_value(model))
```

### Explanation of the Script:

1. **Import Packages**: The script starts by importing the `JuMP` package for modeling and `Ipopt` as the optimization solver.
2. **Create Model**: A new optimization model is created with `Ipopt.Optimizer`, indicating that we will use the IPOPT solver to solve the problem.
3. **Define Variables**: Decision variables `x` and `y` are defined with the constraint that they must be non-negative (`x >= 0`, `y >= 0`).
4. **Objective Function**: The objective function \( f(x, y) = 3x + 4y \) is set to be maximized using `@objective`.
5. **Constraints**: The constraints \( x + 2y \leq 14 \) and \( 3x - y \geq 0 \) are added to the model using `@constraint`.
6. **Solve the Model**: The `optimize!` function is called to solve the optimization problem.
7. **Output Results**: Finally, the optimal values of `x`, `y`, and the maximum objective value are printed.

### Running the Script:

To run this script, save it to a file, for example, `optimization_problem.jl`, and execute it in Julia:

```bash
julia optimization_problem.jl
```

This will output the optimal values of `x` and `y` that maximize the objective function under the given constraints, along with the maximum value of the objective function.

---

## Run statistics

- Prompts completed: 3/3
- Average speed: 27.05 t/s
- Total wall time: 70.5s
