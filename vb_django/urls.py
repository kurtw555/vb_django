"""vb_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.views import serve
from rest_framework import permissions, routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .landing import landing
from vb_django.user_views import UserView, UserLoginView
from vb_django.locations_views import LocationView
from vb_django.workflow_views import WorkflowView
from vb_django.analytical_model_views import AnalyticalModelView
from vb_django.dataset_views import DatasetView


schema_view = get_schema_view(
    openapi.Info(
        title="Virtual Beach Web API",
        default_version='v1',
        description="Swagger documentation for Virtual Beavh REST API endpoints",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)
)

router = routers.SimpleRouter()
# ---------- Location API endpoints ---------- #
router.register('location', LocationView, basename='location')
# --------- Workflows API endpoints ---------- #
router.register('workflow', WorkflowView, basename='workflow')
# ------ Analytical Model API endpoints ------ #
router.register('analyticalmodel', AnalyticalModelView, basename='analyticalmodel')
# --------- Dataset API endpoints ---------- #
router.register('dataset', DatasetView, basename='dataset')


urlpatterns = [
    path('', landing),
    path('admin/', admin.site.urls),
    path('app/*', serve),

    # ----------- Swagger Docs/UI ------------- #
    # re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # ---------- User API endpoints ----------- #
    path('api/user/login/', UserLoginView.as_view()),                           # POST
    path('api/user/register/', UserView.as_view()),       # POST

    # ------ ADD the DRF urls registered to the router ------ #
    path('api/', include(router.urls)),

    # ---------- Location Metadata API endpoints ----------- #
    # path('api/locationmeta/', LocationMetadataAPI.get_metadata),            # GET
    # path('api/locationmeta/add/', LocationMetadataAPI.add_metadata),        # POST
    # path('api/locationmeta/update/', LocationMetadataAPI.edit_metadata),    # PUT
    # path('api/locationmeta/remove/', LocationMetadataAPI.delete_metadata),  # DELETE

]
