from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.login),
    path('login', views.login),
    path('hello/',views.say_hello),
   # path('register/', views.register),
]