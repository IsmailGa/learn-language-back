import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str | Any) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_telegram_data(init_data: str, bot_token: str) -> dict | bool:
    """
    Validates the data received from the Telegram web app.
    """
    from urllib.parse import parse_qs, unquote
    
    try:
        parsed_data = parse_qs(init_data)
        hash_value = parsed_data.pop('hash', [None])[0]
        
        data_check_string = "\n".join([f"{k}={v[0]}" for k, v in sorted(parsed_data.items())])
        
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == hash_value:
            import json
            return json.loads(parsed_data['user'][0])
        return False
    except Exception:
        return False

def verify_telegram_widget_data(data: dict, bot_token: str) -> bool:
    """
    Validates the data received from the Telegram Login Widget.
    """
    try:
        data = data.copy()
        hash_value = data.pop('hash')
        
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
        
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == hash_value
    except Exception:
        return False