from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views

urlpatterns = [
    path('', views.home),
    path('login', views.login, name='login'),
<<<<<<< HEAD
    path('register', views.register, name='register'),
    path('register-finish', views.registerFinish, name='registerFinish'),
=======
    path('logout', views.logout, name='logout'),
    path('register', views.registerHandler, name='register'),
    path('register-finish', views.user_create_view, name='register-finish'),
>>>>>>> eaf6956f605211fb0a7f082bd5b3a1c079a20367
    path('feed', views.feed, name='feed'),
    path('blabbers', views.blabbers, name='blabbers'),
    path('profile', views.profile, name='profile'),
    path('tools', views.tools, name='tools'),
    #path('hello/',views.say_hello),
    # path('register/', views.register),
]