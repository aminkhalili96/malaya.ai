import json
from pathlib import Path

nb_path = Path("Malaya_LLM_Finetune.ipynb")

with open(nb_path, "r") as f:
    nb = json.load(f)

# Define the new cell
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# [OPTIONAL] Push to Hugging Face Hub (Run this after training)\n",
        "# 1. Get your token from https://huggingface.co/settings/tokens\n",
        "# 2. Un-comment the lines below and run\n",
        "\n",
        "# from huggingface_hub import login\n",
        "# login()\n",
        "# model.push_to_hub_gguf(\n",
        "#     \"YOUR_USERNAME/malaya-llm-7b-instruct-v1\", # <--- Change this to your repo name\n",
        "#     tokenizer,\n",
        "#     quantization_method = \"q4_k_m\"\n",
        "# )\n",
        "# print(\"✅ Model Pushed to Hugging Face!\")"
    ]
}

# Append to cells
nb["cells"].append(new_cell)

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=4)

print("✅ Added Hugging Face Push cell to notebook.")
