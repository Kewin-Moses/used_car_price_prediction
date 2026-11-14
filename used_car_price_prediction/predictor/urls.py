from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="predictor/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("predict/", views.predict, name="predict"),
    path("history/", views.history, name="history"),
    path("report/<int:prediction_id>/", views.download_report, name="download_report"),
    path("chatbot/", views.chatbot, name="chatbot"),
]
