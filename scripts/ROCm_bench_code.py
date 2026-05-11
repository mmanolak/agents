import subprocess
import time
import requests
import os
import sys
import glob
from datetime import datetime

# ==============================================================================
# FishTex Code Benchmark — bench_code_ROCm.py
# System: AMD Ryzen AI Max+ 395 (Strix Halo) | 128GB LPDDR5 | Fedora 43 Server
# Engine: ROCm — ~/llama.cpp/build/bin/llama-server
#
# YaRN fix (mscale_all_dim 1→0) confirmed baked into recompiled ROCm binary.
# HIP_VISIBLE_DEVICES and HSA_OVERRIDE_GFX_VERSION set system-wide via
# /etc/profile.d/rocm-env.sh — not set inline here.
#
# KV Cache Strategy — LIGHTWEIGHT:
#   -ctk and -ctv flags REMOVED ENTIRELY from this script.
#   Small coding models have short context windows. Uncompressed F16 KV
#   eliminates compute overhead and minimises Time-To-First-Token (TTFT).
#   128GB RAM — no need to compress.
#
# Batch Strategy — LIGHTWEIGHT:
#   --ubatch-size 1024 --batch-size 2048
#   Smaller batches appropriate for short coding prompt context windows.
# ==============================================================================

TESTING_DIR = "/mnt/ai_vault/testing"

models = {
    "Kimi-Linear-48B-Q6_K": {
        "path":       f"{TESTING_DIR}/moonshotai_Kimi-Linear-48B-A3B-Instruct-Q6_K.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
    "Kimi-Linear-48B-Q6_K_L": {
        "path":       f"{TESTING_DIR}/moonshotai_Kimi-Linear-48B-A3B-Instruct-Q6_K_L.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
    "Kimi-Linear-48B-Q8_0": {
        "path":       f"{TESTING_DIR}/moonshotai_Kimi-Linear-48B-A3B-Instruct-Q8_0-00001-of-00002.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
    "Llama4-Scout-UD-Q5_K_XL": {
        "path":       f"{TESTING_DIR}/Llama-4-Scout-17B-16E-Instruct-UD-Q5_K_XL-00001-of-00002.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
    "Llama4-Scout-Q6_K": {
        "path":       f"{TESTING_DIR}/Llama-4-Scout-17B-16E-Instruct-Q6_K-00001-of-00002.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
    "Llama4-Scout-UD-Q6_K_XL": {
        "path":       f"{TESTING_DIR}/Llama-4-Scout-17B-16E-Instruct-UD-Q6_K_XL-00001-of-00002.gguf",
        "context":    32768,
        "gpu_layers": 999,
    },
}


# ------------------------------------------------------------------------------
# HARDWARE CONFIG — Lightweight strategy
# ------------------------------------------------------------------------------
LLAMA_BIN     = os.path.expanduser("~/llama.cpp/build/bin/llama-server")
THREADS       = 16
UBATCH        = 1024
BATCH         = 2048
PORT          = 8080
BOOT_TIMEOUT  = 420
INFER_TIMEOUT = 300
COOLDOWN      = 15


# ------------------------------------------------------------------------------
# REPORT FILE — single flat MD, timestamped, never overwrites
# ------------------------------------------------------------------------------
timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = f"bench_code_ROCm_{timestamp}.md"


# ------------------------------------------------------------------------------
# CODING PROMPTS
# ------------------------------------------------------------------------------
prompts = [
    {
        "id":   "R_1_Spatial_Join",
        "text": (
            "Write an R script using the 'sf' and 'dplyr' packages to load two shapefiles: "
            "'properties.shp' and 'golf_courses.shp'. Perform a spatial join to calculate "
            "the exact distance from every property to the nearest golf course boundary. "
            "Add this distance as a new column called 'dist_to_golf_m' and return the "
            "updated dataframe."
        ),
    },
    {
        "id":   "Py_2_Hedonic_Regression",
        "text": (
            "Write a Python script using 'statsmodels' to perform a hedonic pricing "
            "regression. Load 'data.csv', define 'log_price' as the dependent variable, "
            "and use 'bedrooms', 'bathrooms', 'sqft', and 'dist_to_golf' as independent "
            "variables. Include a constant term and print the summary statistics."
        ),
    },
    {
        "id":   "Ju_3_Optimization",
        "text": (
            "Write a Julia script using the 'JuMP.jl' and 'Ipopt.jl' packages to solve "
            "a simple optimization problem. Maximize the objective function f(x, y) = 3x + 4y "
            "subject to the constraints: x + 2y <= 14, 3x - y >= 0, and x, y >= 0."
        ),
    },
]


# ------------------------------------------------------------------------------
# MEMORY FLUSH
# ------------------------------------------------------------------------------
def flush_memory():
    try:
        subprocess.run(["sync"], check=False, timeout=10)
        subprocess.run(
            ["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"],
            check=False, timeout=10
        )
    except Exception as e:
        print(f"    [!] Memory flush failed (non-critical): {e}")


# ------------------------------------------------------------------------------
# SERVER HEALTH POLL
# ------------------------------------------------------------------------------
def wait_for_server(timeout_seconds):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=2)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


# ------------------------------------------------------------------------------
# VERIFY BINARY
# ------------------------------------------------------------------------------
if not os.path.isfile(LLAMA_BIN):
    print(f"[FATAL] llama-server binary not found at: {LLAMA_BIN}")
    sys.exit(1)


# ------------------------------------------------------------------------------
# REPORT HEADER
# ------------------------------------------------------------------------------
with open(report_file, "w") as f:
    f.write("# FishTex Code Benchmark — ROCm\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("**System:** AMD Ryzen AI Max+ 395 | 128GB LPDDR5 @ 8000MHz | Fedora 43 Server\n")
    f.write("**Engine:** ROCm — `~/llama.cpp/build/bin/llama-server`\n")
    f.write("**KV Cache:** F16 uncompressed (lightweight — `-ctk`/`-ctv` removed)\n")
    f.write("**Batch:** `--ubatch-size 1024 --batch-size 2048`\n")
    f.write(f"**Models queued:** {len(models)}\n\n---\n\n")

print(f"\n{'='*60}")
print(f"  FishTex Code Benchmark — ROCm")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"  Engine: ROCm | KV: F16 uncompressed | Models: {len(models)}")
print(f"  Report: {report_file}")
print(f"{'='*60}")


# ------------------------------------------------------------------------------
# MAIN BENCHMARK LOOP
# ------------------------------------------------------------------------------
for model_alias, model_cfg in models.items():
    model_path = model_cfg["path"]
    context    = model_cfg["context"]
    gpu_layers = model_cfg["gpu_layers"]

    print(f"\n{'='*60}")
    print(f"[+] Model: {model_alias}")
    print(f"    Path:    {model_path}")
    print(f"    Context: {context} | GPU Layers: {gpu_layers}")
    print(f"{'='*60}")

    if os.path.isfile(model_path):
        actual_path = model_path
    else:
        parent_dir = os.path.dirname(model_path)
        candidates = sorted(glob.glob(os.path.join(parent_dir, "*.gguf")))
        if not candidates:
            print(f"[-] No .gguf files found in {parent_dir} — skipping.")
            with open(report_file, "a") as f:
                f.write(f"## Model: {model_alias}\n\n")
                f.write(f"**SKIPPED** — file not found at `{model_path}`\n\n---\n\n")
            continue
        actual_path = candidates[0]
        print(f"    [i] Using resolved path: {actual_path}")

    server_process = None
    prompts_run    = 0
    tps_list       = []

    try:
        env = os.environ.copy()

        cmd = [
            LLAMA_BIN,
            "-m",            actual_path,
            "--alias",       model_alias,
            "-c",            str(context),
            "-t",            str(THREADS),
            "-ngl",          str(gpu_layers),
            "--parallel",    "1",
            "--flash-attn",  "on",
            "--ubatch-size", str(UBATCH),
            "--batch-size",  str(BATCH),
            "--repeat-penalty", "1.1",
            "--min-p",       "0.05",
            # NOTE: -ctk and -ctv intentionally omitted — lightweight strategy.
            # F16 uncompressed KV eliminates compute overhead for short contexts.
            # Also required for Kimi-Linear: n_embd_head_v=72 incompatible with q8_0.
            "--host",        "0.0.0.0",
            "--port",        str(PORT),
        ]

        if gpu_layers != 999:
            cmd.append("--mmap")
        else:
            cmd.append("--no-mmap")

        model_error_log = f"error_rocm_{model_alias.replace(' ', '_')}_{timestamp}.log"

        with open(model_error_log, "w") as err_out:
            server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=err_out,
                env=env
            )

        print(f"    Waiting up to {BOOT_TIMEOUT}s for server ready...")
        if not wait_for_server(BOOT_TIMEOUT):
            print(f"[-] Server failed to start within {BOOT_TIMEOUT}s. Check {model_error_log}")
            with open(report_file, "a") as f:
                f.write(f"## Model: {model_alias}\n\n")
                f.write(f"**FAILED** — server did not start within {BOOT_TIMEOUT}s.\n")
                f.write(f"See error log: `{model_error_log}`\n\n---\n\n")
            continue

        print("    Server online. Starting benchmark...\n")

        with open(report_file, "a") as f:
            f.write(f"## Model: {model_alias}\n\n")
            f.write(f"- **Context:** {context}\n")
            f.write(f"- **GPU Layers:** {gpu_layers}\n")
            f.write(f"- **Engine:** ROCm\n")
            f.write(f"- **Started:** {datetime.now().strftime('%H:%M:%S')}\n\n")

        model_start = time.time()

        for idx, p in enumerate(prompts):
            print(f"    -> {p['id']} ({idx + 1}/{len(prompts)})...")
            start_time = time.time()

            try:
                res = requests.post(
                    f"http://127.0.0.1:{PORT}/v1/chat/completions",
                    json={
                        "messages":    [{"role": "user", "content": p["text"]}],
                        "temperature": 0.1,
                        "max_tokens":  2048,
                    },
                    timeout=INFER_TIMEOUT,
                )
                end_time = time.time()

                if res.status_code == 200:
                    data             = res.json()
                    response_text    = data["choices"][0]["message"]["content"]
                    tokens_generated = data["usage"]["completion_tokens"]
                    prompt_tokens    = data["usage"]["prompt_tokens"]
                    time_taken       = end_time - start_time
                    tps              = tokens_generated / time_taken if time_taken > 0 else 0

                    tps_list.append(tps)
                    prompts_run += 1
                    print(f"       Done — {tps:.2f} t/s  "
                          f"({tokens_generated} tokens out / {prompt_tokens} in, "
                          f"{time_taken:.1f}s)")

                    with open(report_file, "a") as f:
                        f.write(f"### {p['id']}\n")
                        f.write(f"| Metric | Value |\n|--------|-------|\n")
                        f.write(f"| Speed | {tps:.2f} t/s |\n")
                        f.write(f"| Output tokens | {tokens_generated} |\n")
                        f.write(f"| Input tokens | {prompt_tokens} |\n")
                        f.write(f"| Time | {time_taken:.2f}s |\n\n")
                        f.write(f"**Response:**\n\n{response_text}\n\n---\n\n")

                else:
                    print(f"       [-] HTTP {res.status_code}")
                    with open(report_file, "a") as f:
                        f.write(f"### {p['id']}\n")
                        f.write(f"**ERROR:** HTTP {res.status_code}\n\n---\n\n")

            except requests.exceptions.Timeout:
                elapsed = time.time() - start_time
                print(f"       [-] TIMEOUT after {elapsed:.0f}s on {p['id']}")
                with open(report_file, "a") as f:
                    f.write(f"### {p['id']}\n")
                    f.write(f"**ERROR:** Inference timed out after {INFER_TIMEOUT}s\n\n---\n\n")

            except requests.exceptions.RequestException as e:
                print(f"       [-] Request error on {p['id']}: {e}")
                with open(report_file, "a") as f:
                    f.write(f"### {p['id']}\n")
                    f.write(f"**ERROR:** {e}\n\n---\n\n")

        model_elapsed = time.time() - model_start
        avg_tps       = sum(tps_list) / len(tps_list) if tps_list else 0

        with open(report_file, "a") as f:
            f.write(f"**Total time for {model_alias}:** {model_elapsed:.1f}s\n")
            f.write(f"**Average speed:** {avg_tps:.2f} t/s\n\n---\n\n")

        print(f"\n    Model done in {model_elapsed:.1f}s — avg {avg_tps:.2f} t/s")

    except Exception as e:
        print(f"[-] Unexpected error for {model_alias}: {e}")
        with open(report_file, "a") as f:
            f.write(f"## Model: {model_alias}\n\n")
            f.write(f"**FATAL ERROR:** {e}\n\n---\n\n")

    finally:
        if server_process is not None:
            print("    Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                print("    terminate() timed out — sending SIGKILL")
                server_process.kill()
                server_process.wait()
            print("    Flushing memory...")
            flush_memory()
            print(f"    Cooling down {COOLDOWN}s before next model...")
            time.sleep(COOLDOWN)


# ------------------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"[+] Benchmark complete.")
print(f"    Report: {report_file}")
print(f"{'='*60}\n")

with open(report_file, "a") as f:
    f.write(f"## Run Complete\n\n")
    f.write(f"**Finished:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")