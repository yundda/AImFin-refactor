from django.urls import path
from . import views

urlpatterns = [
    path("save", views.portfolio_save, name="portfolio.save"),  # POST /api/portfolio/save
    path("list", views.portfolio_list, name="portfolio.list"),  # GET /api/portfolio/list
    path("representative", views.portfolio_representative, name="portfolio.representative"),  # GET/POST
    path("<int:portfolio_id>", views.portfolio_detail, name="portfolio.detail"),  # GET /api/portfolio/{id}
    path("<int:portfolio_id>/update", views.portfolio_update, name="portfolio.update"),  # PATCH
    path("<int:portfolio_id>/delete", views.portfolio_delete, name="portfolio.delete"),  # DELETE
]
