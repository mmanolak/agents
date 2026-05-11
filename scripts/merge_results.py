import sys
import os
import re
from datetime import datetime

# ==============================================================================
# FishTex Benchmark Merger — merge_results.py
# Merges ROCm and Vulkan benchmark MD files into a single combined document
# using a model-first structure for easy Gemini Pro review.
#
# Usage:
#   python merge_results.py <rocm_file.md> <vulkan_file.md> [output_file.md]
#
# Examples:
#   # General benchmark merge:
#   python merge_results.py bench_general_ROCm_20250505.md bench_general_Vulkan_20250505.md
#
#   # Code benchmark merge:
#   python merge_results.py bench_code_ROCm_20250505.md bench_code_Vulkan_20250505.md
#
#   # With explicit output filename:
#   python merge_results.py bench_general_ROCm_20250505.md bench_general_Vulkan_20250505.md general_combined.md
#
# Output structure per model:
#   ## Model Name
#   ### ROCm
#   [all ROCm prompts and results]
#   ### Vulkan
#   [all Vulkan prompts and results]
#   ### Speed Comparison
#   [side-by-side t/s table]
# ==============================================================================


def usage():
    print("Usage: python merge_results.py <rocm_file.md> <vulkan_file.md> [output_file.md]")
    print("")
    print("  rocm_file.md    — output from bench_general_ROCm.py or bench_code_ROCm.py")
    print("  vulkan_file.md  — output from bench_general_Vulkan.py or bench_code_Vulkan.py")
    print("  output_file.md  — optional output filename (auto-generated if omitted)")
    sys.exit(1)


def parse_md_into_models(filepath):
    """
    Parse a benchmark MD file into a dict of model_name -> raw_content_string.
    Each model section starts with '## Model: <name>' or '## <name>' and ends
    at the next '## ' heading or end of file.
    Returns:
        header_text  — everything before the first model section
        models_dict  — {model_alias: raw_section_text}
        run_complete — the final 'Run Complete' section if present
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on any ## heading that looks like a model entry
    # Model sections start with ## followed by model name (not ###)
    section_pattern = re.compile(r'^## ', re.MULTILINE)
    positions = [m.start() for m in section_pattern.finditer(content)]

    if not positions:
        print(f"[!] Warning: No model sections found in {filepath}")
        return content, {}, ""

    header_text  = content[:positions[0]]
    models_dict  = {}
    run_complete = ""

    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(content)
        section = content[pos:end].strip()

        # Extract the heading name
        first_line = section.split("\n")[0]
        # Strip the '## ' prefix and 'Model: ' prefix if present
        name = first_line.lstrip("# ").strip()
        if name.startswith("Model: "):
            name = name[len("Model: "):].strip()

        # Separate out the Run Complete section
        if name in ("Run Complete", "Run Complete\n"):
            run_complete = section
            continue

        models_dict[name] = section

    return header_text, models_dict, run_complete


def extract_tps_from_section(section_text):
    """
    Extract per-prompt t/s values from a model section.
    Returns a dict of {prompt_id: tps_float} and overall avg if present.
    """
    tps_map = {}
    avg_tps = None

    # Match prompt subsections and their speed values
    # Looks for: | Speed | X.XX t/s |
    prompt_blocks = re.split(r'(?=^### )', section_text, flags=re.MULTILINE)

    for block in prompt_blocks:
        # Get prompt id from ### heading
        heading_match = re.match(r'^### (.+)', block)
        if not heading_match:
            continue
        prompt_id = heading_match.group(1).strip()

        # Get speed value
        speed_match = re.search(r'\| Speed \| ([\d.]+) t/s \|', block)
        if speed_match:
            tps_map[prompt_id] = float(speed_match.group(1))

    # Also try to get average from run statistics
    avg_match = re.search(r'Average speed: ([\d.]+) t/s', section_text)
    if avg_match:
        avg_tps = float(avg_match.group(1))

    # For bench_code format: **Speed:** X.XX t/s
    if not tps_map:
        speed_matches = re.findall(r'\*\*Speed:\*\* ([\d.]+) t/s', section_text)
        prompt_ids    = re.findall(r'^## (.+)', section_text, re.MULTILINE)
        for pid, tps in zip(prompt_ids, speed_matches):
            tps_map[pid.strip()] = float(tps)

    return tps_map, avg_tps


def build_comparison_table(rocm_tps, vulkan_tps, rocm_avg, vulkan_avg):
    """
    Build a markdown comparison table from two tps dicts.
    """
    lines = []
    lines.append("### Speed Comparison\n")
    lines.append("| Prompt | ROCm t/s | Vulkan t/s | Δ t/s | Winner |")
    lines.append("|--------|----------|------------|-------|--------|")

    all_prompts = sorted(set(list(rocm_tps.keys()) + list(vulkan_tps.keys())))

    for prompt in all_prompts:
        r = rocm_tps.get(prompt)
        v = vulkan_tps.get(prompt)

        if r is not None and v is not None:
            delta  = v - r
            winner = "Vulkan" if v > r else ("ROCm" if r > v else "Tie")
            lines.append(f"| {prompt} | {r:.2f} | {v:.2f} | {delta:+.2f} | {winner} |")
        elif r is not None:
            lines.append(f"| {prompt} | {r:.2f} | — | — | ROCm only |")
        else:
            lines.append(f"| {prompt} | — | {v:.2f} | — | Vulkan only |")

    # Average row
    if rocm_avg is not None or vulkan_avg is not None:
        r_avg  = f"{rocm_avg:.2f}" if rocm_avg is not None else "—"
        v_avg  = f"{vulkan_avg:.2f}" if vulkan_avg is not None else "—"
        if rocm_avg is not None and vulkan_avg is not None:
            delta  = vulkan_avg - rocm_avg
            winner = "Vulkan" if vulkan_avg > rocm_avg else ("ROCm" if rocm_avg > vulkan_avg else "Tie")
            lines.append(f"| **Average** | **{r_avg}** | **{v_avg}** | **{delta:+.2f}** | **{winner}** |")
        else:
            lines.append(f"| **Average** | **{r_avg}** | **{v_avg}** | — | — |")

    return "\n".join(lines)


def strip_model_heading(section_text, model_name):
    """Remove the ## Model: <name> or ## <name> heading from the top of a section."""
    lines = section_text.split("\n")
    # Skip the first heading line and any immediately following blank lines
    start = 1
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    return "\n".join(lines[start:]).strip()


def merge_files(rocm_path, vulkan_path, output_path):
    print(f"\n[+] Reading ROCm file:   {rocm_path}")
    rocm_header, rocm_models, rocm_complete = parse_md_into_models(rocm_path)

    print(f"[+] Reading Vulkan file: {vulkan_path}")
    _, vulkan_models, _ = parse_md_into_models(vulkan_path)

    print(f"[+] ROCm models found:   {len(rocm_models)}")
    print(f"[+] Vulkan models found: {len(vulkan_models)}")

    # Union of all model names, preserving ROCm order then any Vulkan-only extras
    all_models = list(rocm_models.keys())
    for m in vulkan_models.keys():
        if m not in all_models:
            all_models.append(m)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_path, "w", encoding="utf-8") as out:
        # --- Document header ---
        out.write("# FishTex Benchmark — Combined Results (ROCm vs Vulkan)\n\n")
        out.write(f"**Generated:** {timestamp}\n")
        out.write(f"**ROCm source:** `{os.path.basename(rocm_path)}`\n")
        out.write(f"**Vulkan source:** `{os.path.basename(vulkan_path)}`\n")
        out.write(f"**Total models:** {len(all_models)}\n\n")
        out.write("---\n\n")

        # --- Global speed summary table ---
        out.write("## Global Speed Summary\n\n")
        out.write("| Model | ROCm Avg t/s | Vulkan Avg t/s | Δ t/s | Winner |\n")
        out.write("|-------|-------------|----------------|-------|--------|\n")

        summary_rows = []
        for model_name in all_models:
            rocm_sec   = rocm_models.get(model_name, "")
            vulkan_sec = vulkan_models.get(model_name, "")

            _, rocm_avg   = extract_tps_from_section(rocm_sec)
            _, vulkan_avg = extract_tps_from_section(vulkan_sec)

            r_str = f"{rocm_avg:.2f}" if rocm_avg is not None else "—"
            v_str = f"{vulkan_avg:.2f}" if vulkan_avg is not None else "—"

            if rocm_avg is not None and vulkan_avg is not None:
                delta  = vulkan_avg - rocm_avg
                winner = "Vulkan" if vulkan_avg > rocm_avg else ("ROCm" if rocm_avg > vulkan_avg else "Tie")
                summary_rows.append((model_name, r_str, v_str, f"{delta:+.2f}", winner))
                out.write(f"| {model_name} | {r_str} | {v_str} | {delta:+.2f} | {winner} |\n")
            elif rocm_avg is not None:
                summary_rows.append((model_name, r_str, "—", "—", "ROCm only"))
                out.write(f"| {model_name} | {r_str} | — | — | ROCm only |\n")
            elif vulkan_avg is not None:
                summary_rows.append((model_name, "—", v_str, "—", "Vulkan only"))
                out.write(f"| {model_name} | — | {v_str} | — | Vulkan only |\n")
            else:
                out.write(f"| {model_name} | — | — | — | — |\n")

        out.write("\n---\n\n")

        # --- Per-model detailed sections ---
        for model_name in all_models:
            rocm_sec   = rocm_models.get(model_name, "")
            vulkan_sec = vulkan_models.get(model_name, "")

            out.write(f"## {model_name}\n\n")

            # ROCm subsection
            out.write("### ROCm\n\n")
            if rocm_sec:
                out.write(strip_model_heading(rocm_sec, model_name))
                out.write("\n\n")
            else:
                out.write("_No ROCm data for this model._\n\n")

            # Vulkan subsection
            out.write("### Vulkan\n\n")
            if vulkan_sec:
                out.write(strip_model_heading(vulkan_sec, model_name))
                out.write("\n\n")
            else:
                out.write("_No Vulkan data for this model._\n\n")

            # Speed comparison table
            if rocm_sec and vulkan_sec:
                rocm_tps,   rocm_avg   = extract_tps_from_section(rocm_sec)
                vulkan_tps, vulkan_avg = extract_tps_from_section(vulkan_sec)
                comparison = build_comparison_table(rocm_tps, vulkan_tps, rocm_avg, vulkan_avg)
                out.write(comparison)
                out.write("\n\n")

            out.write("---\n\n")

        # --- Footer ---
        out.write("## Merge Complete\n\n")
        out.write(f"**Merged at:** {timestamp}\n")
        out.write(f"**ROCm source:** `{rocm_path}`\n")
        out.write(f"**Vulkan source:** `{vulkan_path}`\n")

    print(f"\n[+] Combined report written to: {output_path}")
    print(f"    Models merged: {len(all_models)}")
    print(f"    File size:     {os.path.getsize(output_path) / 1024:.1f} KB\n")


# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()

    rocm_file   = sys.argv[1]
    vulkan_file = sys.argv[2]

    # Auto-generate output filename if not provided
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]
    else:
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Infer benchmark type from input filename
        base        = os.path.basename(rocm_file).lower()
        bench_type  = "code" if "code" in base else "general"
        output_file = f"bench_{bench_type}_combined_{ts}.md"

    # Validate inputs
    for f in [rocm_file, vulkan_file]:
        if not os.path.isfile(f):
            print(f"[FATAL] File not found: {f}")
            sys.exit(1)

    merge_files(rocm_file, vulkan_file, output_file)