from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('', views.home),
    path('login', views.login, name='login'),
    path('register', views.registerHandler, name='register'),
    path('register-finish', views.user_create_view, name='register-finish'),
    path('feed', views.feed, name='feed'),
    path('blabbers', views.blabbers, name='blabbers'),
    path('profile', views.profile, name='profile'),
    path('tools', views.tools, name='tools'),
    #path('hello/',views.say_hello),
    # path('register/', views.register),
]