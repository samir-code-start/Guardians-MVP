import logging
# Reserved for future semantic layer - DISABLED FOR HYBRID MVP
# import torch
# import torch.nn.functional as F
from PIL import Image
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Initialize model and processor as None
model = None
processor = None

def load_clip_model():
    """Loads the CLIP model and processor lazily."""
    global model, processor
    if model is not None and processor is not None:
        return True
        
    try:
        from transformers import CLIPProcessor, CLIPVisionModelWithProjection
        # Use a lightweight model for MVP and rapid prototyping
        model_name = "openai/clip-vit-base-patch32"
        logger.info(f"Loading CLIP model '{model_name}'...")
        # Load pre-trained model (no training)
        model = CLIPVisionModelWithProjection.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        # Keep inference lightweight: use evaluation mode
        model.eval()
        return True
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        return False

def generate_embedding(image: Image.Image) -> List[float]:
    """Generates a CLIP embedding for a single image."""
    if not load_clip_model():
        raise RuntimeError("CLIP model is not available.")
        
    try:
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            # Normalize the embedding
            embedding = F.normalize(outputs.image_embeds, p=2, dim=1)
            # Return as a simple list of floats
            return embedding.squeeze().tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    t1 = torch.tensor(vec1)
    t2 = torch.tensor(vec2)
    
    # Calculate cosine similarity using PyTorch
    cos_sim = F.cosine_similarity(t1.unsqueeze(0), t2.unsqueeze(0))
    return float(cos_sim.item())

def compare_deep_features(frames1: List[Image.Image], frames2: List[Image.Image], threshold: float = 0.90) -> Dict[str, Any]:
    """
    Compares two lists of frames using CLIP embeddings.
    Returns the maximum similarity found and a boolean indicating if it's a match.
    """
    if not frames1 or not frames2:
        return {"match": False, "max_similarity": 0.0, "confidence": 0, "matches_count": 0}
        
    embeddings1 = [generate_embedding(f) for f in frames1]
    embeddings2 = [generate_embedding(f) for f in frames2]
    
    max_sim = 0.0
    matches = 0
    
    for emb1 in embeddings1:
        if not emb1:
            continue
            
        best_local_sim = 0.0
        for emb2 in embeddings2:
            if not emb2:
                continue
                
            sim = cosine_similarity(emb1, emb2)
            if sim > best_local_sim:
                best_local_sim = sim
            if sim > max_sim:
                max_sim = sim
                
        if best_local_sim >= threshold:
            matches += 1
            
    # Calculate confidence based on similarity
    confidence = 0
    if max_sim >= threshold:
        # Scale: threshold similarity = 50%, 1.0 similarity = 100%
        # Example: threshold 0.90. sim 0.95 -> 50 + (0.05/0.10)*50 = 75%
        scale_factor = (max_sim - threshold) / (1.0 - threshold + 1e-9)
        confidence = 50 + (scale_factor * 50)
        
    return {
        "match": bool(max_sim >= threshold),
        "max_similarity": float(round(max_sim, 4)),
        "matches_count": int(matches),
        "confidence": max(0, min(100, int(confidence)))
    }
