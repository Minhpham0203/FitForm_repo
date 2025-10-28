from django.shortcuts import render

# api/views.py
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg
from django_filters import rest_framework as filters
from .models import Profile, Exercise, WorkoutPlan, WorkoutSession, NutritionLog, HydrationLog
from .serializers import (
    ProfileSerializer, 
    ExerciseSerializer, 
    WorkoutPlanSerializer, 
    WorkoutSessionSerializer,
    NutritionLogSerializer,
    HydrationLogSerializer
)
from .utils import calculate_tdee

# --- NHÓM 1: USER & PROFILE (UC03, UC04) ---
# Dùng `RetrieveUpdateAPIView` vì mỗi user chỉ có 1 profile
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint cho phép xem (GET) và cập nhật (PUT/PATCH) 
    profile của user đang đăng nhập.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Trả về đối tượng profile của user đang gọi API
        return self.request.user.profile

# --- NHÓM 5: EXERCISE LIBRARY (NÂNG CẤP) ---
class ExerciseViewSet(viewsets.ModelViewSet): # <-- 1. ĐỔI THÀNH ModelViewSet
    """
    API endpoint cho phép:
    - UC15 (GET): Xem, Lọc, Tìm kiếm Bài tập
    - UC17 (POST): Tạo Bài tập tùy chỉnh
    """
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 2. Thêm các trường Lọc/Tìm kiếm (UC15)
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = [
        'muscle_group', 
        'equipment', 
        'difficulty', 
        'movement_pattern'
    ]
    # (Bạn cũng có thể thêm 'search_fields' nếu muốn tìm kiếm text)
    # search_fields = ['name', 'description'] 

    def perform_create(self, serializer):
        """
        3. Tự động gán user khi tạo (UC17)
        """
        serializer.save(created_by=self.request.user)

# --- NHÓM 2: PLAN MANAGEMENT (UC07) ---
class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép CRUD (Tạo, Đọc, Sửa, Xóa) 
    các kế hoạch tập luyện (WorkoutPlan).
    """
    serializer_class = WorkoutPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Rất quan trọng! Chỉ trả về các plan của user đang đăng nhập.
        Không cho user này xem plan của user khác.
        """
        return WorkoutPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Tự động gán user hiện tại là chủ sở hữu của plan khi tạo.
        """
        serializer.save(user=self.request.user)

    # Template cho các loại buổi tập
    SESSION_TEMPLATES = {
        'Full Body': ['squat', 'hinge', 'horizontal_push', 'horizontal_pull', 'core'],
        'Upper': ['horizontal_push', 'horizontal_pull', 'vertical_push', 'vertical_pull', 'isolation'],
        'Lower': ['squat', 'hinge', 'lunge', 'core'],
        'Push': ['horizontal_push', 'vertical_push', 'isolation'], # Chest, Shoulders, Triceps
        'Pull': ['horizontal_pull', 'vertical_pull', 'isolation'], # Back, Biceps
        'Legs': ['squat', 'hinge', 'lunge', 'core'],
    }


    def _get_structure(self, days, experience):
        """Helper: Quyết định cấu trúc plan (e.g., Full Body, Upper/Lower)"""
        if days <= 2:
            return ['Full Body'] * days
        if days == 3:
            return ['Full Body'] * 3 # (e.g., Full Body A, B, C)
        if days == 4:
            if experience == 'beginner':
                return ['Full Body', 'Full Body', 'Full Body', 'Full Body']
            else:
                return ['Upper', 'Lower', 'Upper', 'Lower']
        if days >= 5:
            if experience == 'beginner':
                return ['Upper', 'Lower', 'Rest', 'Upper', 'Lower'] # 4 ngày
            else:
                # PPL (Push, Pull, Legs)
                return ['Push', 'Pull', 'Legs', 'Push', 'Pull'] # 5 ngày
        return ['Full Body'] # Default

    def _get_sets_reps(self, goal):
        """Helper: Quyết định sets/reps dựa trên mục tiêu"""
        if goal == 'build_muscle':
            return (4, "8-12") # (sets, reps)
        elif goal == 'lose_weight':
            return (3, "12-15")
        else: # maintain
            return (3, "10-12")
    
    def _select_exercise(self, available_pool, pattern):
        """Helper: Chọn một bài tập từ pool theo movement_pattern"""
        exercise = available_pool.filter(movement_pattern=pattern).first()
        return exercise

    # API ENDPOINT
    # ----------------------------------------------------
    
    # Đây là API: GET /api/v1/plans/generate/
    @action(detail=False, methods=['get'])
    def generate(self, request):
        """
        (UC06) Tự động tạo một kế hoạch tập luyện dựa trên
        profile của user.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        # 1. Lấy thông tin đầu vào
        inputs = {
            "goal": profile.main_goal,
            "experience": profile.experience_level,
            "days": profile.days_per_week,
            "equipment": profile.equipment_available,
        }
        
        if not all(inputs.values()):
            return Response(
                {"error": "Profile của bạn chưa hoàn thiện. Cần có đủ: goal, experience, days, equipment."},
                status=400
            )

        # 2. Lấy Pool bài tập có sẵn
        # Đây là lý do Nâng cấp 1 (đồng bộ equipment) quan trọng:
        available_exercise_pool = Exercise.objects.filter(equipment=inputs["equipment"])
        if not available_exercise_pool.exists():
            return Response(
                {"error": f"Không tìm thấy bài tập nào cho dụng cụ: {inputs['equipment']}"},
                status=404
            )

        # 3. Chạy logic
        plan_structure = self._get_structure(inputs["days"], inputs["experience"])
        sets, reps = self._get_sets_reps(inputs["goal"])
        
        final_exercise_list = [] # Đây là list sẽ trả về
        
        # 4. Xây dựng JSON
        for day_index, session_type in enumerate(plan_structure):
            day_number = day_index + 1 # (e.g., 1, 2, 3)
            
            if session_type == 'Rest':
                continue

            # Lấy template cho buổi tập (e.g., ['squat', 'hinge', 'lunge'])
            movement_patterns_for_day = self.SESSION_TEMPLATES.get(session_type, [])
            
            for pattern in movement_patterns_for_day:
                # Chọn 1 bài tập
                exercise = self._select_exercise(available_exercise_pool, pattern)
                
                if exercise:
                    # Tạo JSON cho bài tập này
                    # Nó phải khớp với PlanExerciseSerializer
                    exercise_json = {
                        "exercise_id": exercise.id,
                        "exercise_name": exercise.name, # Thêm tên cho dễ đọc ở frontend
                        "sets": sets,
                        "reps": reps,
                        "day_number": day_number # Đây là lý do Nâng cấp 2 quan trọng
                    }
                    final_exercise_list.append(exercise_json)

        # 5. Tạo JSON cuối cùng (khớp với WorkoutPlanSerializer)
        plan_name = f"Gợi ý: {inputs['goal']} - {inputs['days']} ngày"
        suggested_plan_json = {
            "name": plan_name,
            "description": f"Kế hoạch tự động cho {inputs['experience']} - {inputs['days']} ngày/tuần.",
            "plan_exercises": final_exercise_list
        }

        # Trả về JSON cho Frontend
        return Response(suggested_plan_json)

# --- NHÓM 3: WORKOUT SESSION (UC11, UC13) ---
class WorkoutSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép tạo (POST - UC11) và xem (GET - UC13) 
    các buổi tập (WorkoutSession).
    """
    serializer_class = WorkoutSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Chỉ trả về các session của user đang đăng nhập.
        """
        return WorkoutSession.objects.filter(user=self.request.user).order_by('-start_time')

    def get_serializer_context(self):
        """
        Gửi `request` object vào trong context của serializer.
        Điều này là để `WorkoutSessionSerializer` có thể truy cập
        `self.context['request'].user` trong hàm `create()`.
        """
        return {'request': self.request}

    # Bạn có thể tắt các hành động không dùng đến, ví dụ 'update'
    # http_method_names = ['get', 'post', 'retrieve', 'delete']'

# --- NHÓM 4: PROGRESS VISUALIZATION (UC12) ---
class DashboardView(APIView):
    """
    API endpoint (chỉ GET) để trả về dữ liệu tổng hợp
    cho dashboard (UC12).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        # 1. Lấy dữ liệu từ Profile (cho BMI)
        current_weight = profile.weight_kg or 0
        current_height_m = (profile.height_cm or 100) / 100
        current_bmi = 0
        if current_height_m > 0:
            current_bmi = round(current_weight / (current_height_m ** 2), 1)

        # 2. Lấy dữ liệu tổng hợp từ các Session
        user_sessions = WorkoutSession.objects.filter(user=user)
        
        total_calories = user_sessions.aggregate(
            total=Sum('total_calories')
        )['total'] or 0
        
        avg_posture = user_sessions.aggregate(
            avg=Avg('posture_score_avg')
        )['avg'] or 0
        
        total_workouts = user_sessions.count()

        # (Logic cho "Streak" và "Adherence %" phức tạp hơn, 
        # bạn có thể thêm sau, chúng đòi hỏi phân tích ngày tháng)

        # 3. Đóng gói JSON trả về
        dashboard_data = {
            "current_bmi": current_bmi,
            "total_calories_burnt": total_calories,
            "total_workouts": total_workouts,
            "average_posture_score": round(avg_posture, 1),
            "streak": 0, # (Để tạm)
            "adherence_percent": 0 # (Để tạm)
        }
        
        return Response(dashboard_data)
    
# --- NHÓM 6: NUTRITION & HYDRATION (UC19, UC20) ---

class NutritionLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép CRUD (Tạo, Đọc, Sửa, Xóa) 
    các log dinh dưỡng (NutritionLog).
    """
    serializer_class = NutritionLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Chỉ trả về log của user đang đăng nhập.
        """
        return NutritionLog.objects.filter(user=self.request.user).order_by('-log_date')

    def perform_create(self, serializer):
        """
        Tự động gán user khi tạo log mới.
        """
        serializer.save(user=self.request.user)

class HydrationLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép CRUD (chủ yếu là POST và GET)
    cho log Nước uống (HydrationLog).
    """
    serializer_class = HydrationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Chỉ cho phép các phương thức này, tránh PUT/PATCH không cần thiết
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """
        Chỉ trả về log của user đang đăng nhập.
        """
        return HydrationLog.objects.filter(user=self.request.user).order_by('-log_time')

    def perform_create(self, serializer):
        """
        Tự động gán user khi tạo log mới.
        """
        serializer.save(user=self.request.user)


# --- NHÓM 6: NUTRITION (UC18) ---
class MealSuggestionView(APIView):
    """
    API endpoint (chỉ GET) để gợi ý bữa ăn (UC18).
    """
    permission_classes = [IsAuthenticated]

    # (Dán hàm calculate_tdee vào đây nếu bạn không tạo file utils.py)
    
    MEAL_TEMPLATES = [
        # ---
        # 1. TEMPLATES CHO "GIẢM MỠ" (lose_weight)
        # ---
        {
            'name': 'Giảm mỡ - 1600 Cal',
            'goal_type': 'lose_weight',
            'target_calories': 1600,
            'macros': {'protein_g': 150, 'carbs_g': 120, 'fat_g': 53},
            'meals': {
                'breakfast': {'name': 'Trứng luộc (3) & Rau bina', 'calories': 300},
                'lunch': {'name': 'Salad Ức gà (150g) & Hạt diêm mạch (Quinoa)', 'calories': 450},
                'snack': {'name': 'Sữa chua Hy Lạp (0% béo) & Hạt', 'calories': 200},
                'dinner': {'name': 'Cá tuyết (Cod) áp chảo & Súp lơ xanh', 'calories': 650},
            }
        },
        {
            'name': 'Giảm mỡ - 2000 Cal',
            'goal_type': 'lose_weight',
            'target_calories': 2000,
            'macros': {'protein_g': 180, 'carbs_g': 180, 'fat_g': 62},
            'meals': {
                'breakfast': {'name': 'Yến mạch (Oatmeal) & Whey Protein', 'calories': 450},
                'lunch': {'name': 'Bò nạc (150g) xào & Cơm lứt (1 bát)', 'calories': 600},
                'snack': {'name': 'Táo & Bơ đậu phộng', 'calories': 300},
                'dinner': {'name': 'Ức gà (200g) nướng & Khoai lang', 'calories': 650},
            }
        },
        # ---
        # 2. TEMPLATES CHO "DUY TRÌ" (maintain)
        # ---
        {
            'name': 'Duy trì - 2200 Cal (Cân bằng)',
            'goal_type': 'maintain',
            'target_calories': 2200,
            'macros': {'protein_g': 165, 'carbs_g': 220, 'fat_g': 73},
            'meals': {
                'breakfast': {'name': 'Bánh mì đen, Trứng ốp la (2) & Bơ', 'calories': 500},
                'lunch': {'name': 'Cơm tấm sườn bì chả (1 đĩa)', 'calories': 700},
                'snack': {'name': 'Trái cây & Hạt hỗn hợp', 'calories': 300},
                'dinner': {'name': 'Heo nạc xào rau củ & Cơm trắng (1 bát)', 'calories': 700},
            }
        },
        {
            'name': 'Duy trì - 2500 Cal (Cân bằng)',
            'goal_type': 'maintain',
            'target_calories': 2500,
            'macros': {'protein_g': 188, 'carbs_g': 250, 'fat_g': 83},
            'meals': {
                'breakfast': {'name': 'Phở bò (1 tô lớn)', 'calories': 600},
                'lunch': {'name': 'Cá hồi (150g), Cơm & Salad', 'calories': 800},
                'snack': {'name': 'Sữa chua & Granola', 'calories': 400},
                'dinner': {'name': 'Ức gà (200g) & Măng tây (thêm dầu olive)', 'calories': 700},
            }
        },
        # ---
        # 3. TEMPLATES CHO "TĂNG CƠ" (build_muscle)
        # ---
        {
            'name': 'Tăng cơ - 2800 Cal',
            'goal_type': 'build_muscle',
            'target_calories': 2800,
            'macros': {'protein_g': 210, 'carbs_g': 300, 'fat_g': 88},
            'meals': {
                'breakfast': {'name': 'Yến mạch, Sữa, Chuối & Whey Protein', 'calories': 700},
                'lunch': {'name': 'Bò bít tết (200g) & Khoai tây nghiền', 'calories': 800},
                'snack': {'name': 'Bánh mì kẹp Bơ đậu phộng & Mứt', 'calories': 400},
                'dinner': {'name': 'Ức gà (200g), Pasta & Sốt cà chua', 'calories': 900},
            }
        },
        {
            'name': 'Tăng cơ - 3200 Cal',
            'goal_type': 'build_muscle',
            'target_calories': 3200,
            'macros': {'protein_g': 240, 'carbs_g': 350, 'fat_g': 107},
            'meals': {
                'breakfast': {'name': 'Trứng (4), Xúc xích (2), Bánh mì (2 lát) & Bơ', 'calories': 800},
                'lunch': {'name': 'Bò xào (200g) & Cơm trắng (2 bát)', 'calories': 1000},
                'snack': {'name': 'Hạt hỗn hợp (1 nắm lớn) & Sữa chua', 'calories': 500},
                'dinner': {'name': 'Cá hồi (200g), Cơm & Rau (thêm dầu olive)', 'calories': 900},
            }
        }
    ]

    # === THAY THẾ HÀM 'get' CŨ BẰNG HÀM NÀY ===
    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        if not all([profile.weight_kg, profile.height_cm, profile.age, profile.gender, profile.activity_level, profile.main_goal]):
            return Response(
                {"error": "Profile của bạn chưa hoàn thiện. Cần có đủ thông tin cơ bản và mục tiêu."},
                status=400
            )

        # 1. Tính TDEE (calo duy trì)
        tdee = calculate_tdee(profile) # (Hoặc self.calculate_tdee(profile))

        # 2. Tính Calo Mục tiêu (Calorie Target)
        calories_target = tdee
        user_goal = profile.main_goal
        
        if user_goal == 'lose_weight':
            calories_target -= 400 # Thâm hụt 400 cal
        elif user_goal == 'build_muscle':
            calories_target += 300 # Thặng dư 300 cal
        # (Nếu là 'maintain', calo giữ nguyên)

        # 3. Lọc các template theo mục tiêu của user
        goal_templates = [
            template for template in self.MEAL_TEMPLATES 
            if template['goal_type'] == user_goal
        ]
        
        if not goal_templates:
            # Dự phòng: Nếu không có template cho mục tiêu, dùng 'maintain'
            goal_templates = [
                template for template in self.MEAL_TEMPLATES 
                if template['goal_type'] == 'maintain'
            ]

        # 4. Tìm template có calo "gần nhất" với calo mục tiêu
        # Dùng hàm `min` với key là chênh lệch tuyệt đối
        best_match_template = min(
            goal_templates, 
            key=lambda x: abs(x['target_calories'] - calories_target)
        )

        # 5. Tạo response
        # Copy template để tránh thay đổi bản gốc
        response_data = best_match_template.copy() 
        
        # Thêm thông tin tính toán của user vào
        response_data['user_info'] = {
            'calculated_tdee': tdee,
            'calculated_target_calories': calories_target
        }

        return Response(response_data)