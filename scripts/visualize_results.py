
import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

# SETTING THE "NANO BANANA PRO 3" AESTHETIC (Cyberpunk/Dark Mode)
plt.style.use('dark_background')
sns.set_palette("husl")

def generate_charts():
    log_path = Path("reports/benchmark_100_cases_logs.jsonl")
    if not log_path.exists():
        print("No log file found.")
        return

    data = []
    with open(log_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except:
                    pass
    
    if not data:
        print("No data found.")
        return

    df = pd.DataFrame(data)
    
    # Process Data
    # Calculate Mean scores (0 or 1)
    # Filter timeouts if necessary, but for now treating 0 as 0
    
    stats = []
    
    # Overall
    raw_acc = df["raw_score"].mean() * 100
    malaya_acc = df["malaya_score"].mean() * 100
    stats.append({"Category": "OVERALL", "Model": "Raw Qwen", "Accuracy": raw_acc})
    stats.append({"Category": "OVERALL", "Model": "Malaya LLM", "Accuracy": malaya_acc})
    
    # By Category
    cats = df["category"].unique()
    for cat in cats:
        sub = df[df["category"] == cat]
        r = sub["raw_score"].mean() * 100
        m = sub["malaya_score"].mean() * 100
        stats.append({"Category": cat, "Model": "Raw Qwen", "Accuracy": r})
        stats.append({"Category": cat, "Model": "Malaya LLM", "Accuracy": m})
        
    df_stats = pd.DataFrame(stats)
    
    # PLOT
    plt.figure(figsize=(14, 8))
    
    # Custom colors: Raw=Red/Grey, Malaya=Neon Green
    palette = {"Raw Qwen": "#ff4d4d", "Malaya LLM": "#00ff99"}
    
    sns.barplot(data=df_stats, x="Category", y="Accuracy", hue="Model", palette=palette)
    
    plt.title("Malaya LLM vs Raw Qwen: Accuracy Benchmark", fontsize=20, color="#ffffff", pad=20)
    plt.ylabel("Accuracy (%)", fontsize=14)
    plt.xlabel("Category", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(title="Model", title_fontsize=12)
    
    # Save
    output_path = "reports/benchmark_viz.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"Chart saved to {output_path}")

if __name__ == "__main__":
    generate_charts()
