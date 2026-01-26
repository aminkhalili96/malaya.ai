#!/usr/bin/env python3
"""
🧹 Mesolitica Data Cleaner for Fine-Tuning
==========================================
Downloads and cleans ALL Mesolitica instruction datasets into a unified format.

Usage:
    python scripts/clean_mesolitica_data.py

Output:
    data/mesolitica_clean.jsonl  (~150k+ instruction-output pairs)
"""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, field_validator
from datasets import load_dataset
from tqdm import tqdm

# ============================================================================
# Configuration
# ============================================================================

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "mesolitica_clean.jsonl"

# Mesolitica datasets to process (with their file patterns)
DATASETS = [
    {
        "name": "mesolitica/chatgpt-malay-instructions",
        "files": [
            "synthetic-malaysian-general-qa.jsonl",
            "synthetic-malaysian-general-qa-v2.jsonl",
            "synthetic-alpaca_data_cleaned.jsonl",
        ]
    },
]

# ============================================================================
# Pydantic Model for Validation
# ============================================================================

class InstructionRow(BaseModel):
    """Validated instruction-output pair."""
    instruction: str
    output: str
    
    @field_validator('instruction', 'output', mode='before')
    @classmethod
    def coerce_to_string(cls, v):
        """Convert any value to string, handle None."""
        if v is None:
            return ""
        if isinstance(v, (list, dict)):
            return json.dumps(v, ensure_ascii=False)
        return str(v).strip()
    
    @field_validator('instruction', 'output')
    @classmethod
    def must_not_be_empty(cls, v):
        """Ensure fields are not empty."""
        if not v or len(v.strip()) < 5:
            raise ValueError("Field too short or empty")
        return v

# ============================================================================
# Cleaning Functions
# ============================================================================

def extract_instruction_output(row: dict) -> Optional[dict]:
    """
    Extract and validate instruction-output from a row.
    Handles multiple column naming conventions.
    """
    # Try different column name patterns
    instruction = (
        row.get("instruction") or 
        row.get("instruction_ms") or 
        row.get("question") or
        row.get("input") or
        ""
    )
    
    output = (
        row.get("output") or 
        row.get("output_ms") or 
        row.get("answer") or
        row.get("response") or
        ""
    )
    
    try:
        validated = InstructionRow(instruction=instruction, output=output)
        return {"instruction": validated.instruction, "output": validated.output}
    except Exception:
        return None

def process_dataset(dataset_config: dict) -> list[dict]:
    """Process a single dataset configuration."""
    results = []
    name = dataset_config["name"]
    files = dataset_config["files"]
    
    print(f"\n📥 Processing: {name}")
    
    for file in files:
        try:
            print(f"   Loading: {file}...")
            ds = load_dataset(name, data_files=file, split="train")
            
            valid_count = 0
            for row in tqdm(ds, desc=f"   Cleaning {file}", leave=False):
                cleaned = extract_instruction_output(row)
                if cleaned:
                    results.append(cleaned)
                    valid_count += 1
            
            print(f"   ✅ {valid_count:,} valid rows from {file}")
            
        except Exception as e:
            print(f"   ⚠️ Skipped {file}: {e}")
    
    return results

def deduplicate(data: list[dict]) -> list[dict]:
    """Remove duplicate instruction-output pairs."""
    seen = set()
    unique = []
    
    for row in data:
        key = (row["instruction"][:100], row["output"][:100])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    
    return unique

# ============================================================================
# Main
# ============================================================================

def main():
    print("🧹 Mesolitica Data Cleaner")
    print("=" * 50)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Process all datasets
    all_data = []
    for ds_config in DATASETS:
        all_data.extend(process_dataset(ds_config))
    
    print(f"\n📊 Total rows collected: {len(all_data):,}")
    
    # Deduplicate
    unique_data = deduplicate(all_data)
    print(f"📊 After deduplication: {len(unique_data):,}")
    
    # Save to JSONL
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in unique_data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    
    # Stats
    file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"\n✅ Done!")
    print(f"   Rows: {len(unique_data):,}")
    print(f"   Size: {file_size:.1f} MB")
    print(f"   File: {OUTPUT_FILE}")
    
    print("\n🚀 Next step: Upload this file to HuggingFace or use directly in Colab!")

if __name__ == "__main__":
    main()
