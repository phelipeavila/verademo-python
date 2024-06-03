from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView

from .forms import UserForm

# Deals with HTTP request/response
def say_hello(request):
    return HttpResponse('hello')

def register(request):
    return render(request, 'app/register.html', {})

def login(request):
<<<<<<< HEAD
    return render(request, 'app/login.html', {})
=======
    return render(request, 'app/login.html',{})

def user_create_view(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        form.save()
        print('help?')
    context = {
        'form': form
    }
    print("help")
    return render (request, 'app/login.html')

class LoginView(TemplateView):
    template_name = 'app/login.html'
    extra_context = {}
>>>>>>> 734d829abd341b9ec23e66f74351b3f13856dbf6
