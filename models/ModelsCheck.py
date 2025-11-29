from sentence_transformers import SentenceTransformer
import os

# Create folder if not exists
save_path = os.path.join("models", "sentence_transformers", "all-MiniLM-L6-v2")
os.makedirs(save_path, exist_ok=True)

# Download and save model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.save(save_path)

print(f"✅ Model downloaded and saved successfully to: {save_path}")
exit()
