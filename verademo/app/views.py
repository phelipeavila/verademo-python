from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.db import connection
import logging
import base64
import hashlib
from django.views.generic import TemplateView
from app.models import User
import pickle

from .forms import UserForm

# Get logger
logger = logging.getLogger("__name__")

def registerHandler(request):
    if(request.method == "GET"):
        return register(request)
    elif(request.method == "POST"):
        return finish_register(request)

'''
renders the register.html file, called by a path in urls
'''
def register(request):
    return render(request, 'app/register.html', {})

def finish_register(request):
    context = {
        'username':request.POST.get('username')
    }
    return render(request, 'app/register-finish.html', context)

def home(request):
    # Equivalent of HomeController.java
    # TODO: Check if user is already logged in.
    #       If so, redirect to user's feed
    # if request.user.is_authenticated:
        # return redirect('feed')
    # else:
    return login(request)

def feed(request):
    return render(request, 'app/feed.html', {})

def login(request):
    if request.method == "GET":
        # Equivalent of UserController.java
        target = request.GET.get('target')
        username = request.GET.get('username')

        # TODO: Check if user is already logged in.
        #       If user is already logged in, redirect to 'feed' by default or target if exists
        # if request.user.is_authenticated:
        #     logger.info("User is already logged in - redirecting...")
        #     if (target != None) and (target) and (not target == "null"):
        #         return redirect(target)
        #     else:
        #         return redirect('feed')

        # TODO: Use cookies to remember users
        userDetailsCookie = request.COOKIES.get('user')
        if userDetailsCookie is None or not userDetailsCookie:
            logger.info("No user cookie")
            userDetailsCookie = None
            if username is None:
                username = ''
            if target is None:
                target = ''
            logger.info("Entering login with username " + username + " and target " + target)
            
            # TODO: Add username and target to login

        else:
            logger.info("User details were remembered")
            unencodedUserDetails = pickle.loads(userDetailsCookie)
            logger.info("User details were retrieved for user: " + unencodedUserDetails.UserName)
            
            # TODO: Set username for session

            if (target != None) and (target) and (not target == "null"):
                return redirect(target)
            else:
                return redirect('feed')

        return render(request, 'app/login.html', { "username": username, "target": target })
    
    if request.method == "POST":
        logger.info("Processing login")

        username = request.POST.get('user')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        target = request.POST.get('target')

        if (target != None) and (target) and (not target == "null"):
            nextView = target
        else:
            nextView = 'feed'

        connect = None
        sqlStatement = None

        try:
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:
                logger.info("Creating database query")
                sqlQuery = "select username, password, password_hint, created_at, last_login, \
                            real_name, blab_name from users where username='" + username + "' \
                            and password='" + hashlib.md5(password) + "';"
                cursor.execute(sqlQuery)
                row = cursor.fetchone()
                if (row):
                    logger.info("User found")
                    response = HttpResponse()
                    response.set_cookie('username', username)
                    if (not remember is None):
                        currentUser = User.objects.create(userName=row["username"],
                                    hint=row["password_hint"], dateCreated=row["created_at"],
                                    lastLogin=row["last_login"], realName=row["real_name"], 
                                    blabName=row["blab_name"])
                        response.set_cookie('user', pickle.dumps(currentUser))
                    request.session['username'] = row['username']

                    update = "UPDATE users SET last_login=NOW() WHERE username={row['" + row['username'] + "']};"
                    cursor.execute(update)
                else:
                    logger.info("User not found")

                    # TODO: Add attributes for errors and target

                    nextView = 'login'
        except:

            # TODO: Implement exceptions

            logger.error("Placeholder")

        logger.info("Redirecting to view: " + nextView)
        return redirect(nextView)

'''
Interprets POST request from register form, adds user to database
TODO: Currently linked with register.html
    - Redirect to login.html
    - called by completion of register-finish.html
    - maintiain /register URL
'''
def user_create_view(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        form.save()
        
    return render (request, 'app/login.html')