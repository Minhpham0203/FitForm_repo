from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User # Import User model mặc định của Django
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------------------------------------------------
# NHÓM 1: USER & PROFILE (UC03, UC04)
# -------------------------------------------------------------------
class Profile(models.Model):
    """ Mở rộng User model mặc định để lưu thông tin thể chất """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Dữ liệu onboarding (UC03)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True) # (e.g., 'male', 'female', 'other')
    activity_level = models.CharField(max_length=20, null=True, blank=True) # (e.g., 'sedentary', 'active')
    
    # Dữ liệu mục tiêu (UC06)
    main_goal = models.CharField(max_length=50, null=True, blank=True) # (e.g., 'lose_weight', 'build_muscle')
    experience_level = models.CharField(max_length=20, null=True, blank=True) # (e.g., 'beginner', 'intermediate')
    days_per_week = models.IntegerField(null=True, blank=True)

    EQUIPMENT_CHOICES = [
        ('bodyweight', 'Chỉ tập Bodyweight'),
        ('basic_gym', 'Cơ bản (Tạ đơn, xà)'),
        ('full_gym', 'Phòng gym đầy đủ'),
    ]

    equipment_available = models.CharField(max_length=20, null=True, blank=True, choices=EQUIPMENT_CHOICES) # (e.g., 'dumbbells, resistance bands')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Tự động tạo Profile khi một User mới được đăng ký (UC01 -> UC03)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# -------------------------------------------------------------------
# NHÓM 5: EXERCISE LIBRARY (UC15, UC17)
# -------------------------------------------------------------------
class Exercise(models.Model):
    """ Thư viện các bài tập (Admin có thể thêm qua Django Admin) """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    video_url = models.URLField(null=True, blank=True)
    muscle_group = models.CharField(max_length=50, db_index=True) # (e.g., 'legs', 'chest', 'back')
    difficulty = models.CharField(max_length=20, null=True, blank=True) # (e.g., 'beginner')
    equipment = models.CharField(max_length=50, null=True, blank=True) # (e.g., 'bodyweight', 'dumbbells')
    movement_pattern = models.CharField(max_length=50, null=True, blank=True) # (e.g., 'squat', 'hinge')
    
    # (UC17) Nếu user tự tạo bài tập, gán user vào đây
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

# -------------------------------------------------------------------
# NHÓM 2: PLAN MANAGEMENT (UC06, UC07)
# -------------------------------------------------------------------
class WorkoutPlan(models.Model):
    """ Kế hoạch tập luyện do user tạo (UC07) hoặc hệ thống gợi ý (UC06) """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    # (Có thể lưu schedule dạng JSON: {"days": ["monday", "wednesday"]})
    schedule = models.JSONField(null=True, blank=True) 

    def __str__(self):
        return f"{self.name} (by {self.user.username})"

class PlanExercise(models.Model):
    """ Bảng trung gian: Một bài tập cụ thể trong một kế hoạch (UC16) """
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='plan_exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.CharField(max_length=20) # (Lưu dạng string "8-12" hoặc "30s")

    day_number  = models.IntegerField(default=1) # Ngày trong tuần của bài tập này (1, 2, ..., 7)

    class Meta:
        unique_together = ('plan', 'exercise', 'day_number') # Không cho thêm 1 bài tập 2 lần vào 1 plan

# -------------------------------------------------------------------
# NHÓM 3: WORKOUT TRACKING (UC09, UC10, UC11)
# -------------------------------------------------------------------
class WorkoutSession(models.Model):
    """ (UC11) Lưu tóm tắt một buổi tập đã hoàn thành """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    plan = models.ForeignKey(WorkoutPlan, null=True, blank=True, on_delete=models.SET_NULL) # Plan đã tập (nếu có)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Dữ liệu tổng kết từ Frontend (UC11)
    total_calories = models.IntegerField(default=0)
    posture_score_avg = models.FloatField(null=True, blank=True) # Điểm tư thế TB (từ UC10)

    def __str__(self):
        return f"Session on {self.start_time.strftime('%Y-%m-%d')} by {self.user.username}"

class ExerciseLog(models.Model):
    """ (UC09, UC10) Lưu chi tiết TỪNG bài tập trong 1 session """
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='logs')
    exercise_name = models.CharField(max_length=100) # Lưu tên, phòng khi Exercise gốc bị xóa
    
    # Dữ liệu tracking (UC09)
    sets_completed = models.IntegerField()
    reps_completed = models.CharField(max_length=50) # (e.g., "12, 10, 8")
    weight_kg = models.CharField(max_length=50, null=True, blank=True) # (e.g., "60, 60, 70")
    
    # Dữ liệu AI (UC10)
    posture_feedback = models.JSONField(null=True, blank=True) # (e.g., {"back_straight": 90, "knee_angle": 85})

# -------------------------------------------------------------------
# NHÓM 6: NUTRITION & HYDRATION (UC19, UC20)
# -------------------------------------------------------------------
class NutritionLog(models.Model):
    """ (UC19) Ghi lại bữa ăn """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_logs')
    food_name = models.CharField(max_length=200)
    calories = models.IntegerField()
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    log_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_name} (by {self.user.username})"

class HydrationLog(models.Model):
    """ (UC20) Ghi lại nước uống """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hydration_logs')
    water_ml = models.IntegerField()
    log_time = models.DateTimeField(auto_now_add=True)