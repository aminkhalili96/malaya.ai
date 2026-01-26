import json
import sys
import os

log = open('script_log.txt', 'w')

try:
    log.write("Starting script...\n")
    with open('reports/benchmark_100_cases_final.json', 'r') as f:
        data = json.load(f)
    log.write("Loaded JSON\n")
    
    header = "| ID | Category | Input | Raw Qwen Response | Q-Res | Malaya LLM Response | M-Res |"
    divider = "|:---|:---|:---|:---|:---:|:---|:---:|"
    
    rows = []
    seen = set()
    details = sorted(data['details'], key=lambda x: x['id'])
    
    for case in details:
        if case['id'] in seen: continue
        seen.add(case['id'])
        
        q_score = case.get('raw_score', 0)
        m_score = case.get('malaya_score', 0)
        
        q_res = "✅" if q_score == 1 else "❌"
        m_res = "✅" if m_score == 1 else "❌"
        
        def clean(s):
            if s is None: return ""
            return str(s).replace('\n', '<br>').replace('|', '\|').replace('\r', '')
        
        row = f"| {case['id']} | {clean(case.get('category'))} | {clean(case.get('input'))} | {clean(case.get('raw_output'))} | {q_res} | {clean(case.get('malaya_output'))} | {m_res} |"
        rows.append(row)
        
    table = header + "\n" + divider + "\n" + "\n".join(rows)
    log.write(f"Generated table with {len(rows)} rows\n")
    
    with open('reports/benchmark_baseline.md', 'r') as f:
        orig = f.read()
        
    start_marker = "## 📜 Full 100-Case Comparison (Line-by-Line)"
    if start_marker not in orig:
        log.write("Marker not found in original file\n")
        sys.exit(1)
        
    # Split content carefully
    header_part = orig.split(start_marker)[0]
    
    # Check for footer
    footer_text = "*(Note: Table excludes duplicate re-runs"
    
    # We will reconstruct: header + marker + new table + footer
    new_content = header_part + start_marker + "\n\n" + table + "\n\n" + footer_text + " of the same case to keep it concise.)*"
    
    target_path = 'reports/benchmark_baseline_temp.md'
    with open(target_path, 'w') as f:
        f.write(new_content)
        
    log.write(f"Written to {target_path}\n")
    
    # Replace original
    os.rename(target_path, 'reports/benchmark_baseline.md')
    log.write("Renamed temp file to original file.\n")

except Exception as e:
    log.write(f"Error: {e}\n")
    
log.close()
