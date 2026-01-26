
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

print("🚀 Verifying Native HuggingFace Mode (Mac Compatible)...")

model_name = "mesolitica/t5-super-tiny-bahasa-cased"

try:
    print(f"📥 Loading model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("✅ Model loaded!")

    input_text = "saya xleh pegi sana"
    prefix = "normalisasi: " 
    # Note: T5 might need specific prefix depending on training.
    # Mesolitica docs usually say prefix is needed or just raw text.
    # For 't5-super-tiny-bahasa-cased', let's try raw first or 'manglish to malay'.
    
    # Official malaya code often uses specific prefix for T5.
    # But let's try raw first.
    
    inputs = tokenizer([input_text], return_tensors="pt")
    
    print(f"🧠 Inference on: '{input_text}'")
    outputs = model.generate(inputs["input_ids"], max_length=50)
    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    
    print(f"📝 Output: '{decoded}'")
    
    if "tidak boleh" in decoded or "tak boleh" in decoded:
        print("✅ SUCCESS: Deep Learning Normalization Working natively!")
    else:
        print("⚠️ Result unexpected (Check prefix/model capability)")

except Exception as e:
    print(f"❌ FAILED: {e}")
