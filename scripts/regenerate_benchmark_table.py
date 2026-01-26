import json

def generate_table():
    with open('reports/benchmark_100_cases_final.json', 'r') as f:
        data = json.load(f)
    
    table_lines = []
    # Header
    table_lines.append("| ID | Category | Input | Raw Qwen Response | Q-Res | Malaya LLM Response | M-Res |")
    table_lines.append("|:---|:---|:---|:---|:---:|:---|:---:|")
    
    seen_ids = set()
    
    # Sort details by ID to be neat
    details = sorted(data['details'], key=lambda x: x['id'])
    
    for case in details:
        if case['id'] in seen_ids:
            continue
        seen_ids.add(case['id'])
        
        # Format Pass/Fail
        # Score 1 = Pass, Score 0 = Fail
        q_res = "✅" if case.get('raw_score', 0) == 1 else "❌"
        m_res = "✅" if case.get('malaya_score', 0) == 1 else "❌"
        
        # Clean text for markdown table
        # 1. Replace newlines with <br>
        # 2. Escape pipe characters |
        def clean(text):
            if text is None: return ""
            return str(text).replace('\n', '<br>').replace('|', '\|').replace('\r', '')

        raw_resp = clean(case.get('raw_output', ''))
        malaya_resp = clean(case.get('malaya_output', ''))
        inp = clean(case.get('input', ''))
        cat = clean(case.get('category', ''))
        
        row = f"| {case['id']} | {cat} | {inp} | {raw_resp} | {q_res} | {malaya_resp} | {m_res} |"
        table_lines.append(row)
        
    return "\n".join(table_lines)

def update_report():
    new_table = generate_table()
    
    file_path = 'reports/benchmark_baseline.md'
    with open(file_path, 'r') as f:
        content = f.read()

    start_marker = "## 📜 Full 100-Case Comparison (Line-by-Line)"
    
    if start_marker not in content:
        print(f"Could not find start marker: {start_marker!r}")
        print(f"First 500 chars: {content[:500]!r}")
        return

    # Split content to insert table
    lines = content.split('\n')
    header_idx = -1
    for i, line in enumerate(lines):
        if start_marker in line:
            header_idx = i
            break
            
    if header_idx == -1:
        print("Error finding header index.")
        return
        
    # We want everything before the table
    # usually header is line N, then N+1 is blank, then table starts
    # We will preserve up to header_idx + 1 (blank line)
    new_lines = lines[:header_idx+2]
    
    new_lines.append(new_table)
    
    # Append the footer note
    footer = "\n\n---\n\n*(Note: Table excludes duplicate re-runs of the same case to keep it concise.)*"
    new_lines.append(footer)
    
    final_content = "\n".join(new_lines)
    
    with open(file_path, 'w') as f:
        f.write(final_content)
    
    print("Report updated successfully.")

if __name__ == "__main__":
    update_report()
