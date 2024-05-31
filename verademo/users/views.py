from django.shortcuts import render
from django.http import HttpResponse

# Deals with HTTP request/response
def say_hello(request):
    return HttpResponse('hello')