import re
from django.http import JsonResponse
from api.models import Student, Parent
from api.jwt_utils import decode_jwt_token

class StudentOwnershipMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.student_path_regex = re.compile(r'/students/([0-9a-fA-F\-]{36})')

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')
        parent = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = decode_jwt_token(token)
            if payload and 'parent_id' in payload:
                try:
                    parent = Parent.objects.get(id=payload['parent_id'])
                    request.parent = parent
                except Parent.DoesNotExist:
                    pass

        # Check path pattern /students/<student_id>
        match = self.student_path_regex.search(request.path)
        student_id = None
        if match:
            student_id = match.group(1)
        elif request.headers.get('X-Student-Id'):
            student_id = request.headers.get('X-Student-Id')

        if student_id and parent:
            # Check if parent owns this student
            if not Student.objects.filter(id=student_id, parent=parent).exists():
                return JsonResponse({
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Authenticated parent does not own this student",
                        "details": {}
                    }
                }, status=403)

        response = self.get_response(request)
        return response
