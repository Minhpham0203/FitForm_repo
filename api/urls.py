# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Import file views.py của bạn

# DefaultRouter tự động tạo ra các URL cho ViewSet
# (Ví dụ: GET /plans/, POST /plans/, GET /plans/1/, PUT /plans/1/, ...)
router = DefaultRouter()

# Đăng ký các ViewSet của bạn với router
# router.register(r'tên-url', views.TênViewSet, basename='tên-dùng-nội-bộ')
router.register(r'exercises', views.ExerciseViewSet, basename='exercise')
router.register(r'plans', views.WorkoutPlanViewSet, basename='plan')
router.register(r'sessions', views.WorkoutSessionViewSet, basename='session')
router.register(r'nutrition-logs', views.NutritionLogViewSet, basename='nutrition-log')
router.register(r'hydration-logs', views.HydrationLogViewSet, basename='hydration-log')

# urlpatterns là danh sách URL cuối cùng
urlpatterns = [
    # Các URL do Router tự động tạo ra
    path('', include(router.urls)),
    
    # Đăng ký ProfileView (vì nó không phải ViewSet, ta đăng ký thủ công)
    # Nó sẽ tạo ra: GET /api/v1/profile/ và PUT /api/v1/profile/
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # URL cho Dashboard (UC12)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('nutrition/suggest/', views.MealSuggestionView.as_view(), name='meal-suggestion')
]