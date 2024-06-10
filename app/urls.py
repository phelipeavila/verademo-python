from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from . import views
from . import view

urlpatterns = [
    path('', views.home),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('register', views.register, name='register'),
    path('register-finish', views.registerFinish, name='registerFinish'),
    path('feed', views.feed, name='feed'),
    path('morefeed', views.morefeed, name='morefeed'),
    path('blabbers', views.blabbers, name='blabbers'),
    path('profile', views.profile, name='profile'),
    path('tools', views.tools, name='tools'),
    path('notImplemented', views.notImplemented, name='notImplemented'),
    path('reset', view.reset, name='reset'),
    path('downloadprofileimage', views.downloadImage, name='downloadProfileImage'),
    path('blab', views.blab, name='blab'),
    #path('hello/',views.say_hello),
    # path('register/', views.register),
]