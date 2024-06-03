from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('', views.home),
    path('login', views.login),
    path('register', views.registerHandler),
    path('register-finish', views.user_create_view),
    path('feed', views.feed),
   # path('register/', views.register),
]