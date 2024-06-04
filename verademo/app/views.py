from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.db import connection
import logging
import base64
import hashlib
from django.views.generic import TemplateView
from app.models import User
from django.core import serializers
import sys

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
    if request.session.get('username'):
        return redirect('feed')
    
    return login(request)

def feed(request):
    return render(request, 'app/feed.html', {})

def login(request):
    if request.method == "GET":
        # Equivalent of UserController.java
        target = request.GET.get('target')
        username = request.GET.get('username')

        if request.session.get('username'):
            logger.info("User is already logged in - redirecting...")
            if (target != None) and (target) and (not target == "null"):
                return redirect(target)
            else:
                return redirect('feed')

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
            unencodedUserDetails = next(serializers.deserialize('xml', userDetailsCookie))

            logger.info("User details were retrieved for user: " + unencodedUserDetails.object.username)
            
            request.session['username'] = unencodedUserDetails.object.username

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
            response = redirect(nextView)
        else:
            nextView = 'feed'
            response = redirect(nextView)

        try:
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:
                logger.info("Creating database query")

                # TODO: Replace with md5 hash after register uses MD5
                # sqlQuery = "select username, password, hint, dateCreated, lastLogin, \
                #             realName, blabName from app_user where username='" + username + "' \
                #             and password='" + hashlib.md5(password.encode('utf-8')).hexdigest() + "';"
                sqlQuery = "select username, password, hint, dateCreated, lastLogin, \
                            realName, blabName from app_user where username='" + username + "' \
                            and password='" + password + "';"
                
                cursor.execute(sqlQuery)
                row = cursor.fetchone()
                columns = [col[0] for col in cursor.description]
                row = dict(zip(columns, row))
                if (row):
                    logger.info("User found")
                    response.set_cookie('username', username)
                    if (not remember is None):
                        currentUser = User(username=row["username"],
                                    hint=row["hint"], dateCreated=row["dateCreated"],
                                    lastLogin=row["lastLogin"], realName=row["realName"], 
                                    blabName=row["blabName"])
                        cookie = serializers.serialize('xml', [currentUser,])
                        response.set_cookie('user', cookie)
                    request.session['username'] = row['username']

                    update = "UPDATE app_user SET lastLogin=date('now') WHERE username='" + row['username'] + "';"
                    cursor.execute(update)
                else:
                    logger.info("User not found")

                    # TODO: Add attributes for errors and target

                    nextView = 'login'
                    response = redirect(nextView)
        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

            nextView = 'login'
            response = redirect(nextView)

        logger.info("Redirecting to view: " + nextView)
            
        return response

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
        
    return render (request, 'app/feed.html')