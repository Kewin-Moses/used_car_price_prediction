from django.contrib import admin
from .models import Prediction

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("car_name", "user", "predicted_price", "created_at")
    list_filter = ("fuel_type", "selling_type", "transmission")
    search_fields = ("car_name", "user__username")
