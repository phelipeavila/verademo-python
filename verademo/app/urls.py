from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('', views.login),
    path('login', views.login),
    path('register', views.register),
    path('reg-return', views.user_create_view),
    path('hello/',views.say_hello),
   # path('register/', views.register),
]