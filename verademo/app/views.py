from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
import logging
import base64
from django.views.generic import TemplateView

from .forms import UserForm

# Get logger
logger = logging.getLogger(__name__)

# Deals with HTTP request/response
def say_hello(request):
    return HttpResponse('hello')

def register(request):
    return render(request, 'app/register.html', {})

def home(request):
    # Equivalent of HomeController.java
    # TODO: Check if user is already logged in.
    #   If so, redirect to user's feed
    # if request.user.is_authenticated:
        # return redirect('feed')
    # else:
    return login(request)

def login(request):
    # Equivalent of UserController.java
    target = request.GET.get('target')
    username = request.GET.get('username')

    # TODO: Check if user is already logged in.
    #       If user is already logged in, redirect to 'feed' by default or target if exists
    # if request.user.is_authenticated:
    #     logger.info("User is already logged in - redirecting...")
    #     if (target != None) and (target) and (not target == "null"):
    #         return redirect('target')
    #     else:
    #         return redirect('feed')

    # TODO: Use cookies to remember users
    userDetailsCookie = request.COOKIES.get('user')
    if userDetailsCookie is None:
        logger.info("No user cookie")
        userDetailsCookie = None
    if not userDetailsCookie:
        logger.info("User cookie is empty")
        userDetailsCookie = None

    logger.info("User details were remembered")
    unencodedUserDetails = userDetailsCookie.decode('ascii')

    return render(request, 'app/login.html', {})

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

