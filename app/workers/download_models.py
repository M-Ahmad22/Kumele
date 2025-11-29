from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from transformers import AutoModelForImageClassification, ViTImageProcessor

# 1. Updated Text Classification model
model_name_text = "facebook/roberta-hate-speech-dynabench-r4-target"
tokenizer_text = AutoTokenizer.from_pretrained(model_name_text)
model_text = AutoModelForSequenceClassification.from_pretrained(model_name_text)
print(f"Text model {model_name_text} downloaded successfully!")

# 2. ViT model (Image Classification)
vit_model_name = "google/vit-base-patch16-224"
processor_vit = ViTImageProcessor.from_pretrained(vit_model_name)
model_vit = AutoModelForImageClassification.from_pretrained(vit_model_name)
print(f"Image model {vit_model_name} downloaded successfully!")

# Optional: Test pipeline
text_pipe = pipeline(
    "text-classification",
    model=model_text,
    tokenizer=tokenizer_text,
    return_all_scores=True
)
print("Pipeline test successful!")
