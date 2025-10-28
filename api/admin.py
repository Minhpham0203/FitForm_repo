from django.contrib import admin

from django.contrib import admin
from .models import (
    Profile, 
    Exercise, 
    WorkoutPlan, 
    PlanExercise, 
    WorkoutSession, 
    ExerciseLog, 
    NutritionLog, 
    HydrationLog
)

# Đăng ký các models của bạn tại đây
# Cách 1: Đăng ký cơ bản (dễ nhất)
admin.site.register(Profile)
admin.site.register(Exercise)
admin.site.register(WorkoutPlan)
admin.site.register(PlanExercise)
admin.site.register(WorkoutSession)
admin.site.register(ExerciseLog)
admin.site.register(NutritionLog)
admin.site.register(HydrationLog)
