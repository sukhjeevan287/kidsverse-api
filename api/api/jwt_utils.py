import datetime
import jwt
from django.conf import settings

def generate_jwt_token(parent_id: str) -> str:
    payload = {
        'parent_id': str(parent_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None
