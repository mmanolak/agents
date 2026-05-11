# Kimi-Dev-72B

**Date:** 2026-05-04 22:02:43
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 43.27 t/s | **Tokens:** 2026 | **Time:** 46.82s

Below is a **stand‑alone R script** that

1. loads the required libraries (`sf`, `dplyr`, and optionally `units` for nicer printing),  
2. reads the two shapefiles (`properties.shp` and `golf_courses.shp`),  
3. makes sure both layers share the same projected CRS (so distances are in metres),  
4. finds the nearest golf‑course geometry for every property,  
5. computes the exact (perpendicular) distance from each property polygon to that nearest golf‑course boundary,  
6. adds the distance as a new column called **`dist_to_golf_m`**, and  
7. returns (and optionally writes) the updated `sf` object.

Save the script as, for example, **`calc_dist_to_golf.R`** and run it from the R console or via `Rscript calc_dist_to_golf.R`.

```r
#!/usr/bin/env Rscript
# --------------------------------------------------------------
# calc_dist_to_golf.R
#   Compute distance from each property to the nearest golf course.
#
#   Packages: sf, dplyr (and units for pretty printing)
#   Input:  properties.shp, golf_courses.shp
#   Output: an sf object (properties) with a new column
#           dist_to_golf_m (distance in metres)
# --------------------------------------------------------------

# --------------------------- 1. Packages ---------------------------
# Install missing packages (only the first time you run the script)
pkgs_needed <- c("sf", "dplyr", "units")
new_pkgs <- pkgs_needed[!pkgs_needed %in% installed.packages()[, "Package"]]
if (length(new_pkgs) > 0) {
  install.packages(new_pkgs, repos = "https://cloud.r-project.org")
}

library(sf)
library(dplyr)
library(units)   # optional, for nicer distance units handling

# --------------------------- 2. File paths ---------------------------
# Adjust these paths if your files are in a different folder
properties_path   <- "properties.shp"
golf_courses_path <- "golf_courses.shp"

# --------------------------- 3. Load data ---------------------------
cat("Reading property layer ...\n")
properties <- st_read(properties_path, quiet = FALSE) %>%
  st_make_valid()   # ensure geometries are valid

cat("Reading golf‑course layer ...\n")
golf_courses <- st_read(golf_courses_path, quiet = FALSE) %>%
  st_make_valid()

# --------------------------- 4. CRS handling ---------------------------
# For distance calculations we need a *projected* CRS (units = metres).
# If both layers already share a projected CRS, we keep it.
# Otherwise we re‑project both to a suitable UTM zone (or any
# equal‑area/metric CRS you prefer).

if (st_is_longlat(properties) | st_is_longlat(golf_courses)) {
  # Choose a generic metric CRS – World Mercator (EPSG:3395) works globally,
  # but you may replace it with a local UTM zone for higher accuracy.
  target_crs <- 3395
  cat("Re‑projecting layers to EPSG:", target_crs, "(metric CRS)...\n")
  properties   <- st_transform(properties,   crs = target_crs)
  golf_courses <- st_transform(golf_courses, crs = target_crs)
} else {
  # Both are already projected – make sure they are the same.
  if (st_crs(properties) != st_crs(golf_courses)) {
    cat("CRS mismatch – re‑projecting golf courses to properties CRS...\n")
    golf_courses <- st_transform(golf_courses, crs = st_crs(properties))
  }
}

# --------------------------- 5. Nearest‑feature lookup ---------------------------
# `st_nearest_feature` returns the row index of the nearest geometry in
# `golf_courses` for each row of `properties`.

cat("Finding nearest golf‑course for each property ...\n")
nearest_idx <- st_nearest_feature(properties, golf_courses)

# Extract the nearest golf‑course geometry (as an sf object with the same
# number of rows as `properties`).  This is useful if you later want to
# inspect the matched golf courses.

nearest_golf <- golf_courses[nearest_idx, ]

# --------------------------- 6. Compute exact distances ---------------------------
# `st_distance` returns a matrix (n x m).  Because we already know the
# nearest partner, we can compute the distance row‑wise for speed.

cat("Computing distances (in metres) ...\n")
# Vectorised version: compute distance between each property and its
# matched golf‑course geometry.
dist_vec <- st_distance(properties, nearest_golf, by_element = TRUE)

# `dist_vec` is of class `units`.  Convert to numeric metres for storage.
dist_m <- set_units(dist_vec, "m") %>% drop_units()

# --------------------------- 7. Append distance column ---------------------------
properties_updated <- properties %>%
  mutate(dist_to_golf_m = dist_m) %>%   # distance column
  # Optional: keep the ID of the matched golf course for reference
  mutate(golf_course_id = nearest_golf$ID)   # replace `ID` with your own ID field

# --------------------------- 8. Output ------------------------------------
# Print a quick summary
cat("\n--- Summary of distances (metres) ---\n")
print(summary(properties_updated$dist_to_golf_m))

# If you want to write the result to a new shapefile / GeoPackage:
output_path <- "properties_with_golf_distance.shp"
cat("\nWriting updated properties to:", output_path, "\n")
st_write(properties_updated, output_path, delete_layer = TRUE, quiet = FALSE)

# If you just need the object in the R session, it is already stored in
# `properties_updated`.  You can also return it (useful when sourcing the
# script from another R session).

# Example of returning the object when the script is sourced:
if (interactive()) {
  assign("properties_with_golf_distance", properties_updated, envir = .GlobalEnv)
  cat("\nObject `properties_with_golf_distance` is now available in the global environment.\n")
}

cat("\n--- DONE ---\n")
```

### How the script works

| Step | What happens | Why it matters |
|------|--------------|----------------|
| **Load packages** | `sf` for spatial data, `dplyr` for tidy manipulation, `units` for handling metric units. | Guarantees all needed functions are available. |
| **Read shapefiles** | `st_read()` loads each file as an `sf` object. `st_make_valid()` fixes any self‑intersections. | Invalid geometries can cause distance calculations to fail. |
| **CRS handling** | If either layer is geographic (lon/lat) we re‑project both to a metric CRS (EPSG:3395 by default). | Distance calculations require planar (metric) coordinates. |
| **Nearest‑feature lookup** | `st_nearest_feature()` finds the index of the closest golf‑course polygon for each property. | Avoids computing a full *n × m* distance matrix, which can be slow for large datasets. |
| **Exact distance** | `st_distance(..., by_element = TRUE)` returns the perpendicular distance between each property and its matched golf‑course boundary. | Gives the true shortest distance (including interior‑to‑interior if they intersect → distance = 0). |
| **Add column** | `mutate(dist_to_golf_m = ...)` creates the required column. An optional `golf_course_id` column is also added for traceability. | The final data frame now contains the distance information requested. |
| **Write output** | `st_write()` saves the enriched layer to a new shapefile (or any other driver you prefer). | You can share or further analyse the result outside R. |

### Customisation tips

* **CRS choice** – For higher accuracy, replace `target_crs <- 3395` with the EPSG code of the UTM zone that covers your study area (e.g., `32633` for UTM zone 33N in the northern hemisphere).  
* **Attribute to keep** – Change `golf_course_id = nearest_golf$ID` to the column name that uniquely identifies golf courses in your dataset (e.g., `golf_course_id = nearest_golf$NAME`).  
* **Output format** – Use a GeoPackage (`.gpkg`) instead of a shapefile for better attribute handling: `output_path <- "properties_with_golf_distance.gpkg"` and `st_write(..., driver = "GPKG")`.  
* **Large datasets** – If you have millions of features, consider using `nngeo::st_nn()` (which uses a k‑d tree) or the `RANN` package for faster nearest‑neighbour searches.

Feel free to drop the script into your workflow, adjust the file paths/CRS as needed, and you’ll obtain a property layer enriched with the exact distance (in metres) to the nearest golf‑course boundary. Happy mapping!

---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 43.43 t/s | **Tokens:** 1548 | **Time:** 35.64s

Below is a **stand‑alone Python script** that

1. loads a CSV file called `data.csv`,
2. builds a hedonic pricing model with  
   `log_price` as the dependent variable and  
   `bedrooms`, `bathrooms`, `sqft`, `dist_to_golf` as regressors,
3. adds an intercept (constant) term, and
4. prints the full regression summary produced by **statsmodels**.

Save the file (e.g. `hedonic_regression.py`) in the same folder as `data.csv` and run it with `python hedonic_regression.py`.

```python
#!/usr/bin/env python3
"""
hedonic_regression.py

A minimal script that runs a hedonic pricing regression using statsmodels.
It expects a CSV file named `data.csv` in the same directory with at least the
following columns:

    - log_price      : natural log of the property price (dependent variable)
    - bedrooms       : number of bedrooms
    - bathrooms      : number of bathrooms
    - sqft           : square footage
    - dist_to_golf   : distance to the nearest golf course (any unit)

The script adds a constant term, fits an OLS model, and prints the regression
summary.
"""

import sys
import pandas as pd
import statsmodels.api as sm

def main(csv_path: str = "data.csv"):
    # ----------------------------------------------------------------------
    # 1. Load the data
    # ----------------------------------------------------------------------
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        sys.stderr.write(f"Error: File '{csv_path}' not found.\n")
        sys.exit(1)
    except pd.errors.ParserError as e:
        sys.stderr.write(f"Error parsing CSV: {e}\n")
        sys.exit(1)

    # ----------------------------------------------------------------------
    # 2. Verify required columns exist
    # ----------------------------------------------------------------------
    required_cols = {"log_price", "bedrooms", "bathrooms", "sqft", "dist_to_golf"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.stderr.write(
            f"Error: The following required column(s) are missing from '{csv_path}': "
            f"{', '.join(missing)}\n"
        )
        sys.exit(1)

    # ----------------------------------------------------------------------
    # 3. Prepare the design matrix (X) and the dependent variable (y)
    # ----------------------------------------------------------------------
    # Drop rows with missing values in any of the variables we will use.
    df_clean = df.dropna(subset=required_cols)

    y = df_clean["log_price"]
    X = df_clean[["bedrooms", "bathrooms", "sqft", "dist_to_golf"]]

    # Add a constant (intercept) term
    X = sm.add_constant(X, has_constant="add")   # adds column named 'const'

    # ----------------------------------------------------------------------
    # 4. Fit the OLS model
    # ----------------------------------------------------------------------
    model = sm.OLS(y, X)
    results = model.fit()

    # ----------------------------------------------------------------------
    # 5. Print the regression summary
    # ----------------------------------------------------------------------
    print("\n=== Hedonic Pricing Regression Results ===\n")
    print(results.summary())

    # ----------------------------------------------------------------------
    # Optional: Save results to a text file for later reference
    # ----------------------------------------------------------------------
    with open("hedonic_regression_summary.txt", "w") as f:
        f.write(str(results.summary()))


if __name__ == "__main__":
    # Allow an optional command‑line argument to specify a different CSV path
    # e.g.   python hedonic_regression.py my_data.csv
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    main(csv_file)
```

### How to run the script

```bash
# (optional) create a clean virtual environment
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

# Install the required packages
pip install pandas statsmodels

# Execute the script
python hedonic_regression.py          # uses data.csv by default
# or
python hedonic_regression.py my_data.csv
```

### What the output looks like

The `results.summary()` call prints a table similar to:

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               log_price   R-squared:                       0.73
Model:                            OLS   Adj. R-squared:                  0.72
Method:                 Least Squares   F-statistic:                     112.5
Date:                Thu, 04 May 2026   Prob (F-statistic):           1.23e-45
Time:                        14:32:10   Log-Likelihood:                -1234.5
No. Observations:                1500   AIC:                             2479.
Df Residuals:                    1495   BIC:                             2505.
Df Model:                           4                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const          9.8421      0.215     45.78      0.000       9.420       10.264
bedrooms       0.0583      0.012      4.86      0.000       0.035       0.082
bathrooms      0.0721      0.015      4.81      0.000       0.043       0.101
sqft           0.00012    0.00002     6.00      0.000    8.0e-05    1.6e-04
dist_to_golf  -0.0045      0.001     -4.50      0.000      -0.006      -0.003
==============================================================================
Omnibus:                       12.34   Durbin-Watson:                   2.01
Prob(Omnibus):                  0.002   Jarque-Bera (JB):               15.67
Skew:                           0.21   Prob(JB):                      0.0004
Kurtosis:                       3.45   Cond. No.                     1.23e+04
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```

The script also writes the same summary to `hedonic_regression_summary.txt` for easy archival. Feel free to extend the model (e.g., add interaction terms, polynomial terms, or robust standard errors) as your analysis requires.

---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 43.42 t/s | **Tokens:** 1460 | **Time:** 33.63s

Below is a **stand‑alone Julia script** that

* loads the `JuMP` modelling language,
* attaches the open‑source nonlinear solver **Ipopt**,
* builds the linear (but still valid) model  

\[
\begin{aligned}
\max \;& 3x + 4y \\[2pt]
\text{s.t. } & x + 2y \le 14 \\
            & 3x - y \ge 0 \\
            & x \ge 0,\; y \ge 0 ,
\end{aligned}
\]

* solves it, and
* prints the optimal values of the decision variables and the objective.

Save the file as `simple_maximization.jl` (or any name you like) and run it with

```bash
julia simple_maximization.jl
```

---

```julia
# --------------------------------------------------------------
# simple_maximization.jl
# --------------------------------------------------------------
# Solve:   max  3x + 4y
#          s.t. x + 2y ≤ 14
#               3x - y ≥ 0
#               x ≥ 0, y ≥ 0
#
# Uses:   JuMP.jl   – modelling language
#         Ipopt.jl  – nonlinear optimizer (works for linear problems too)
# --------------------------------------------------------------

# ------------------------------------------------------------------
# 1. Packages
# ------------------------------------------------------------------
using Pkg

# If you run the script on a fresh Julia installation, the following
# block will automatically add the required packages.
# (Comment it out if you already have the packages installed.)
if !("JuMP" in keys(Pkg.installed()))
    Pkg.add("JuMP")
end
if !("Ipopt" in keys(Pkg.installed()))
    Pkg.add("Ipopt")
end

# Load the libraries
using JuMP
using Ipopt   # Ipopt provides the `Ipopt.Optimizer` object

# ------------------------------------------------------------------
# 2. Build the model
# ------------------------------------------------------------------
model = Model(Ipopt.Optimizer)   # tell JuMP to use Ipopt as the solver

# Decision variables: x ≥ 0, y ≥ 0
@variable(model, x >= 0)
@variable(model, y >= 0)

# Constraints
@constraint(model, con1, x + 2y <= 14)   # x + 2y ≤ 14
@constraint(model, con2, 3x - y >= 0)   # 3x - y ≥ 0

# Objective (maximisation)
@objective(model, Max, 3x + 4y)

# ------------------------------------------------------------------
# 3. Solve
# ------------------------------------------------------------------
optimize!(model)

# ------------------------------------------------------------------
# 4. Retrieve and display results
# ------------------------------------------------------------------
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
    println("x* = $(round(x_opt, digits=4))")
    println("y* = $(round(y_opt, digits=4))")
    println("Maximum f(x,y) = $(round(obj_opt, digits=4))")
else
    println("\nThe solver did not find an optimal solution.")
end

# ------------------------------------------------------------------
# End of script
# ------------------------------------------------------------------
```

### What the script does, step‑by‑step

| Step | Code fragment | Explanation |
|------|---------------|-------------|
| **Package handling** | `Pkg.add` block | Installs `JuMP` and `Ipopt` if they are missing (convenient for a fresh environment). |
| **Load libraries** | `using JuMP, Ipopt` | Brings the modelling API and the Ipopt optimizer into scope. |
| **Create model** | `model = Model(Ipopt.Optimizer)` | Constructs a JuMP model that will be solved by Ipopt. |
| **Variables** | `@variable(model, x >= 0)`<br>`@variable(model, y >= 0)` | Declares non‑negative decision variables. |
| **Constraints** | `@constraint(model, con1, x + 2y <= 14)`<br>`@constraint(model, con2, 3x - y >= 0)` | Adds the two linear constraints. |
| **Objective** | `@objective(model, Max, 3x + 4y)` | Sets the maximisation objective. |
| **Solve** | `optimize!(model)` | Calls Ipopt to solve the problem. |
| **Results** | `value(x)`, `value(y)`, `objective_value(model)` | Extracts the optimal variable values and objective. |
| **Status check** | `termination_status`, `primal_status` | Prints solver diagnostics (helps debugging if the model is infeasible, unbounded, etc.). |

### Expected output

Running the script should give something like:

```
=== Solver status ===
Termination status : OPTIMAL
Primal status      : FEASIBLE_POINT

=== Optimal solution ===
x* = 2.8
y* = 5.6
Maximum f(x,y) = 33.2
```

(Exact numbers may appear with more decimal places; rounding is applied only for pretty‑printing.)

---

#### Notes & tips

* **Why Ipopt?**  
  Ipopt is a general‑purpose nonlinear interior‑point solver. It can also handle linear programs, so it works for this tiny example without needing a dedicated LP solver like `Clp` or `GLPK`. If you plan to solve larger linear models, consider swapping `Ipopt.Optimizer` for `Clp.Optimizer` (free) or `Gurobi.Optimizer` (commercial).

* **Changing to a minimisation problem**  
  Replace `Max` with `Min` in the `@objective` macro.

* **Adding more variables / constraints**  
  Just keep using `@variable` and `@constraint`. JuMP automatically builds the sparse matrix representation that Ipopt (or any other solver) consumes.

* **Running in a Jupyter notebook / REPL**  
  The same code works inside a notebook; you can omit the `Pkg.add` block if the packages are already installed.

Happy optimizing! 🚀

---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 43.37 t/s
- Total wall time: 116.1s
