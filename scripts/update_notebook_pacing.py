import json

notebook_path = "Malaya_LLM_Finetune.ipynb"

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# Find the cell that sets up the trainer
# The logic handles:
# 1. Drive mounting
# 2. Checkpoint dir logic
# 3. Trainer Modification
# 4. Resume from checkpoint logic

# We will modify the cell that initializes the model and trainer.
# Looking at the previous views, that is around cell index 4?
# Let's verify cell content
# Cell 0: Markdown intro
# Cell 1: imports
# Cell 2: Load model
# Cell 3: Load dataset
# Cell 4: Format dataset
# Cell 5: Setup Trainer (THIS ONE)

trainer_cell_source = nb['cells'][5]['source']

# New source code for the cell
new_source = [
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
    "# FULL TRAINING\n",
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
    "        # max_steps = -1, \n",
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
    "print(\"✅ Trainer ready! Checkpoints enabled.\")"
]

nb['cells'][5]['source'] = new_source

# Update the Training execution cell (Cell 6) to use resume_from_checkpoint
training_cell_source = nb['cells'][6]['source']

# Modify starting code to resume if checkpoint found
new_training_source = [
    "# IMPORTANT: When wandb asks, type 3 and press Enter!\n",
    "import os\n",
    "os.environ[\"WANDB_DISABLED\"] = \"true\"  # Skip wandb prompt\n",
    "\n",
    "print(\"🚀 Starting training...\")\n",
    "# If checkpoint was found in previous cell, resume from it\n",
    "if last_checkpoint:\n",
    "    print(f\"▶️ Resuming from {last_checkpoint}...\")\n",
    "    trainer_stats = trainer.train(resume_from_checkpoint=last_checkpoint)\n",
    "else:\n",
    "    trainer_stats = trainer.train()\n",
    "\n",
    "print(\"\\n\" + \"=\"*50)\n",
    "print(\"🎉 TRAINING COMPLETE!\")\n",
    "print(\"=\"*50)"
]

nb['cells'][6]['source'] = new_training_source

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=4) # changed from default indent to 4 for niceness
    
print("Notebook updated successfully.")
