# portfolios/views.py
from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from portfolios.models import Portfolio
from portfolios.serializers import (
    PortfolioCreateSerializer,
    PortfolioDetailSerializer,
    PortfolioListSerializer,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_save(request):
    """
    저장(생성)
    - body: PortfolioCreateSerializer 스펙 그대로
    - 성공: 생성된 포트폴리오 상세(JSON) 201
    """
    s = PortfolioCreateSerializer(data=request.data, context={"request": request})
    s.is_valid(raise_exception=True)
    p = s.save()
    out = PortfolioDetailSerializer(p).data
    return Response(out, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_list(request):
    """
    목록
    - 응답: List[PortfolioListSerializer]
    """
    qs = Portfolio.objects.filter(user=request.user)
    data = PortfolioListSerializer(qs, many=True).data
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_detail(request, portfolio_id: int):
    """
    상세
    - 응답: PortfolioDetailSerializer
    """
    p = get_object_or_404(Portfolio.objects.filter(user=request.user), pk=portfolio_id)
    return Response(PortfolioDetailSerializer(p).data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def portfolio_representative(request):
    """
    GET  : 현재 대표 포트폴리오 상세 반환 (없으면 404)
    POST : { "id": <portfolio_id> }로 대표 지정
    """
    if request.method == "GET":
        p = Portfolio.objects.filter(user=request.user, is_representative=True).first()
        if not p:
            return Response({"detail": "대표 포트폴리오가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PortfolioDetailSerializer(p).data, status=status.HTTP_200_OK)

    # POST
    pid = request.data.get("id")
    if not pid:
        return Response({"detail": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    p = get_object_or_404(Portfolio, pk=pid, user=request.user)
    p.set_representative()
    return Response({"ok": True, "id": p.id, "is_representative": p.is_representative}, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def portfolio_update(request, portfolio_id: int):
    """
    수정 (이름, 메모)
    """
    p = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
    
    name = request.data.get("name")
    memo = request.data.get("memo") # Frontend sends 'memo' -> Backend 'rationale'
    
    if name is not None:
        p.name = name
    if memo is not None:
        p.rationale = memo
        
    p.save()
    return Response(PortfolioDetailSerializer(p).data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def portfolio_delete(request, portfolio_id: int):
    """
    삭제
    """
    p = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
    p.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)