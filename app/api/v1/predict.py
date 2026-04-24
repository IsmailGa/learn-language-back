import base64
import json
import logging
import os
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import cv2
import torch

# Ensure the 'ai' directory is in the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))
try:
    from ai.model import CharacterCNN
except ImportError:
    # Fallback if path logic varies
    from ai.model import CharacterCNN

router = APIRouter()
# Model weights updated - triggering reload
logger = logging.getLogger(__name__)

class PredictRequest(BaseModel):
    image: str

# --- Module Global State for Model ---
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai/weights/character_model.pth"))
_model = None

# Mapping classes to characters
CHAR_MAP = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ"]

def get_model():
    global _model
    if _model is not None:
        return _model
    
    # Initialize architecture
    _model = CharacterCNN(num_classes=len(CHAR_MAP))
    
    if os.path.exists(MODEL_PATH):
        try:
            state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True)
            _model.load_state_dict(state_dict)
            _model.eval()
            logger.info("AI Model loaded successfully from weights/character_model.pth")
        except Exception as e:
            logger.error(f"Failed to load AI model weights: {e}")
            _model = None # Reset to prevent crash but allow re-attempt
    else:
        logger.warning(f"AI weights not found at {MODEL_PATH}. Model will return mock results.")
        _model = None
        
    return _model

@router.post("")
async def predict_character(request: PredictRequest):
    try:
        # Extract base64 part
        if "," in request.image:
            header, encoded = request.image.split(",", 1)
        else:
            encoded = request.image
        
        # Decode base64 to numpy array
        try:
            image_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
            
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
            
        # --- Preprocessing ---
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # The frontend sends a white background with black strokes.
        # We need to invert this to black background and white strokes for EMNIST.
        # THRESH_BINARY_INV with threshold ~200 will turn white bg -> 0, black ink -> 255
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        coords = cv2.findNonZero(thresh)
        
        if coords is None:
            return {"prediction": "Empty", "confidence": 0, "success": False}
            
        x, y, w, h = cv2.boundingRect(coords)
        cropped = thresh[y:y+h, x:x+w]
        size = max(w, h)
        pad_h, pad_w = (size - h) // 2, (size - w) // 2
        
        square = cv2.copyMakeBorder(cropped, pad_h, size-h-pad_h, pad_w, size-w-pad_w, cv2.BORDER_CONSTANT, value=0)
        margin = int(size * 0.1)
        square_with_margin = cv2.copyMakeBorder(square, margin, margin, margin, margin, cv2.BORDER_CONSTANT, value=0)
        resized = cv2.resize(square_with_margin, (28, 28), interpolation=cv2.INTER_AREA)
        
        # --- Real AI Inference ---
        model = get_model()
        if model is not None:
            # Convert to torch tensor [Batch, Channel, Height, Width]
            input_tensor = torch.from_numpy(resized).float().unsqueeze(0).unsqueeze(0) / 255.0
            input_tensor = (input_tensor - 0.5) / 0.5 # Match EMNIST normalization
            
            with torch.no_grad():
                output = model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                confidence, class_idx = torch.max(probabilities, 1)
                
            prediction = CHAR_MAP[class_idx.item()]
            return {
                "prediction": prediction,
                "confidence": float(confidence.item()),
                "success": True
            }
        else:
            # Mock fallback if model weights missing
            return {
                "prediction": "A", 
                "confidence": 0.5,
                "success": False,
                "message": "Model weights missing, please train AI."
            }
        
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trigger reload 


# Trigger reload 


# reload v3

