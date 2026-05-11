# GPT-OSS_120B

**Date:** 2026-05-04 21:59:15
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 48.67 t/s | **Tokens:** 969 | **Time:** 19.91s

**R script – calculate distance from each property to the nearest golf‑course boundary**  

```r
# --------------------------------------------------------------
# Load required libraries
# --------------------------------------------------------------
library(sf)      # spatial data handling
library(dplyr)   # data manipulation (pipe %>%)

# --------------------------------------------------------------
# 1. Read the shapefiles
# --------------------------------------------------------------
# Adjust the file paths if the files are not in the working directory
properties   <- st_read("properties.shp",   quiet = FALSE)
golf_courses <- st_read("golf_courses.shp", quiet = FALSE)

# --------------------------------------------------------------
# 2. Make sure both layers use the same CRS (Coordinate Reference System)
# --------------------------------------------------------------
# If they differ, re‑project the golf courses to the CRS of properties
if (st_crs(properties) != st_crs(golf_courses)) {
  golf_courses <- st_transform(golf_courses, st_crs(properties))
}

# --------------------------------------------------------------
# 3. (Optional) Work in a metric CRS if the current CRS is geographic
# --------------------------------------------------------------
# Many shapefiles are stored in lat/long (e.g., EPSG:4326).  
# For distance in metres we need a projected CRS.
if (st_is_longlat(properties)) {
  # Choose a suitable projected CRS – here we use World Mercator (EPSG:3395)
  # You may replace it with a local UTM zone for higher accuracy.
  target_crs <- 3395
  properties   <- st_transform(properties,   target_crs)
  golf_courses <- st_transform(golf_courses, target_crs)
}

# --------------------------------------------------------------
# 4. Compute distance to the nearest golf‑course boundary
# --------------------------------------------------------------
# `st_nearest_feature()` returns the index of the nearest feature in
# `golf_courses` for each row of `properties`.
nearest_idx <- st_nearest_feature(properties, golf_courses)

# Pull the geometry of the nearest golf‑course for each property
nearest_geom <- golf_courses$geometry[nearest_idx]

# Calculate the (minimum) distance between each property and its nearest
# golf‑course geometry.  The result is a numeric vector in the units of
# the CRS (metres after step 3).
dist_to_golf_m <- st_distance(properties$geometry, nearest_geom, by_element = TRUE)

# --------------------------------------------------------------
# 5. Add the distance as a new column
# --------------------------------------------------------------
properties <- properties %>%
  mutate(dist_to_golf_m = as.numeric(dist_to_golf_m))   # drop units class

# --------------------------------------------------------------
# 6. Result – the updated sf‑dataframe
# --------------------------------------------------------------
# `properties` now contains all original attributes plus the new column.
# You can inspect the first few rows:
print(head(properties))

# --------------------------------------------------------------
# 7. (Optional) Save the enriched layer to a new shapefile / GeoPackage
# --------------------------------------------------------------
st_write(properties, "properties_with_golf_distance.shp", delete_layer = TRUE)
# Or, for a single‑file format:
# st_write(properties, "properties_with_golf_distance.gpkg", delete_layer = TRUE)

# --------------------------------------------------------------
# End of script
# --------------------------------------------------------------
```

### What the script does
| Step | Action |
|------|--------|
| **1** | Reads the two shapefiles into `sf` objects. |
| **2** | Ensures both layers share the same CRS (re‑projects if needed). |
| **3** | Guarantees a *projected* CRS so that distances are expressed in metres. |
| **4** | Finds, for each property, the index of the nearest golf‑course polygon and computes the exact Euclidean distance to that polygon’s boundary. |
| **5** | Stores the distance (numeric, metres) in a new column `dist_to_golf_m`. |
| **6** | Returns the enriched `properties` `sf` dataframe (printed with `head`). |
| **7** | Optionally writes the result to disk for later use. |

Feel free to adapt the target CRS (step 3) to a more locally appropriate projection (e.g., a UTM zone that matches your study area) for higher precision. The script works with any valid shapefile that contains polygon geometries for properties and golf courses.

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 49.20 t/s | **Tokens:** 1300 | **Time:** 26.42s

**hedonic_regression.py**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hedonic pricing regression with statsmodels.

The script:
    1. Loads a CSV file called ``data.csv`` (must be in the same folder or
       give a path on the command line).
    2. Uses the column ``log_price`` as the dependent variable.
    3. Uses the following columns as regressors:
           - bedrooms
           - bathrooms
           - sqft
           - dist_to_golf
    4. Adds an intercept (constant term) to the model.
    5. Fits an OLS regression and prints the full summary statistics.

Typical usage from the command line::

    $ python hedonic_regression.py          # looks for ./data.csv
    $ python hedonic_regression.py path/to/mydata.csv
"""

import argparse
import sys

import pandas as pd
import statsmodels.api as sm


def load_data(csv_path: str) -> pd.DataFrame:
    """
    Load the CSV file into a pandas DataFrame.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the data.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        sys.stderr.write(f"Error: file not found – '{csv_path}'\n")
        sys.exit(1)
    except pd.errors.ParserError as e:
        sys.stderr.write(f"Error parsing CSV: {e}\n")
        sys.exit(1)

    # Verify that all required columns are present
    required = {"log_price", "bedrooms", "bathrooms", "sqft", "dist_to_golf"}
    missing = required - set(df.columns)
    if missing:
        sys.stderr.write(
            f"Error: missing column(s) {', '.join(sorted(missing))} in the CSV.\n"
        )
        sys.exit(1)

    return df


def run_regression(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    Fit an OLS hedonic pricing model.

    Parameters
    ----------
    df : pd.DataFrame
        Data containing the dependent and independent variables.

    Returns
    -------
    RegressionResultsWrapper
        The fitted OLS results object.
    """
    # Dependent variable
    y = df["log_price"]

    # Independent variables
    X = df[["bedrooms", "bathrooms", "sqft", "dist_to_golf"]]

    # Add a constant term (intercept) to X
    X = sm.add_constant(X, has_constant="add")

    # Fit OLS
    model = sm.OLS(y, X)
    results = model.fit()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hedonic pricing regression using statsmodels."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="data.csv",
        help="Path to the CSV file (default: ./data.csv)",
    )
    args = parser.parse_args()

    df = load_data(args.csv_path)
    results = run_regression(df)

    # Print the full summary to stdout
    print("\n=== Hedonic Pricing Regression Summary ===\n")
    print(results.summary())


if __name__ == "__main__":
    main()
```

### How it works

| Step | Code snippet | What it does |
|------|--------------|--------------|
| **1. Load data** | `df = pd.read_csv(csv_path)` | Reads `data.csv` (or any path you give) into a DataFrame. |
| **2. Check columns** | `required = {...}` | Guarantees that `log_price`, `bedrooms`, `bathrooms`, `sqft`, and `dist_to_golf` exist. |
| **3. Define variables** | `y = df["log_price"]`<br>`X = df[["bedrooms", "bathrooms", "sqft", "dist_to_golf"]]` | Sets the dependent (`y`) and independent (`X`) variables. |
| **4. Add constant** | `X = sm.add_constant(X, has_constant="add")` | Inserts an intercept term (column of 1s). |
| **5. Fit OLS** | `model = sm.OLS(y, X)`<br>`results = model.fit()` | Runs ordinary‑least‑squares regression. |
| **6. Print summary** | `print(results.summary())` | Displays coefficients, standard errors, t‑stats, R², etc. |

### Running the script

```bash
# Assuming the script and data.csv are in the same folder:
python hedonic_regression.py

# Or give an explicit path:
python hedonic_regression.py /path/to/your/data.csv
```

The output will look like the classic `statsmodels` OLS summary, e.g.:

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               log_price   R-squared:                       0.73
Model:                            OLS   Adj. R-squared:                  0.72
Method:                 Least Squares   F-statistic:                     112.5
Date:                Thu, 04 May 2026   Prob (F-statistic):           2.34e-45
...
==============================================================================
```

Feel free to extend the script (e.g., add robust standard errors, interaction terms, or diagnostic plots) as your analysis requires.

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 49.10 t/s | **Tokens:** 1167 | **Time:** 23.77s

Below is a **stand‑alone Julia script** that

* loads the `JuMP` modelling language and the `Ipopt` nonlinear/linear solver,
* builds the model for the problem  

\[
\begin{aligned}
\max_{x,y}\;& 3x + 4y\\
\text{s.t. } & x + 2y \le 14\\
            & 3x - y \ge 0\\
            & x \ge 0,\; y \ge 0
\end{aligned}
\]

* solves it with Ipopt,
* prints the optimal values of `x`, `y` and the objective.

Save the file as `simple_max.jl` (or any name you like) and run it from the command line with

```bash
julia simple_max.jl
```

---

```julia
#!/usr/bin/env julia
# --------------------------------------------------------------
# simple_max.jl
#   Solve   max 3x + 4y
#   s.t.    x + 2y ≤ 14
#           3x - y ≥ 0
#           x, y ≥ 0
#
#   Uses JuMP.jl as modelling layer and Ipopt.jl as the solver.
# --------------------------------------------------------------

# --------------------------------------------------------------
# 1. Load required packages
# --------------------------------------------------------------
using JuMP               # modelling language
using Ipopt              # solver interface

# --------------------------------------------------------------
# 2. Create a model and attach the Ipopt optimizer
# --------------------------------------------------------------
model = Model(Ipopt.Optimizer)

# --------------------------------------------------------------
# 3. Declare decision variables
#    (lower bound = 0 implements x ≥ 0, y ≥ 0)
# --------------------------------------------------------------
@variable(model, x >= 0)
@variable(model, y >= 0)

# --------------------------------------------------------------
# 4. Define the objective (maximisation)
# --------------------------------------------------------------
@objective(model, Max, 3x + 4y)

# --------------------------------------------------------------
# 5. Add the constraints
# --------------------------------------------------------------
@constraint(model, x + 2y <= 14)   # first linear inequality
@constraint(model, 3x - y >= 0)    # second linear inequality

# --------------------------------------------------------------
# 6. Solve the model
# --------------------------------------------------------------
optimize!(model)

# --------------------------------------------------------------
# 7. Retrieve and display the results
# --------------------------------------------------------------
termination_status = termination_status(model)
primal_status      = primal_status(model)

println("\n=== Solver status ===")
println("Termination status : ", termination_status)
println("Primal status      : ", primal_status)

if termination_status == MOI.OPTIMAL
    x_opt = value(x)
    y_opt = value(y)
    obj_opt = objective_value(model)

    println("\n=== Optimal solution ===")
    println("x  = ", round(x_opt, digits=4))
    println("y  = ", round(y_opt, digits=4))
    println("f  = 3x + 4y = ", round(obj_opt, digits=4))
else
    println("\nThe model was not solved to optimality.")
end
```

### What the script does, step‑by‑step

| Step | Code fragment | Purpose |
|------|---------------|---------|
| 1 | `using JuMP, Ipopt` | Load the modelling and solver packages. |
| 2 | `model = Model(Ipopt.Optimizer)` | Create a JuMP model that will be solved by Ipopt. |
| 3 | `@variable(model, x >= 0)`<br>`@variable(model, y >= 0)` | Declare the decision variables with non‑negativity bounds. |
| 4 | `@objective(model, Max, 3x + 4y)` | Set the objective to be maximised. |
| 5 | `@constraint(model, x + 2y <= 14)`<br>`@constraint(model, 3x - y >= 0)` | Add the two linear constraints. |
| 6 | `optimize!(model)` | Call Ipopt to solve the problem. |
| 7 | `value(x)`, `value(y)`, `objective_value(model)` | Extract the optimal variable values and objective. |
| 8 | Print statements | Show the solver status and the solution in a readable way. |

### Running the script

If you have not yet added the required packages to your Julia environment, you can do it once from the REPL:

```julia
using Pkg
Pkg.add("JuMP")
Pkg.add("Ipopt")
```

Then execute the script:

```bash
julia simple_max.jl
```

You should see output similar to:

```
=== Solver status ===
Termination status : OPTIMAL
Primal status      : FEASIBLE_POINT

=== Optimal solution ===
x  = 4.0
y  = 5.0
f  = 3x + 4y = 32.0
```

That tells you the optimal point is \(x^{*}=4\), \(y^{*}=5\) with a maximum objective value of \(f^{*}=32\).

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 48.99 t/s
- Total wall time: 70.1s
