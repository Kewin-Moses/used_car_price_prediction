import csv
from pathlib import Path
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

DATASET_PATH = settings.BASE_DIR / "dataset" / "car data.csv"

def get_car_names():
    try:
        with open(DATASET_PATH, newline="", encoding="utf-8-sig") as file:
            return sorted({row["Car_Name"].strip() for row in csv.DictReader(file) if row.get("Car_Name")})
    except (FileNotFoundError, KeyError):
        return []

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class CarPredictionForm(forms.Form):
    car_name = forms.ChoiceField(label="Car name", choices=[])
    year = forms.IntegerField(min_value=2000, max_value=2026, label="Manufacturing year")
    present_price = forms.FloatField(min_value=0.1, label="Present price (₹ lakhs)")
    driven_kms = forms.IntegerField(min_value=0, label="Kilometres driven")
    fuel_type = forms.ChoiceField(choices=[
        ("Petrol", "Petrol"), ("Diesel", "Diesel"), ("CNG", "CNG")
    ])
    selling_type = forms.ChoiceField(choices=[
        ("Dealer", "Dealer"), ("Individual", "Individual")
    ])
    transmission = forms.ChoiceField(choices=[
        ("Manual", "Manual"), ("Automatic", "Automatic")
    ])
    owner = forms.ChoiceField(choices=[
        ("0", "First owner (0 previous owners)"),
        ("1", "1 previous owner"),
        ("2", "2 previous owners"),
        ("3", "3 previous owners"),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        names = get_car_names()
        self.fields["car_name"].choices = [("", "Select a car")] + [(name, name.title()) for name in names]
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
