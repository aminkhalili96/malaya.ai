import json

notebook_path = "Malaya_LLM_Finetune.ipynb"

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# 1. Update Cell 2 (Model Loading) to swap to 7B
model_load_source =  nb['cells'][2]['source']
new_model_source = [
    "from unsloth import FastLanguageModel\n",
    "import torch\n",
    "\n",
    "max_seq_length = 2048\n",
    "dtype = None\n",
    "load_in_4bit = True\n",
    "\n",
    "model, tokenizer = FastLanguageModel.from_pretrained(\n",
    "    # Switched to Qwen 2.5 7B for feasible training on Free Colab\n",
    "    model_name = \"unsloth/Qwen2.5-7B-Instruct-bnb-4bit\",\n",
    "    # model_name = \"unsloth/Qwen2.5-14B-Instruct-bnb-4bit\", # <-- Requires A100 or paid tier\n",
    "    max_seq_length = max_seq_length,\n",
    "    dtype = dtype,\n",
    "    load_in_4bit = load_in_4bit,\n",
    ")\n",
    "print(\"✅ Model loaded! Using Qwen 2.5 7B (Lightweight Version)\")"
]
nb['cells'][2]['source'] = new_model_source


# 2. Update Cell 5 (Trainer Setup) to add max_steps limit
# We need to find the specific line in the source array and inject max_steps
trainer_source = nb['cells'][5]['source']

# Use a clean replacement of the TrainingArgs section
# We iterate to find where 'num_train_epochs = 1' is
new_trainer_source = [
    "from google.colab import drive\n",
    "drive.mount('/content/drive')\n",
    "\n",
    "# Checkpoint directory in Drive\n",
    "checkpoint_dir = \"/content/drive/MyDrive/Malaya_LLM_Checkpoints\"\n",
    "import os\n",
    "os.makedirs(checkpoint_dir, exist_ok=True)\n",
    "\n",
    "from trl import SFTTrainer\n",
    "from transformers import TrainingArguments\n",
    "from unsloth import is_bfloat16_supported\n",
    "\n",
    "model = FastLanguageModel.get_peft_model(\n",
    "    model,\n",
    "    r = 16,\n",
    "    target_modules = [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\",\n",
    "                      \"gate_proj\", \"up_proj\", \"down_proj\",],\n",
    "    lora_alpha = 16,\n",
    "    lora_dropout = 0,\n",
    "    bias = \"none\",\n",
    "    use_gradient_checkpointing = \"unsloth\",\n",
    "    random_state = 3407,\n",
    "    use_rslora = False,\n",
    "    loftq_config = None,\n",
    ")\n",
    "\n",
    "# Check for existing checkpoints to resume\n",
    "last_checkpoint = None\n",
    "if os.path.isdir(checkpoint_dir):\n",
    "    checkpoints = [d for d in os.listdir(checkpoint_dir) if d.startswith(\"checkpoint-\")]\n",
    "    if checkpoints:\n",
    "        # Sort by step number\n",
    "        checkpoints.sort(key=lambda x: int(x.split(\"-\")[1]))\n",
    "        last_checkpoint = os.path.join(checkpoint_dir, checkpoints[-1])\n",
    "        print(f\"🔄 Found checkpoint: {last_checkpoint}. Will resume training!\")\n",
    "\n",
    "# FULL TRAINING - With Steps Limit for Feasibility\n",
    "trainer = SFTTrainer(\n",
    "    model = model,\n",
    "    tokenizer = tokenizer,\n",
    "    train_dataset = dataset,\n",
    "    dataset_text_field = \"text\",\n",
    "    max_seq_length = max_seq_length,\n",
    "    dataset_num_proc = 2,\n",
    "    packing = False,\n",
    "    args = TrainingArguments(\n",
    "        per_device_train_batch_size = 2,\n",
    "        gradient_accumulation_steps = 4,\n",
    "        warmup_steps = 100,\n",
    "        num_train_epochs = 1, \n",
    "        max_steps = 3000,      # <-- CAPPED AT 3000 STEPS (Approx 4-5 hours) \n",
    "        learning_rate = 2e-4,\n",
    "        fp16 = not is_bfloat16_supported(),\n",
    "        bf16 = is_bfloat16_supported(),\n",
    "        logging_steps = 50,\n",
    "        optim = \"adamw_8bit\",\n",
    "        weight_decay = 0.01,\n",
    "        lr_scheduler_type = \"cosine\",\n",
    "        seed = 3407,\n",
    "        output_dir = checkpoint_dir,\n",
    "        save_steps = 100,      # Save often to avoid data loss\n",
    "        save_total_limit = 2,  # Keep only last 2 checkpoints\n",
    "    ),\n",
    ")\n",
    "\n",
    "print(\"✅ Trainer ready! Optimized for Free Colab (3000 Steps Limit).\")"
]

nb['cells'][5]['source'] = new_trainer_source

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=4) # Clean indentation
    
print("Successfully switched to 7B model and applied 3000 max_steps limit.")
