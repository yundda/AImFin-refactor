from django.urls import path
from rest_framework.decorators import api_view
from . import views
from analysis import views_recommend,views_rebalance, views_compare


urlpatterns = [
    path("compare", views.compare, name="analysis.compare"),  # POST /api/analysis/compare
    path("analyze", views.single_analyze, name="analysis.analyze"),  # POST /api/analysis/analyze
    path("survey_analyze", views.survey_analyze, name="analysis.survey_analyze"),  # POST

    path("recommend/portfolio", views_recommend.recommend, name="recommend-portfolio"),
    path("rebalance/portfolio/<int:portfolio_id>", views_rebalance.rebalance, name="analysis.rebalance"),
    path("compare/portfolio", views_compare.compare_portfolio, name="analysis.compare.portfolio"),
]