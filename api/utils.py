from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import exception_handler

def hash_password(password: str) -> str:
    return make_password(password)

def verify_password(password: str, password_hash: str) -> bool:
    return check_password(password, password_hash)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        code_map = {
            400: "VALIDATION_ERROR",
            401: "AUTHENTICATION_FAILED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            500: "INTERNAL_SERVER_ERROR",
        }
        error_code = code_map.get(response.status_code, "ERROR")
        
        message = "An error occurred."
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
            else:
                messages = []
                for k, v in response.data.items():
                    if isinstance(v, list):
                        messages.append(f"{k}: {v[0]}")
                    else:
                        messages.append(f"{k}: {v}")
                message = ", ".join(messages) if messages else "Validation failed"
        elif isinstance(response.data, list):
            message = ", ".join([str(item) for item in response.data])

        response.data = {
            "error": {
                "code": error_code,
                "message": message,
                "details": context.get('kwargs', {})
            }
        }
    return response
