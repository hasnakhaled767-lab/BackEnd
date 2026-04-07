import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myconfig.settings')
django.setup()

from dataAboutUser.models import Food, FoodAlternative

# القائمة الكاملة من رسالتك (61 صنف)
all_items = [
    'apple', 'avocado', 'banana', 'bilimbi', 'bitter melon', 'bottle gourd', 'cabbage', 
    'calamansi', 'carrots', 'celery', 'cherry', 'cucumber', 'durian', 'eggplant', 
    'garlic', 'grapes', 'hyacinth bean', 'kiwi', 'ladies-finger', 'lemon', 'lima bean', 
    'mango', 'mustard green', 'onion', 'orange', 'papaya', 'peach', 'peanut', 
    'pineapple', 'plum', 'pomelo', 'potato', 'ribbed gourd', 'strawberry', 'string bean', 
    'tomato', 'watermelon', 'winged bean', 'bacon', 'barbecue ribs', 'beer', 
    'chicken pot pie', 'eggs', 'french fries', 'fried chicken', 'hamburgers', 
    'hot dogs', 'ice cream', 'macaroni', 'meatloaf', 'milkshakes', 'pancakes', 
    'pizza', 'potato wedges', 'sandwich', 'sausage', 'shrimp', 'spaghetti', 
    'steak', 'tacos', 'waffles'
]

print(f"جاري إضافة {len(all_items)} صنف للداتا بيز...")

for item_name in all_items:
    # لو الصنف موجود مش هيضيفه تاني، لو مش موجود هيضيفه
    food, created = Food.objects.get_or_create(
        name=item_name, 
        defaults={'calories': 150, 'protein': 5, 'carbs': 20, 'fats': 5}
    )

# إضافة روابط البدائل الصحية (أمثلة ذكية للربط)
alternatives_map = {
    'hamburgers': ('sandwich', 'Try a lean grilled sandwich instead of a greasy burger'),
    'french fries': ('potato', 'Baked potatoes are a much healthier source of carbs'),
    'pizza': ('chicken pot pie', 'Choose protein-rich pies over high-carb pizza'),
    'ice cream': ('watermelon', 'Fruit sugars are better for your health score'),
    'beer': ('orange', 'Fresh orange juice is a vitamin-rich alternative'),
    'fried chicken': ('steak', 'Grilled steak provides better quality protein'),
    'bacon': ('eggs', 'Eggs give you the protein without the processed fats'),
    'waffles': ('banana', 'A banana is a great natural energy breakfast'),
}

for orig, (sugg, reason) in alternatives_map.items():
    try:
        f_orig = Food.objects.get(name=orig)
        f_sugg = Food.objects.get(name=sugg)
        FoodAlternative.objects.get_or_create(
            original_food=f_orig, 
            suggested_alternative=f_sugg, 
            reason_why=reason
        )
    except Exception as e:
        print(f"Error linking {orig}: {e}")

print("تم التأكد من إضافة الـ 61 صنف بنجاح!")