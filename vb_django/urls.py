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
from django.urls import path, include, re_path
from django.contrib.staticfiles.views import serve
# from django.views.generic import TemplateView
from rest_framework import permissions, routers
from drf_yasg.views import get_schema_view
# from rest_framework.schemas import get_schema_view
from drf_yasg import openapi
from .landing import landing
from vb_django.views.user_views import UserView, UserLoginView
from vb_django.views.locations_views import LocationView
from vb_django.views.workflow_views import WorkflowView
from vb_django.views.analytical_model_views import AnalyticalModelView
from vb_django.views.dataset_views import DatasetView
from vb_django.views.preprocessing_views import PreProcessingConfigView
from vb_django.views.utilities_views import analytical_model_details


router = routers.SimpleRouter()
# ---------- Location API endpoints ---------- #
router.register('location', LocationView, basename='location')
# --------- Workflows API endpoints ---------- #
router.register('workflow', WorkflowView, basename='workflow')
# ------ Analytical Model API endpoints ------ #
router.register('analyticalmodel', AnalyticalModelView, basename='analyticalmodel')
# --------- Dataset API endpoints ---------- #
router.register('dataset', DatasetView, basename='dataset')
# --------- PreprocessingConfig API API endpoints ---------- #
router.register('preprocessing', PreProcessingConfigView, basename='preprocessing')


schema_view = get_schema_view(
    openapi.Info(
        title="Virtual Beach Web API",
        description="Open API documentation for the Virtual Beach REST Web API",
        default_version="0.0.1",
    ),
    patterns=router.urls,
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', landing),
    path('admin/', admin.site.urls),
    path('app/*', serve),

    # ----------- Swagger Docs/UI ------------- #
    # path('swagger/', TemplateView.as_view(
    #     template_name='swagger-ui.html',
    #     extra_context={'schema_url': 'openapi-schema'}
    # ), name='swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('swagger/', schema_view, name='openapi-schema'),

    # ---------- User API endpoints ----------- #
    path('api/user/login/', UserLoginView.as_view()),                           # POST
    path('api/user/register/', UserView.as_view()),       # POST

    # ------ ADD the DRF urls registered to the router ------ #
    path('api/', include(router.urls)),

    path('info/analyticalmodels/', analytical_model_details),

]

