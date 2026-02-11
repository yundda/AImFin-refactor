from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

class SwaggerCSPView(SpectacularSwaggerView):
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        resp['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:"
        )
        return resp

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SwaggerCSPView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/users/", include("users.urls")),
    path("api/assets/", include("assets.urls")),
    path("api/portfolios/", include("portfolios.urls")),
    path("api/analysis/", include("analysis.urls")),
]
