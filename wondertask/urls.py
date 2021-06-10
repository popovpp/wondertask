"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from generic.jwt import CustomJWTSerializer
from rest_framework_jwt.views import (
    ObtainJSONWebToken,
    refresh_jwt_token,
    verify_jwt_token,
)

from accounts.endpoints import registration_endpoint
from tasks.endpoints import task_endpoints
from accounts.endpoints import recover_password_endpoints


authentication_endpoints = [
    path('token/obtaining/', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    path('token/refreshing/', refresh_jwt_token),
    path('token/verification/', verify_jwt_token),
]

v1 = [
    path('authentication/', include(authentication_endpoints)),
    path('openapi/', TemplateView.as_view(template_name='swugger.html')),
    path('accounts/', include(registration_endpoint)),
    path('accounts/', include(recover_password_endpoints)),
    path('tasks/', include(task_endpoints)),

] + static(settings.STATIC_URL)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include(v1)),
] #+ static(settings.STATIC_URL)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
