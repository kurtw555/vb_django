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
from django.urls import path
from django.contrib.staticfiles.views import serve
from .landing import landing
from vb_django.user import UserAPI
from vb_django.locations import LocationAPI
from vb_django.locations_metadata import LocationMetadataAPI
from vb_django.workflow import WorkflowAPI


urlpatterns = [
    path('', landing),
    path('admin/', admin.site.urls),
    path('app/*', serve),

    # ---------- User API endpoints ----------- #
    path('api/user/register/', UserAPI.register),                           # POST
    path('api/user/login/', UserAPI.login),                                 # POST
    path('api/user/passwordreset/', UserAPI.reset_password),                # GET

    # ---------- Location API endpoints ---------- #
    path('api/location/', LocationAPI.get_locations),                       # GET
    path('api/location/add/', LocationAPI.add_location),                    # POST
    path('api/location/update/', LocationAPI.edit_location),                # PUT
    path('api/location/remove/', LocationAPI.delete_location),              # DELETE

    # ---------- Location Metadata API endpoints ----------- #
    path('api/locationmeta/', LocationMetadataAPI.get_metadata),            # GET
    path('api/locationmeta/add/', LocationMetadataAPI.add_metadata),        # POST
    path('api/locationmeta/update/', LocationMetadataAPI.edit_metadata),    # PUT
    path('api/locationmeta/remove/', LocationMetadataAPI.delete_metadata),  # DELETE

    # --------- Workflows API endpoints ---------- #
    path('api/workflow/', WorkflowAPI.get_workflows),                       # GET
    path('api/workflow/add/', WorkflowAPI.add_workflow),                    # POST
    path('api/workflow/update/', WorkflowAPI.edit_workflow),                # PUT
    path('api/workflow/remove/', WorkflowAPI.delete_workflow),              # DELETE

    # --------- Analytical Models API endpoints ---------- #
    # path('api/analyticalmodel/', AnalyticalModelAPI.get_model),           # GET
    # path('api/analyticalmodel/add/', AnalyticalModelAPI.add_model),       # POST
    # path('api/analyticalmodel/update/', AnalyticalModelAPI.edit_model),   # PUT
    # path('api/analyticalmodel/remove/', AnalyticalModelAPI.delete_model), # DELETE
]
