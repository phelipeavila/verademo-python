from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('', views.home),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('register-finish', views.registerFinish, name='registerFinish'),
    path('feed', views.feed, name='feed'),
    path('blabbers', views.blabbers, name='blabbers'),
    path('profile', views.profile, name='profile'),
    path('tools', views.tools, name='tools'),
    path('notImplemented', views.notImplemented, name='notImplemented'),
    path('reset', views.reset, name='reset'),
    #path('hello/',views.say_hello),
    # path('register/', views.register),
]