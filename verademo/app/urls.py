from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.LoginView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('hello/',views.say_hello),
]