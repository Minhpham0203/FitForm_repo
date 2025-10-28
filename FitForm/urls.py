"""
URL configuration for FitForm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

urlpatterns = [
    # 1. URL cho trang Admin của Django
    path('admin/', admin.site.urls),
    
    # 2. URL cho API Xác thực (UC01, UC02) - Cung cấp bởi dj-rest-auth
    # Sẽ tạo ra:
    # /api/v1/auth/login/
    # /api/v1/auth/logout/
    # /api/v1/auth/registration/
    # ...
    path('api/v1/auth/', include('dj_rest_auth.urls')),
    path('api/v1/auth/registration/', include('dj_rest_auth.registration.urls')),

    # 3. URL cho các API nghiệp vụ của bạn (UC03 -> UC20)
    # "Bất cứ URL nào bắt đầu bằng /api/v1/ hãy chuyển tiếp đến file api.urls"
    path('api/v1/', include('api.urls')),
]