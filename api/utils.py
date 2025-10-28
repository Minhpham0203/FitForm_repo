# api/utils.py (File mới)
def calculate_tdee(profile):
    """
    Tính TDEE (calo duy trì) dùng công thức Harris-Benedict (đơn giản).
    """
    if not all([profile.weight_kg, profile.height_cm, profile.age, profile.gender]):
        return 2000 # Trả về một giá trị mặc định

    # 1. Tính BMR (Basal Metabolic Rate)
    if profile.gender == 'male':
        bmr = 88.362 + (13.397 * profile.weight_kg) + (4.799 * profile.height_cm) - (5.677 * profile.age)
    else: # 'female' or 'other'
        bmr = 447.593 + (9.247 * profile.weight_kg) + (3.098 * profile.height_cm) - (4.330 * profile.age)

    # 2. Tính TDEE
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    multiplier = activity_multipliers.get(profile.activity_level, 1.2)
    tdee = bmr * multiplier

    return int(tdee)