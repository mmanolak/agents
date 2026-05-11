"""
FishTex Autocomplete Benchmark -- bench_complete.py (v6 - Final)
=================================================================
System:  AMD Ryzen AI Max+ 395 (Strix Halo) | 128GB LPDDR5 | Fedora 43
eGPU:    NVIDIA RTX 3060 Ti 8GB via TB4 (AOOSTAR AG02)
ROCm:    6.4.0 | gfx1151 native | llama.cpp build 8850 (ROCm)
CUDA:    13.2  | sm_86          | llama.cpp build 8940 (CUDA)

All 19 models route to CUDA (RTX 3060 Ti).
All confirmed under 6.0GB — fit within 7698 MiB usable VRAM.

HIP_VISIBLE_DEVICES, HSA_OVERRIDE_GFX_VERSION, CUDA_VISIBLE_DEVICES
are set system-wide via /etc/profile.d/rocm-env.sh — not set inline.

OUTPUT: Single timestamped .md file. Script exits cleanly when done.
No system shutdown. No reboot. Server is terminated between models only.

FIM token modes:
  fim_qwen      : <|fim_prefix|> / <|fim_suffix|> / <|fim_middle|>
  fim_starcoder : <fim_prefix> / <fim_suffix> / <fim_middle>
  fim_codegemma : <|fim_prefix|> / <|fim_suffix|> / <|fim_middle|>  (same as qwen, different stop)
  generic       : chat-style instruction prompt (no native FIM tokens)
  raw           : bare prefix only (tiny models without FIM training)

BEHAVIOR:
  - Server boots once per model, stays up for ALL prompts on that model
  - WARMUP_RUNS discarded runs prime KV cache before timing begins
  - RUNS_PER_PROMPT timed runs recorded with full statistics
  - Single .md report written incrementally (safe against crashes)
  - Script prints [DONE] and exits cleanly — no shutdown/reboot
"""

import subprocess
import time
import requests
import os
import sys
import math
from datetime import datetime

# ==============================================================================
# BINARIES
# ==============================================================================
CUDA_BIN = os.path.expanduser("~/llama.cpp-cuda/build/bin/llama-server")
ROCM_BIN = os.path.expanduser("~/llama.cpp/build/bin/llama-server")

# ==============================================================================
# PATHS
# ==============================================================================
MODEL_DIR   = os.path.expanduser("~/ai_vault/auto-correct")
REPORT_DIR  = os.path.expanduser("~/ai_vault")

# ==============================================================================
# PORT — isolated from all live servers (8080/8082/8084/8085)
# ==============================================================================
PORT = 8086

# ==============================================================================
# BENCHMARK TUNING
# ==============================================================================
THREADS          = 8       # Leaves cores free for OS and live research servers
UBATCH           = 512     # Small — autocomplete prompts are short
BATCH            = 2048
BOOT_TIMEOUT     = 180     # 3 min — small models load fast
INFER_TIMEOUT    = 45      # Hard cap per inference — if it takes >45s it's not autocomplete
COOLDOWN         = 15      # Between models — lets VRAM fully release
WARMUP_RUNS      = 2       # Discarded runs that prime the KV cache
RUNS_PER_PROMPT  = 10      # Timed runs — statistically meaningful sample
MAX_TOKENS       = 128     # Completions should be short and focused
TEMPERATURE      = 0.1     # Low temp for deterministic, accurate completions


# ==============================================================================
# MODEL REGISTRY — 19 models, all CUDA
# Exact filenames verified against: ls ~/ai_vault/auto-correct/
#
# FIM mode key:
#   fim_qwen      → Qwen2.5-Coder, Granite, Yi-Coder family
#   fim_starcoder → StarCoder2 family
#   fim_codegemma → CodeGemma base (pure FIM model, Qwen-style tokens + diff stop)
#   generic       → Llama/Gemma instruct models without native FIM
#   raw           → Sub-500M models, bare prefix completion
# ==============================================================================
models = {

    # ── MICRO TIER (under 500MB) ──────────────────────────────────────────────

    "Kimi-Coder-135M": {
        "path":    "kimi-coder-135m.Q8_0.gguf",                           # 139 MB
        "mode":    "raw",
        "stop":    ["<|endoftext|>"],
    },

    # ── SMALL TIER (0.5B – 1.5B) ─────────────────────────────────────────────

    "Qwen2.5-Coder-0.5B": {
        "path":    "qwen2.5-coder-0.5b-instruct-q8_0.gguf",               # ~500 MB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },
    "Qwen2.5-Coder-1.5B": {
        "path":    "Qwen2.5-Coder-1.5B-Instruct-Q8_0.gguf",               # ~1.6 GB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },

    # ── MID TIER (3B) ────────────────────────────────────────────────────────

    "StarCoder2-3B": {
        "path":    "starcoder2-3b-Q8_0.gguf",                             # 3.1 GB
        "mode":    "fim_starcoder",
        "stop":    ["<|endoftext|>"],
    },

    # ── 7B TIER — Qwen Coder family ──────────────────────────────────────────

    "Qwen2.5-Coder-7B-Base": {
        "path":    "Qwen2.5-Coder-7B.Q5_K_M.gguf",                       # 5.1 GB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },
    "Qwen2.5-Coder-7B-Instruct": {
        "path":    "Qwen2.5.1-Coder-7B-Instruct-Q5_K_M.gguf",            # 5.1 GB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },
    "Qwen2.5-Coder-7B-Abliterated": {
        "path":    "Qwen2.5-Coder-7B-Instruct-abliterated-Q5_K_M.gguf",  # 5.1 GB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },

    # ── 7B TIER — StarCoder2 family ──────────────────────────────────────────

    "StarCoder2-7B-Base": {
        "path":    "starcoder2-7b-Q5_K_M.gguf",                          # 4.8 GB
        "mode":    "fim_starcoder",
        "stop":    ["<|endoftext|>"],
    },
    "StarCoder2-7B-Instruct": {
        "path":    "starcoder2-7b-instruct.Q5_K_M.gguf",                 # 4.9 GB
        "mode":    "fim_starcoder",
        "stop":    ["<|endoftext|>"],
    },

    # ── 7B TIER — CodeGemma (pure FIM pretrained) ────────────────────────────

    "CodeGemma-7B": {
        "path":    "codegemma-7b-Q5_K_M.gguf",                           # ~5.0 GB
        "mode":    "fim_codegemma",
        "stop":    ["<|file_separator|>", "<eos>", "<|endoftext|>"],
    },

    # ── 7B TIER — Mamba architecture ─────────────────────────────────────────

    "Mamba-Codestral-7B": {
        "path":    "Mamba-Codestral-7B-v0.1-Q6_K.gguf",                  # 5.99 GB
        "mode":    "fim_starcoder",   # Codestral uses StarCoder-style FIM tokens
        "stop":    ["<|endoftext|>"],
    },

    # ── 7-9B TIER — Granite hybrid (Mamba-2 + MoE) ───────────────────────────

    "Granite-4.0-H-Tiny-Q5": {
        "path":    "granite-4.0-h-tiny-Q5_K_M.gguf",                     # 4.7 GB
        "mode":    "fim_qwen",
        "stop":    ["<|endoftext|>"],
    },
    "Granite-4.0-H-Tiny-Q6": {
        "path":    "granite-4.0-h-tiny-Q6_K.gguf",                       # 5.4 GB
        "mode":    "fim_qwen",
        "stop":    ["<|endoftext|>"],
    },
    "Granite-4.1-8B": {
        "path":    "granite-4.1-8b.Q4_K_M.gguf",                         # 5.0 GB
        "mode":    "fim_qwen",
        "stop":    ["<|endoftext|>"],
    },

    # ── 8-9B TIER — Llama/Gemma instruct (generic FIM via instruction) ────────

    "Qwen3.5-9B-Sushi-Coder": {
        "path":    "Qwen3.5-9b-Sushi-Coder-RL.Q4_K_M.gguf",              # 5.3 GB
        "mode":    "fim_qwen",
        "stop":    ["<|file_separator|>", "<|im_end|>", "<|endoftext|>"],
    },
    "Yi-9B-Coder": {
        "path":    "Yi-9B-Coder.i1-Q4_K_M.gguf",                         # 5.0 GB
        "mode":    "fim_qwen",
        "stop":    ["<|endoftext|>", "<|im_end|>"],
    },
    "Gemma-4-E4B": {
        "path":    "gemma-4-E4b-it.Q4_K_M.gguf",                         # 5.0 GB
        "mode":    "generic",
        "stop":    ["<eos>", "<end_of_turn>"],
    },
    "Athena-Llama-Coder-8B": {
        "path":    "Athena-llama-Coder-3-8B.Q5_K_M.gguf",                # 5.4 GB
        "mode":    "generic",
        "stop":    ["<|eot_id|>"],
    },
    "Replete-Coder-Llama3-8B": {
        "path":    "Replete-Coder-Llama3-8B.Q5_K_M.gguf",                # 5.4 GB
        "mode":    "generic",
        "stop":    ["<|eot_id|>"],
    },
}

# All models share these server settings — context kept low for latency
MODEL_DEFAULTS = {
    "context":    4096,
    "gpu_layers": 999,     # Full CUDA offload — all models fit in 7698 MiB
    "backend":    "cuda",
}


# ==============================================================================
# PROMPTS — 12 realistic VS Code autocomplete scenarios
# Covers: Python functions, mid-logic, imports, context awareness,
#         error handling, class bodies, decorators, R code, LaTeX, SQL
# ==============================================================================
prompts = [
    {
        "id":     "PY1_Function_Body",
        "desc":   "Complete function body from signature + docstring",
        "prefix": '''def calculate_hedonic_price_index(prices, features, weights):
    """
    Calculate a weighted hedonic price index for residential properties.

    Args:
        prices:   list of sale prices (float)
        features: list of feature vectors [sqft, beds, baths, dist_golf]
        weights:  regression coefficients for each feature

    Returns:
        float: composite weighted price index
    """
    ''',
        "suffix": "",
        "expect": ["return", "sum", "zip", "weight", "for"],
    },
    {
        "id":     "PY2_Mid_Function_Logic",
        "desc":   "Complete missing spatial join logic mid-function",
        "prefix": '''def filter_golf_courses_by_msa(gdf, msa_shapefile):
    import geopandas as gpd
    msa = gpd.read_file(msa_shapefile)
    msa = msa.to_crs(gdf.crs)
    ''',
        "suffix": "\n    return filtered\n",
        "expect": ["sjoin", "within", "clip", "intersects", "overlay"],
    },
    {
        "id":     "PY3_Import_Completion",
        "desc":   "Complete a partial sklearn import",
        "prefix": "from sklearn.linear_model import ",
        "suffix": "",
        "expect": ["LinearRegression", "Ridge", "Lasso", "ElasticNet"],
    },
    {
        "id":     "PY4_Context_Variable_Awareness",
        "desc":   "Use variables defined earlier in scope",
        "prefix": '''import pandas as pd
import numpy as np

hpi_data = pd.read_csv("fhfa_hpi_2024.csv")
hpi_data["date"] = pd.to_datetime(hpi_data["date"])
appreciation_rates = hpi_data.groupby("msa_code")["hpi"].apply(
    lambda x: (x.iloc[-1] / x.iloc[0]) ** (1 / len(x)) - 1
)
parcel_acres = 150
current_land_value_per_acre = 2_500_000

# Calculate annual opportunity cost
''',
        "suffix": "",
        "expect": ["appreciation_rates", "parcel_acres", "current_land_value", "opportunity"],
    },
    {
        "id":     "PY5_Error_Handler",
        "desc":   "Complete a try/except block",
        "prefix": '''def load_tiger_shapefile(filepath):
    try:
        import geopandas as gpd
        gdf = gpd.read_file(filepath)
        return gdf
    ''',
        "suffix": "",
        "expect": ["except", "FileNotFoundError", "raise", "return None"],
    },
    {
        "id":     "PY6_Class_Body",
        "desc":   "Complete a class __init__ body",
        "prefix": '''class HedonicModel:
    """Spatial hedonic pricing model for golf course amenity valuation."""

    def __init__(self, data, spatial_weights):
        ''',
        "suffix": "\n    def fit(self):\n        pass\n",
        "expect": ["self.data", "self.spatial_weights", "self.results", "self.model"],
    },
    {
        "id":     "PY7_Decorator",
        "desc":   "Complete a timing decorator wrapper body",
        "prefix": '''from functools import wraps
import time, logging

def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ''',
        "suffix": "\n    return wrapper\n",
        "expect": ["time", "logging", "result", "return", "start"],
    },
    {
        "id":     "PY8_List_Comprehension",
        "desc":   "Complete a filtered list comprehension",
        "prefix": '''# Filter MSAs where golf course density exceeds threshold
# msa_data: list of dicts with keys: msa_code, total_acres, golf_acres, pop
high_density_msas = [
    ''',
        "suffix": "\n]\n",
        "expect": ["msa", "golf_acres", "total_acres", "for", "if"],
    },
    {
        "id":     "R1_Spatial_Weights",
        "desc":   "Complete R spatial weights matrix construction",
        "prefix": '''library(spdep)
library(sf)
golf_sf <- st_read("golf_courses.geojson")
coords <- st_coordinates(st_centroid(golf_sf))
# Create k-nearest-neighbor spatial weights (k=5)
''',
        "suffix": "",
        "expect": ["nb2listw", "knearneigh", "knn2nb", "listw", "style"],
    },
    {
        "id":     "R2_Regression",
        "desc":   "Complete R hedonic regression with robust SE",
        "prefix": '''library(sandwich)
model <- lm(log(sale_price) ~ sqft + beds + baths + age + dist_golf,
            data = housing_data)
robust_se <- ''',
        "suffix": "",
        "expect": ["vcovHC", "coeftest", "sandwich", "HC3", "sqrt"],
    },
    {
        "id":     "TEX1_Equation",
        "desc":   "Complete a LaTeX hedonic pricing equation",
        "prefix": r'''\begin{equation}
    \ln(P_{it}) = \alpha_i + \beta_1 \text{dist\_golf}_{it} + \beta_2 X_{it} + ''',
        "suffix": r"\end{equation}",
        "expect": ["gamma", "epsilon", "mu", "delta", "lambda"],
    },
    {
        "id":     "SQL1_Query",
        "desc":   "Complete a spatial SQL query",
        "prefix": '''SELECT
    m.msa_code,
    m.msa_name,
    COUNT(g.parcel_id) as golf_course_count,
    SUM(g.total_acres) as total_golf_acres,
    ''',
        "suffix": "\nFROM msa_boundaries m\n",
        "expect": ["AVG", "SUM", "JOIN", "WHERE", "land_value", "GROUP BY"],
    },
]


# ==============================================================================
# OUTPUT — single timestamped mono markdown file
# ==============================================================================
timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = os.path.join(REPORT_DIR, f"autocomplete_bench_{timestamp}.md")


# ==============================================================================
# STATISTICS HELPERS
# ==============================================================================

def mean(values):
    return sum(values) / len(values) if values else 0.0

def stddev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))

def percentile(values, pct):
    if not values:
        return 0.0
    s = sorted(values)
    idx = (pct / 100) * (len(s) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] * (1 - (idx - lo)) + s[hi] * (idx - lo)

def cv_pct(values):
    m = mean(values)
    return (stddev(values) / m * 100) if m else 0.0


# ==============================================================================
# SERVER MANAGEMENT
# ==============================================================================

def flush_memory():
    try:
        subprocess.run(["sync"], check=False, timeout=10)
        subprocess.run(
            ["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"],
            check=False, timeout=10
        )
    except Exception as e:
        print(f"    [!] Memory flush warning (non-critical): {e}")

def wait_for_server(timeout_seconds):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=2)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def kill_stale_server():
    try:
        subprocess.run(
            ["pkill", "-f", f"llama-server.*--port.*{PORT}"],
            check=False, timeout=5
        )
        time.sleep(2)
    except Exception:
        pass


# ==============================================================================
# FIM PROMPT BUILDERS
# ==============================================================================

def build_fim_prompt(mode, prefix, suffix):
    if mode == "fim_qwen":
        if suffix:
            return f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"
        return f"<|fim_prefix|>{prefix}<|fim_suffix|><|fim_middle|>"

    if mode == "fim_codegemma":
        # CodeGemma base uses same tokens as Qwen but is a pure completion model
        # suffix token placement is at cursor position, not after
        if suffix:
            return f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"
        return f"<|fim_prefix|>{prefix}<|fim_suffix|><|fim_middle|>"

    if mode == "fim_starcoder":
        if suffix:
            return f"<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>"
        return f"<fim_prefix>{prefix}<fim_suffix><fim_middle>"

    if mode == "raw":
        return prefix

    if mode == "generic":
        block = (
            f"```\n{prefix}\n# [CURSOR]\n{suffix}\n```"
            if suffix else
            f"```\n{prefix}\n# [CURSOR]\n```"
        )
        return (
            "### Instruction:\n"
            "Complete the code at [CURSOR]. Output ONLY the missing code. "
            "No explanation. No markdown fences.\n\n"
            f"{block}\n\n### Response:\n"
        )

    raise ValueError(f"Unknown FIM mode: {mode}")


# ==============================================================================
# COMPLETION RUNNERS
# ==============================================================================

def run_raw_completion(mode, stop_tokens, prompt_text):
    payload = {
        "prompt":       prompt_text,
        "n_predict":    MAX_TOKENS,
        "temperature":  TEMPERATURE,
        "stop":         stop_tokens,
        "stream":       False,
        "cache_prompt": True,
    }
    start = time.time()
    try:
        res = requests.post(
            f"http://127.0.0.1:{PORT}/completion",
            json=payload,
            timeout=INFER_TIMEOUT
        )
        total_ms = (time.time() - start) * 1000
        if res.status_code != 200:
            return None, f"HTTP {res.status_code}"
        data    = res.json()
        timings = data.get("timings", {})
        return {
            "text":       data.get("content", "").strip(),
            "ttft_ms":    timings.get("prompt_ms", total_ms),
            "gen_ms":     timings.get("predicted_ms", 0),
            "tps":        timings.get("predicted_per_second", 0),
            "tokens_out": data.get("tokens_predicted", 0),
            "tokens_in":  data.get("tokens_evaluated", 0),
            "total_ms":   total_ms,
        }, None
    except requests.exceptions.Timeout:
        return None, f"TIMEOUT after {INFER_TIMEOUT}s"
    except Exception as e:
        return None, str(e)


def run_chat_completion(stop_tokens, prompt_text):
    payload = {
        "messages":    [{"role": "user", "content": prompt_text}],
        "temperature": TEMPERATURE,
        "max_tokens":  MAX_TOKENS,
        "stop":        stop_tokens,
        "stream":      False,
    }
    start = time.time()
    try:
        res = requests.post(
            f"http://127.0.0.1:{PORT}/v1/chat/completions",
            json=payload,
            timeout=INFER_TIMEOUT
        )
        total_ms = (time.time() - start) * 1000
        if res.status_code != 200:
            return None, f"HTTP {res.status_code}"
        data    = res.json()
        tok_out = data["usage"]["completion_tokens"]
        tok_in  = data["usage"]["prompt_tokens"]
        gen_ms  = total_ms * 0.75
        return {
            "text":       data["choices"][0]["message"]["content"].strip(),
            "ttft_ms":    total_ms * 0.25,
            "gen_ms":     gen_ms,
            "tps":        (tok_out / (gen_ms / 1000.0)) if gen_ms > 0 else 0,
            "tokens_out": tok_out,
            "tokens_in":  tok_in,
            "total_ms":   total_ms,
        }, None
    except requests.exceptions.Timeout:
        return None, f"TIMEOUT after {INFER_TIMEOUT}s"
    except Exception as e:
        return None, str(e)


def run_completion(model_cfg, prefix, suffix):
    mode   = model_cfg["mode"]
    stop   = model_cfg["stop"]
    prompt = build_fim_prompt(mode, prefix, suffix)
    if mode == "generic":
        return run_chat_completion(stop, prompt)
    return run_raw_completion(mode, stop, prompt)


# ==============================================================================
# ACCURACY CHECK — loose keyword signal
# ==============================================================================

def check_accuracy(text, expected):
    low = text.lower()
    matched = [kw for kw in expected if kw.lower() in low]
    return len(matched), len(expected), matched


# ==============================================================================
# PREFLIGHT CHECKS
# ==============================================================================

for label, binary in [("CUDA", CUDA_BIN), ("ROCm", ROCM_BIN)]:
    if not os.path.isfile(binary):
        print(f"[FATAL] {label} binary not found: {binary}")
        sys.exit(1)

missing_models = []
for alias, cfg in models.items():
    path = os.path.join(MODEL_DIR, cfg["path"])
    if not os.path.isfile(path):
        missing_models.append(f"  {alias}: {cfg['path']}")

if missing_models:
    print("[WARNING] The following model files were not found and will be skipped:")
    for m in missing_models:
        print(m)
    print()


# ==============================================================================
# REPORT INITIALISATION — written once at start, appended throughout
# ==============================================================================

total_inferences = len(models) * len(prompts) * (WARMUP_RUNS + RUNS_PER_PROMPT)

os.makedirs(REPORT_DIR, exist_ok=True)
with open(report_file, "w") as f:
    f.write("# FishTex Autocomplete Benchmark (v6)\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
    f.write("**System:** AMD Ryzen AI Max+ 395 | 128GB LPDDR5 @ 8000MHz | Fedora 43 Server  \n")
    f.write("**GPU:** NVIDIA RTX 3060 Ti 8GB (CUDA 13.2 | sm_86 | build 8940) via TB4  \n")
    f.write("**ROCm:** 6.4.0 | gfx1151 | build 8850 (research fleet, not used here)  \n\n")
    f.write("| Config | Value |\n|--------|-------|\n")
    f.write(f"| Total models | {len(models)} |\n")
    f.write(f"| Total prompts | {len(prompts)} |\n")
    f.write(f"| Warmup runs (discarded) | {WARMUP_RUNS} per prompt |\n")
    f.write(f"| Timed runs | {RUNS_PER_PROMPT} per prompt |\n")
    f.write(f"| Total inferences | ~{total_inferences} |\n")
    f.write(f"| Max tokens per completion | {MAX_TOKENS} |\n")
    f.write(f"| Temperature | {TEMPERATURE} |\n")
    f.write(f"| Context window | 4096 tokens |\n")
    f.write(f"| Bench port | {PORT} |\n\n")
    f.write("### Metrics\n\n")
    f.write("| Metric | Meaning |\n|--------|---------|\n")
    f.write("| **TTFT** | Prompt eval time in ms — lower = better autocomplete feel |\n")
    f.write("| **t/s** | Generation tokens per second — higher = faster completion |\n")
    f.write("| **p50/p90/p95** | TTFT latency percentiles across timed runs |\n")
    f.write("| **CV%** | Coefficient of variation (stddev/mean %) — lower = more consistent |\n")
    f.write("| **Cold** | First timed run (empty KV cache) |\n")
    f.write("| **Warm** | Average of runs 2+ (primed KV cache) |\n")
    f.write("| **Accuracy** | Keyword match signal — not a hard pass/fail |\n\n")
    f.write("---\n\n")
    f.write("## Model Results\n\n")

print(f"\n{'='*60}")
print(f"  FishTex Autocomplete Benchmark v6")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"  {len(models)} models | {len(prompts)} prompts | "
      f"{WARMUP_RUNS}+{RUNS_PER_PROMPT} runs each")
print(f"  ~{total_inferences} total inferences")
print(f"  Report: {report_file}")
print(f"{'='*60}")


# ==============================================================================
# SUMMARY ACCUMULATOR
# ==============================================================================
summary = []


# ==============================================================================
# MAIN LOOP
# Server boots once per model, stays up for ALL prompts, then terminates.
# Script exits cleanly at the end — no shutdown, no reboot.
# ==============================================================================
for model_alias, model_cfg in models.items():

    model_path   = os.path.join(MODEL_DIR, model_cfg["path"])
    context      = MODEL_DEFAULTS["context"]
    gpu_layers   = MODEL_DEFAULTS["gpu_layers"]
    binary       = CUDA_BIN   # All 19 models route to CUDA

    print(f"\n{'='*60}")
    print(f"[+] {model_alias}")
    print(f"    {model_cfg['path']}  [{model_cfg['mode']}]")
    print(f"{'='*60}")

    if not os.path.isfile(model_path):
        print(f"[-] File not found — skipping")
        with open(report_file, "a") as f:
            f.write(f"### {model_alias}\n\n")
            f.write(f"**SKIPPED** — file not found: `{model_path}`\n\n---\n\n")
        continue

    file_size_gb   = os.path.getsize(model_path) / (1024 ** 3)
    kill_stale_server()
    server_process = None
    model_prompt_stats = []

    try:
        env = os.environ.copy()

        cmd = [
            binary,
            "-m",            model_path,
            "--alias",       model_alias,
            "-c",            str(context),
            "-t",            str(THREADS),
            "-ngl",          str(gpu_layers),
            "--parallel",    "1",
            "--flash-attn",  "on",
            "--ubatch-size", str(UBATCH),
            "--batch-size",  str(BATCH),
            "-ctk",          "q8_0",
            "-ctv",          "q8_0",
            "--cache-ram",   "-1",
            "--no-mmap",
            "--host",        "0.0.0.0",
            "--port",        str(PORT),
        ]

        error_log = os.path.join(
            REPORT_DIR,
            f"ac_err_{model_alias.replace(' ', '_')}_{timestamp}.log"
        )

        with open(error_log, "w") as err_out:
            server_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=err_out, env=env
            )

        print(f"    Booting ({file_size_gb:.2f} GB) — waiting up to {BOOT_TIMEOUT}s...")
        if not wait_for_server(BOOT_TIMEOUT):
            print(f"[-] Server failed to start — see: {error_log}")
            with open(report_file, "a") as f:
                f.write(f"### {model_alias}\n\n")
                f.write(f"**FAILED TO START** within {BOOT_TIMEOUT}s.  \n")
                f.write(f"Error log: `{error_log}`\n\n---\n\n")
            continue

        print(f"    Server ready. "
              f"{WARMUP_RUNS} warmup + {RUNS_PER_PROMPT} timed × {len(prompts)} prompts\n")

        # Write model header to report
        with open(report_file, "a") as f:
            f.write(f"### {model_alias}\n\n")
            f.write(f"| | |\n|---|---|\n")
            f.write(f"| File | `{model_cfg['path']}` |\n")
            f.write(f"| Size | {file_size_gb:.2f} GB |\n")
            f.write(f"| FIM mode | `{model_cfg['mode']}` |\n\n")

        model_start = time.time()

        # ── PROMPT LOOP ────────────────────────────────────────────────────────
        for p in prompts:
            print(f"    ── {p['id']}")

            # Warmup — prime KV cache, results discarded
            for w in range(WARMUP_RUNS):
                result, err = run_completion(model_cfg, p["prefix"], p["suffix"])
                status = f"{result['tps']:.0f} t/s" if result else f"ERR: {err}"
                print(f"       warmup {w+1}: {status} [discarded]")
                time.sleep(0.3)

            # Timed runs
            timed, errors = [], []
            for run_num in range(1, RUNS_PER_PROMPT + 1):
                result, err = run_completion(model_cfg, p["prefix"], p["suffix"])
                if result:
                    timed.append(result)
                    tag = "cold" if run_num == 1 else "warm"
                    print(f"       run {run_num:02d} [{tag}]: "
                          f"{result['tps']:.1f} t/s | "
                          f"TTFT {result['ttft_ms']:.0f}ms | "
                          f"{result['tokens_out']} tok")
                else:
                    errors.append(err)
                    print(f"       run {run_num:02d}: ERROR — {err}")
                time.sleep(0.3)

            if not timed:
                with open(report_file, "a") as f:
                    f.write(f"#### {p['id']} — {p['desc']}\n\n")
                    f.write(f"**ALL RUNS FAILED:** {'; '.join(errors)}\n\n")
                continue

            # Statistics
            ttft_vals  = [r["ttft_ms"]    for r in timed]
            tps_vals   = [r["tps"]        for r in timed]
            total_vals = [r["total_ms"]   for r in timed]
            tok_vals   = [r["tokens_out"] for r in timed]

            cold_ttft  = ttft_vals[0]
            warm_ttft  = mean(ttft_vals[1:]) if len(ttft_vals) > 1 else ttft_vals[0]

            s = {
                "ttft_mean":  mean(ttft_vals),
                "ttft_min":   min(ttft_vals),
                "ttft_max":   max(ttft_vals),
                "ttft_sd":    stddev(ttft_vals),
                "ttft_p50":   percentile(ttft_vals, 50),
                "ttft_p90":   percentile(ttft_vals, 90),
                "ttft_p95":   percentile(ttft_vals, 95),
                "ttft_cv":    cv_pct(ttft_vals),
                "ttft_cold":  cold_ttft,
                "ttft_warm":  warm_ttft,
                "tps_mean":   mean(tps_vals),
                "tps_min":    min(tps_vals),
                "tps_max":    max(tps_vals),
                "total_mean": mean(total_vals),
                "tok_mean":   mean(tok_vals),
                "runs_ok":    len(timed),
            }

            last_text = timed[-1]["text"]
            matched, total_kw, matched_kws = check_accuracy(last_text, p["expect"])
            acc_pct = (matched / total_kw * 100) if total_kw else 0

            print(f"       avg {s['tps_mean']:.1f} t/s | "
                  f"TTFT p50={s['ttft_p50']:.0f}ms p90={s['ttft_p90']:.0f}ms | "
                  f"CV={s['ttft_cv']:.1f}% | acc {matched}/{total_kw}")

            model_prompt_stats.append({
                "id":       p["id"],
                "ttft":     s["ttft_mean"],
                "tps":      s["tps_mean"],
                "acc":      acc_pct,
                "cv":       s["ttft_cv"],
                "p90":      s["ttft_p90"],
            })

            # Write prompt section to report
            with open(report_file, "a") as f:
                f.write(f"#### {p['id']} — {p['desc']}\n\n")

                f.write("**Timing (ms)**\n\n")
                f.write("| Metric | TTFT |\n|--------|------|\n")
                f.write(f"| Mean | {s['ttft_mean']:.0f} |\n")
                f.write(f"| Min | {s['ttft_min']:.0f} |\n")
                f.write(f"| Max | {s['ttft_max']:.0f} |\n")
                f.write(f"| Std Dev | {s['ttft_sd']:.0f} |\n")
                f.write(f"| p50 | {s['ttft_p50']:.0f} |\n")
                f.write(f"| p90 | {s['ttft_p90']:.0f} |\n")
                f.write(f"| p95 | {s['ttft_p95']:.0f} |\n")
                f.write(f"| CV% | {s['ttft_cv']:.1f}% |\n\n")

                f.write("**Cold vs Warm Cache**\n\n")
                f.write("| | TTFT (ms) |\n|---|---|\n")
                f.write(f"| Cold (run 1) | {s['ttft_cold']:.0f} |\n")
                f.write(f"| Warm avg (runs 2+) | {s['ttft_warm']:.0f} |\n")
                delta = s["ttft_cold"] - s["ttft_warm"]
                f.write(f"| Cache benefit | {delta:+.0f} ms |\n\n")

                f.write("**Generation**\n\n")
                f.write(f"| Metric | Value |\n|--------|-------|\n")
                f.write(f"| Avg t/s | {s['tps_mean']:.1f} |\n")
                f.write(f"| Min t/s | {s['tps_min']:.1f} |\n")
                f.write(f"| Max t/s | {s['tps_max']:.1f} |\n")
                f.write(f"| Avg tokens out | {s['tok_mean']:.0f} |\n")
                f.write(f"| Successful runs | {s['runs_ok']}/{RUNS_PER_PROMPT} |\n\n")

                f.write(f"**Accuracy:** {matched}/{total_kw} ({acc_pct:.0f}%)")
                if matched_kws:
                    f.write(f" — matched: `{'`, `'.join(matched_kws)}`")
                f.write("\n\n")

                f.write(f"**Completion (last run):**\n\n```\n{last_text}\n```\n\n")

        # Model summary row
        elapsed = time.time() - model_start
        if model_prompt_stats:
            summary.append({
                "alias":    model_alias,
                "path":     model_cfg["path"],
                "size_gb":  file_size_gb,
                "mode":     model_cfg["mode"],
                "ttft":     mean([x["ttft"] for x in model_prompt_stats]),
                "tps":      mean([x["tps"]  for x in model_prompt_stats]),
                "acc":      mean([x["acc"]  for x in model_prompt_stats]),
                "cv":       mean([x["cv"]   for x in model_prompt_stats]),
                "p90":      mean([x["p90"]  for x in model_prompt_stats]),
            })

        with open(report_file, "a") as f:
            f.write(f"**Model total time:** {elapsed/60:.1f} min\n\n---\n\n")

    except Exception as e:
        print(f"[-] Unexpected error for {model_alias}: {e}")
        with open(report_file, "a") as f:
            f.write(f"### {model_alias}\n\n**FATAL ERROR:** {e}\n\n---\n\n")

    finally:
        if server_process is not None:
            print(f"    Terminating server for {model_alias}...")
            server_process.terminate()
            try:
                server_process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
            flush_memory()
            print(f"    Cooling down {COOLDOWN}s...")
            time.sleep(COOLDOWN)


# ==============================================================================
# FINAL SUMMARY TABLES — appended at end of same report file
# ==============================================================================
with open(report_file, "a") as f:
    f.write("---\n\n")
    f.write("## Final Summary\n\n")
    f.write(f"*{len(models)} models | {len(prompts)} prompts | "
            f"{RUNS_PER_PROMPT} timed runs each (+{WARMUP_RUNS} warmup discarded)*\n\n")
    f.write(f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    if summary:
        # Table 1 — ranked by TTFT (primary autocomplete metric)
        by_ttft = sorted(summary, key=lambda x: x["ttft"])
        f.write("### Ranked by Avg TTFT — *lower = better ghost text feel*\n\n")
        f.write("| Rank | Model | Size | FIM Mode | Avg TTFT | p90 TTFT | "
                "Avg t/s | CV% | Accuracy |\n")
        f.write("|------|-------|------|----------|----------|----------|"
                "---------|-----|----------|\n")
        for i, r in enumerate(by_ttft, 1):
            f.write(f"| {i} | **{r['alias']}** | {r['size_gb']:.2f} GB | "
                    f"`{r['mode']}` | {r['ttft']:.0f} ms | {r['p90']:.0f} ms | "
                    f"{r['tps']:.1f} | {r['cv']:.1f}% | {r['acc']:.0f}% |\n")

        f.write("\n")

        # Table 2 — ranked by t/s (generation throughput)
        by_tps = sorted(summary, key=lambda x: x["tps"], reverse=True)
        f.write("### Ranked by Avg t/s — *higher = faster generation*\n\n")
        f.write("| Rank | Model | Avg t/s | Avg TTFT | CV% | Accuracy |\n")
        f.write("|------|-------|---------|----------|-----|----------|\n")
        for i, r in enumerate(by_tps, 1):
            f.write(f"| {i} | **{r['alias']}** | {r['tps']:.1f} | "
                    f"{r['ttft']:.0f} ms | {r['cv']:.1f}% | {r['acc']:.0f}% |\n")

        f.write("\n")

        # Table 3 — ranked by consistency (CV%)
        by_cv = sorted(summary, key=lambda x: x["cv"])
        f.write("### Ranked by Consistency (CV%) — *lower = more reliable*\n\n")
        f.write("| Rank | Model | CV% | Avg TTFT | Avg t/s | Accuracy |\n")
        f.write("|------|-------|-----|----------|---------|----------|\n")
        for i, r in enumerate(by_cv, 1):
            f.write(f"| {i} | **{r['alias']}** | {r['cv']:.1f}% | "
                    f"{r['ttft']:.0f} ms | {r['tps']:.1f} | {r['acc']:.0f}% |\n")

    else:
        f.write("*No models completed successfully.*\n")

print(f"\n{'='*60}")
print(f"  [DONE] Benchmark complete.")
print(f"  Report: {report_file}")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# Script exits here — no shutdown, no reboot, no sleep.
# sys.exit(0) is implicit — Python exits cleanly.