from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import numpy as np
from app.db.database import SessionLocal
from app.db.models import Event

MODEL_PATH = "models/sentence_transformers/all-MiniLM-L6-v2"
FINETUNED_PATH = "models/sentence_transformers/all-MiniLM-L6-v2-finetuned"

# Load base model
model = SentenceTransformer(MODEL_PATH)

# Fetch synthetic data from DB
db = SessionLocal()
events = db.query(Event).all()
synthetic_texts = [e.description for e in events if e.description]

# Create InputExamples (we can set all labels to 1.0 for semantic fine-tuning)
train_examples = [InputExample(texts=[txt], label=1.0) for txt in synthetic_texts]

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
train_loss = losses.CosineSimilarityLoss(model)

print(f"Training on {len(train_examples)} examples...")
model.fit(train_objectives=[(train_dataloader, train_loss)], epochs=1, warmup_steps=10)

# Save fine-tuned model
model.save(FINETUNED_PATH)
print(f"✅ Fine-tuned model saved at {FINETUNED_PATH}")
db.close()
