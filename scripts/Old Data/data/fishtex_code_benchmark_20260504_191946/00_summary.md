# FishTex Coding Benchmark — Summary

**Date:** 2026-05-04 19:19:46
**System:** AMD Ryzen AI Max+ 395 | 128GB LPDDR5 @ 8000MHz | Fedora 43 Server
**Engine:** ROCm — `~/llama.cpp/build/bin/llama-server`
**KV Cache:** F16 uncompressed (lightweight strategy — `-ctk`/`-ctv` removed)
**Batch:** `--ubatch-size 1024 --batch-size 2048`
**Models queued:** 26

| Model | Prompts run | Avg t/s | Total time |
|-------|-------------|---------|------------|
| Qwen2.5-Coder-32B-Q8_0 | 3/3 | 6.42 | 225.3s |
| Qwen2.5-Coder-32B-Q6_K_L | 3/3 | 8.08 | 194.1s |
| DavidAU-Qwen3.6-27B-Heretic-Q8_0 | 3/3 | 7.31 | 664.3s |
| DavidAU-Qwen3.6-27B-Heretic-Q6_K | 3/3 | 9.32 | 507.7s |
| DavidAU-Qwen3.6-40B-Deckard-Q8_0 | 0/3 | 0.00 | 900.3s |
| DavidAU-Qwen3.6-40B-Deckard-Q6_K | 1/3 | 6.31 | 872.3s |
| Cerebras-MiniMax-M2-172B-IQ4_NL | SKIPPED — file not found | — | — |
| Nemotron-3-Super-120B-UD-Q4_K_XL | 3/3 | 15.72 | 187.0s |
| Qwen3.5-122B-Claude-Q5_K_M | 3/3 | 21.27 | 72.3s |
| Zen4-Thinking-Q6_K | 3/3 | 39.87 | 132.6s |
| Qwen3.5-35B-Claude-Distilled-Q6_K | 3/3 | 49.00 | 38.4s |
| Qwen3.5-40B-Claude-Deckard-Heretic-Q6_K | 1/3 | 6.39 | 866.0s |
| DBRX-Instruct-Q5_K_M | FAILED — server did not start | — | — |
| Mistral-Medium-3.5-128B-Q5_K_M | 3/3 | 2.39 | 638.4s |
| Mistral-Large-2411-Q5_K_M | 3/3 | 2.45 | 790.0s |
| Mistral-Large-2411-Q6_K | 2/3 | 2.20 | 872.1s |
| HauhauCS-Qwen3.6-35B-Uncensored-Q6_K_P | 3/3 | 48.58 | 126.5s |
| DuoNeural-Qwen3.6-35B-Code-Q5_K_M | 3/3 | 52.64 | 116.0s |
| GPT-OSS_120B | 3/3 | 48.99 | 70.1s |
| Kimi-Dev-72B | 3/3 | 43.37 | 116.1s |
| Qwen3-Next-80B-Thinking-Uncensored | 3/3 | 39.99 | 131.9s |
| Qwen3-Coder-Next | 3/3 | 34.43 | 52.1s |
| Qwen3-Coder-30B | 3/3 | 53.50 | 44.6s |
| DeepSeek-Coder-V2-Lite-Instruct | 3/3 | 46.81 | 38.9s |
| Qwen3-VL-235B-A22B-Thinking | 3/3 | 13.71 | 252.1s |
| Qwen3.5-122B-Claude | SKIPPED — file not found | — | — |
