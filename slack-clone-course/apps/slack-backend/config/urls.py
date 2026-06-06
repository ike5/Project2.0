"""Root URL configuration. API routes are mounted under /api/ by each app's router."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    """Liveness probe target (used by Docker/K8s in Modules 12–15)."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),       # Module 03
    path("api/", include("workspaces.urls")),          # Module 04
    path("api/", include("chat.urls")),                # Module 04
    path("api/webhooks/", include("webhooks.urls")),   # Module 08
    # OpenAPI schema + Swagger UI (Module 04)
    path("api/schema/", include("config.schema_urls")),
]
