import subprocess
import time
import requests
import os
import sys
from datetime import datetime

# ==============================================================================
# FishTex General Benchmark — Vulkan_bench_general.py
# System: AMD Ryzen AI Max+ 395 (Strix Halo) | 128GB LPDDR5 | Fedora 43 Server
# Engine: Vulkan — ~/llama.cpp/build-vulkan/bin/llama-server
#
# Run this AFTER ROCm_bench_general.py has fully completed and cooled down.
# Do not run both simultaneously — port 8080 is shared.
#
# YaRN fix (mscale_all_dim 1→0) confirmed baked into recompiled Vulkan binary.
#
# DEVICE ROUTING:
#   Vulkan0 = NVIDIA GeForce RTX 3060 Ti (8GB) — discrete GPU, TB4
#   Vulkan1 = AMD Radeon 8060S / Strix Halo (128GB) — target device
#   All models use --device vulkan1 to force the correct device.
#
# KV Cache Strategy:
#   HEAVYWEIGHT models: -ctk q8_0 -ctv q8_0 RETAINED
#   KIMI-LINEAR models: -ctk and -ctv REMOVED — architecture incompatibility.
#     n_embd_head_v=72 does not divide by block size 32 for q8_0.
#     Attempting KV quantisation on Kimi-Linear causes a fatal init error.
#
# Batch Strategy — HEAVYWEIGHT:
#   --batch-size 4096 --ubatch-size 4096
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

# Models requiring special launch flags due to architecture constraints.
# Kimi-Linear: n_embd_head_v=72 is incompatible with q8_0 KV block size (32).
KIMI_LINEAR_MODELS = {
    "Kimi-Linear-48B-Q6_K",
    "Kimi-Linear-48B-Q6_K_L",
    "Kimi-Linear-48B-Q8_0",
}


# ------------------------------------------------------------------------------
# HARDWARE CONFIG
# ------------------------------------------------------------------------------
LLAMA_BIN     = os.path.expanduser("~/llama.cpp/build-vulkan/bin/llama-server")
THREADS       = 16
UBATCH        = 4096
BATCH         = 4096
PORT          = 8080
BOOT_TIMEOUT  = 480
INFER_TIMEOUT = 900
COOLDOWN      = 20


# ------------------------------------------------------------------------------
# REPORT & LOG FILES
# ------------------------------------------------------------------------------
timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = f"bench_general_Vulkan_{timestamp}.md"


# ------------------------------------------------------------------------------
# Q5 DOCUMENT — RAG extraction test
# ------------------------------------------------------------------------------
q5_doc_text = ""
if os.path.exists("q5_document.txt"):
    with open("q5_document.txt", "r", encoding="utf-8") as f:
        q5_doc_text = f.read()
else:
    q5_doc_text = "[DOCUMENT TEXT MISSING — create q5_document.txt with PDF text]"


# ------------------------------------------------------------------------------
# BENCHMARK PROMPTS — identical to ROCm script for clean comparison
# ------------------------------------------------------------------------------
prompts = [
    {
        "id":   "Q1_Hedonic_Pricing_Math",
        "text": (
            "Construct a formal hedonic pricing model to estimate the impact of proximity "
            "to a golf course on residential property values. Define the equation using a "
            "spatial fixed-effects approach, explicitly isolating the environmental amenity "
            "value from standard structural characteristics. Explain the assumptions behind "
            "the error term in this specific spatial context."
        ),
    },
    {
        "id":   "Q2_Highest_Best_Use",
        "text": (
            "Assume a 150-acre privately owned golf course is situated within a high-density "
            "urban MSA where residential land values are appreciating at 8% annually. Detail "
            "a step-by-step 'highest and best use' analysis to calculate the opportunity cost "
            "of maintaining the parcel as a golf course versus converting it to high-density "
            "residential zoning. What specific discount rate challenges arise in this valuation?"
        ),
    },
    {
        "id":   "Q3_Geospatial_Data",
        "text": (
            "Compare the methodological limitations of using OpenStreetMap (OSM) polygon data "
            "versus Census TIGER/Line shapefiles when calculating the exact acreage of "
            "recreational land at the county level. Furthermore, why would FHFA housing price "
            "indexes be insufficient on their own to determine the underlying raw land value "
            "of those parcels?"
        ),
    },
    {
        "id":   "Q4_Formatting_Constraints",
        "text": (
            "Write a theoretical abstract (exactly 100 words) about the opportunity cost of "
            "urban land. Immediately following the abstract, provide a LaTeX BibTeX citation "
            "for a theoretical paper on this topic. Crucial Constraints: Do not use any "
            "bracketed sections or 'cite:' tags in the output. The abstract must not contain "
            "the word 'valuation'."
        ),
    },
    {
        "id":   "Q5_Document_Extraction",
        "text": (
            f"DOCUMENT TEXT:\n---\n{q5_doc_text}\n---\n\n"
            "Using strictly the provided document, identify the three main steps of multiple "
            "imputation as defined by the author. Then, referring to the numbered exercise "
            "section at the end of the text, how many extra iterations does the author suggest "
            "running with the mice.mids() function, and what specific algorithmic behavior is "
            "that action meant to evaluate?"
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
    print(f"[FATAL] Vulkan llama-server binary not found at: {LLAMA_BIN}")
    print(f"        Ensure build-vulkan has been compiled: ~/llama.cpp/build-vulkan/")
    sys.exit(1)


# ------------------------------------------------------------------------------
# REPORT HEADER
# ------------------------------------------------------------------------------
with open(report_file, "w") as f:
    f.write("# FishTex General Benchmark — Vulkan\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("**System:** AMD Ryzen AI Max+ 395 | 128GB LPDDR5 @ 8000MHz | Fedora 43 Server\n")
    f.write("**Engine:** Vulkan — `~/llama.cpp/build-vulkan/bin/llama-server`\n")
    f.write("**Device:** `vulkan1` (AMD Radeon 8060S / Strix Halo 128GB)\n")
    f.write("**KV Cache:** `-ctk q8_0 -ctv q8_0` (heavyweight) | Kimi-Linear: F16 (architecture constraint)\n")
    f.write("**Batch:** `--ubatch-size 4096 --batch-size 4096`\n")
    f.write(f"**Models queued:** {len(models)}\n\n---\n\n")

print(f"\n{'='*60}")
print(f"  FishTex General Benchmark — Vulkan")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"  Engine: Vulkan1 (Strix Halo) | Models: {len(models)}")
print(f"  Report: {report_file}")
print(f"{'='*60}")


# ------------------------------------------------------------------------------
# MAIN BENCHMARK LOOP
# ------------------------------------------------------------------------------
for model_alias, model_cfg in models.items():
    model_path = model_cfg["path"]
    context    = model_cfg["context"]
    gpu_layers = model_cfg["gpu_layers"]
    is_kimi    = model_alias in KIMI_LINEAR_MODELS

    print(f"\n{'='*60}")
    print(f"[+] Model: {model_alias}")
    print(f"    Path:    {model_path}")
    print(f"    Context: {context} | GPU Layers: {gpu_layers}")
    print(f"    Device:  vulkan1 | KV: {'F16 (Kimi-Linear)' if is_kimi else 'q8_0'}")
    print(f"{'='*60}")

    if not os.path.isfile(model_path):
        print(f"[-] Model file not found — skipping: {model_path}")
        with open(report_file, "a") as f:
            f.write(f"## Model: {model_alias}\n\n")
            f.write(f"**SKIPPED** — file not found at `{model_path}`\n\n---\n\n")
        continue

    server_process = None

    try:
        env = os.environ.copy()

        cmd = [
            LLAMA_BIN,
            "-m",            model_path,
            "--alias",       model_alias,
            "-c",            str(context),
            "-t",            str(THREADS),
            "-ngl",          str(gpu_layers),
            "--device",      "vulkan1",     # Force Strix Halo — avoid 3060 Ti (vulkan0)
            "--parallel",    "1",
            "--flash-attn",  "on",
            "--ubatch-size", str(UBATCH),
            "--batch-size",  str(BATCH),
            "--no-mmap",
            "--host",        "0.0.0.0",
            "--port",        str(PORT),
        ]

        # Kimi-Linear architecture requires F16 KV cache.
        # n_embd_head_v=72 is not divisible by q8_0 block size (32).
        # All other models retain q8_0 KV compression for heavyweight strategy.
        if not is_kimi:
            cmd += ["-ctk", "q8_0", "-ctv", "q8_0"]

        model_error_log = f"error_vulkan_{model_alias.replace(' ', '_')}_{timestamp}.log"

        with open(model_error_log, "w") as err_out:
            server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=err_out,
                env=env
            )

        print(f"    Waiting up to {BOOT_TIMEOUT}s for server ready...")
        ready = wait_for_server(BOOT_TIMEOUT)

        if not ready:
            print(f"[-] Server failed to start — check: {model_error_log}")
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
            f.write(f"- **Engine:** Vulkan1 (Strix Halo)\n")
            f.write(f"- **KV Cache:** {'F16 uncompressed (Kimi-Linear architecture constraint)' if is_kimi else 'q8_0 compressed'}\n")
            f.write(f"- **Started:** {datetime.now().strftime('%H:%M:%S')}\n\n")

        model_start = time.time()

        for idx, p in enumerate(prompts):
            print(f"    -> {p['id']} ({idx+1}/{len(prompts)})...")
            start_time = time.time()

            try:
                res = requests.post(
                    f"http://127.0.0.1:{PORT}/v1/chat/completions",
                    json={
                        "messages":    [{"role": "user", "content": p["text"]}],
                        "temperature": 0.1,
                        "max_tokens":  4096,
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
                    print(f"       [-] HTTP {res.status_code} on {p['id']}")
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
        with open(report_file, "a") as f:
            f.write(f"**Total time for {model_alias}:** {model_elapsed:.1f}s\n\n---\n\n")

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
print(f"[+] All models complete.")
print(f"    Report: {report_file}")
print(f"{'='*60}\n")

with open(report_file, "a") as f:
    f.write(f"## Run Complete\n\n")
    f.write(f"**Finished:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")