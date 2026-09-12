from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from api.models import Parent
from api.jwt_utils import decode_jwt_token

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        payload = decode_jwt_token(token)
        if not payload or 'parent_id' not in payload:
            raise AuthenticationFailed("Invalid or expired token")

        try:
            parent = Parent.objects.get(id=payload['parent_id'])
        except Parent.DoesNotExist:
            raise AuthenticationFailed("Parent account not found")

        request.parent = parent
        request.user = parent
        return (parent, token)
