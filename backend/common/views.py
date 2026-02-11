# common/views.py
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.response import Response

@ensure_csrf_cookie
@api_view(["GET"])
def csrf_ping(request):
    return Response({"detail": "ok"})
