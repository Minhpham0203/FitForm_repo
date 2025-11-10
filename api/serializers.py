# api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
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
# (Bỏ qua NutritionLog và HydrationLog cho ngắn gọn, bạn có thể tự thêm sau)

# --- NHÓM 1: USER & PROFILE ---

class ProfileSerializer(serializers.ModelSerializer):
    """ Dịch Profile cho UC03, UC04 """
    
    # Lấy email từ User model liên quan
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Profile
        # Các trường bạn cho phép Frontend xem/cập nhật
        fields = [
            'username', 'email', 'height_cm', 'weight_kg', 
            'age', 'gender', 'activity_level', 'main_goal', 'experience_level',
            'days_per_week',
            'equipment_available'
    
        ]
        read_only_fields = ['username', 'email'] # User không thể đổi username/email qua đây

# --- NHÓM 5: EXERCISE LIBRARY ---

class ExerciseSerializer(serializers.ModelSerializer):
    """ Dịch Exercise cho UC15 (Chỉ đọc) """
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'description', 'video_url', 
            'muscle_group', 'difficulty', 'equipment', 'movement_pattern'
        ]

class ExcersiseGuideSerializer(serializers.ModelSerializer):
    """ 
    Serializer "gọn nhẹ" chỉ trả về video_url và description.
    """
    class Meta:
        model = Exercise
        fields = ['description', 'video_url']

# --- NHÓM 2: PLAN MANAGEMENT (Phức tạp hơn) ---

class PlanExerciseSerializer(serializers.ModelSerializer):
    """ Dịch chi tiết bài tập TRONG một kế hoạch (UC07) """
    # Gửi ID của bài tập khi tạo/sửa
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(), source='exercise'
    )
    # Gửi tên bài tập khi đọc
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = PlanExercise
        fields = ['id', 'exercise_id', 'exercise_name', 'sets', 'reps', 'day_number']

class WorkoutPlanSerializer(serializers.ModelSerializer):
    """ Dịch Kế hoạch tập luyện (UC07) """
    
    # 'plan_exercises' là `related_name` ta đặt trong models.py
    # Dùng nested serializer (serializer lồng nhau)
    plan_exercises = PlanExerciseSerializer(many=True)

    class Meta:
        model = WorkoutPlan
        fields = ['id', 'name', 'description', 'schedule', 'plan_exercises']

    def create(self, validated_data):
        # Tách dữ liệu lồng (nested data) ra
        exercises_data = validated_data.pop('plan_exercises')
        
        # 1. Tạo đối tượng cha (WorkoutPlan)
        plan = WorkoutPlan.objects.create(**validated_data)
        
        # 2. Tạo các đối tượng con (PlanExercise)
        for exercise_data in exercises_data:
            PlanExercise.objects.create(plan=plan, **exercise_data)
        return plan

    def update(self, instance, validated_data):
        # (Logic update phức tạp hơn, tạm thời bỏ qua cho dự án 2 tuần)
        # (Nếu bạn muốn, logic là: Xóa hết PlanExercise cũ, tạo lại cái mới)
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.schedule = validated_data.get('schedule', instance.schedule)
        instance.save()
        
        # (Đây là logic update đơn giản)
        if 'plan_exercises' in validated_data:
            exercises_data = validated_data.pop('plan_exercises')
            instance.plan_exercises.all().delete() # Xóa cũ
            for exercise_data in exercises_data: # Tạo mới
                PlanExercise.objects.create(plan=instance, **exercise_data)
                
        return instance

# --- NHÓM 3: WORKOUT SESSION (Quan trọng nhất) ---

class ExerciseLogSerializer(serializers.ModelSerializer):
    """ Dịch chi tiết log của TỪNG bài tập (UC09, UC10) """
    class Meta:
        model = ExerciseLog
        # Đây là các trường Frontend gửi lên (từ Hợp đồng API)
        fields = [
            'exercise_name', 'sets_completed', 'reps_completed', 
            'weight_kg', 'posture_feedback'
        ]

class WorkoutSessionSerializer(serializers.ModelSerializer):
    """ Dịch TOÀN BỘ buổi tập (UC11) """
    
    # 'logs' là `related_name` trong model WorkoutSession
    # Đây là nơi nhận mảng JSON 'logs' từ Hợp đồng API
    logs = ExerciseLogSerializer(many=True)

    class Meta:
        model = WorkoutSession
        fields = [
            'id', 'plan', 'start_time', 'end_time', 
            'total_calories', 'posture_score_avg', 'logs'
        ]

    def create(self, validated_data):
        # Lấy user từ context (sẽ được inject từ View)
        user = self.context['request'].user
        
        # Tách dữ liệu lồng
        logs_data = validated_data.pop('logs')
        
        # 1. Tạo đối tượng cha (WorkoutSession)
        session = WorkoutSession.objects.create(user=user, **validated_data)
        
        # 2. Tạo các đối tượng con (ExerciseLog)
        for log_data in logs_data:
            ExerciseLog.objects.create(session=session, **log_data)
            
        return session  

# --- NHÓM 6: NUTRITION & HYDRATION ---

class NutritionLogSerializer(serializers.ModelSerializer):
    """
    Dịch NutritionLog (UC19)
    Trường 'user' sẽ được xử lý tự động ở View.
    """
    
    # Hiển thị user_id khi GET, nhưng không cho phép ghi đè khi POST
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = NutritionLog
        fields = [
            'id', 'user_id', 'food_name', 'calories', 
            'protein_g', 'carbs_g', 'fat_g', 'log_date'
        ]
        # Đảm bảo 'log_date' là chỉ đọc, vì nó được gán tự động
        read_only_fields = ['id', 'user_id', 'log_date']

class HydrationLogSerializer(serializers.ModelSerializer):
    """
    Dịch HydrationLog (UC20)
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = HydrationLog
        fields = ['id', 'user_id', 'water_ml', 'log_time']
        read_only_fields = ['id', 'user_id', 'log_time']