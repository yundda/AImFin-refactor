from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["POST"])
# @permission_classes([AllowAny])
def compare(request):
    return Response({"api": "analysis.compare", "echo": request.data})

@api_view(["POST"])
# @permission_classes([AllowAny])
def single_analyze(request):
    return Response({"api": "analysis.analyze", "echo": request.data})

@api_view(["POST"])
# @permission_classes([AllowAny])
def survey_analyze(request):
    return Response({"api": "analysis.survey_analyze", "echo": request.data})
