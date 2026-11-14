from django.db import models
from django.contrib.auth.models import User

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car_name = models.CharField(max_length=100)
    year = models.IntegerField()
    present_price = models.FloatField()
    driven_kms = models.IntegerField()
    fuel_type = models.CharField(max_length=30)
    selling_type = models.CharField(max_length=30)
    transmission = models.CharField(max_length=30)
    owner = models.IntegerField()
    predicted_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car_name} - {self.predicted_price}"
