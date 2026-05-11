# Qwen3-Next-80B-Thinking-Uncensored

**Date:** 2026-05-04 22:06:56
**Context:** 32768 tokens | **GPU layers:** 999
**KV Cache:** F16 uncompressed (lightweight)

---

## R_1_Spatial_Join

> **Prompt:** Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: 'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate the exact distance from every property to the nearest golf course boundary. Add this distance as a new column called 'dist_to_golf_m' and return the updated dataframe.

**Speed:** 39.99 t/s | **Tokens:** 1678 | **Time:** 41.96s



---

## Py_2_Hedonic_Regression

> **Prompt:** Write a Python script using 'statsmodels' to perform a hedonic pricing regression. Load 'data.csv', define 'log_price' as the dependent variable, and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent variables. Include a constant term and print the summary statistics.

**Speed:** 40.06 t/s | **Tokens:** 2048 | **Time:** 51.12s



---

## Ju_3_Optimization

> **Prompt:** Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0.

**Speed:** 39.93 t/s | **Tokens:** 1551 | **Time:** 38.84s



---

## Run Statistics

- Prompts completed: 3/3
- Average speed: 39.99 t/s
- Total wall time: 131.9s
