from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.db import connection
import logging
import base64
import hashlib
from django.views.generic import TemplateView
from app.models import User
from django.core import serializers

from datetime import datetime
import pickle
import sys
from app.models import User
from .forms import UserForm, RegisterForm

# Get logger
logger = logging.getLogger("__name__")

def feed(request):
    return render(request, 'app/feed.html', {})

def blabbers(request):
    return render(request, 'app/blabbers.html', {})

def profile(request):
    return render(request, 'app/profile.html', {})

def tools(request):
    return render(request, 'app/tools.html', {})

def profile(request):
    if(request.method == "GET"):
        return showProfile(request)
    elif(request.method == "POST"):
        return processProfile(request)
    
def showProfile(request):
    pass

def processProfile(request):
    pass

def register(request):
    if(request.method == "GET"):
        return showRegister(request)
    elif(request.method == "POST"):
        return processRegister(request)

'''
renders the register.html file, called by a path in urls
'''
def showRegister(request):
    return render(request, 'app/register.html', {})

''' Sends username into register-finish page'''
def processRegister(request):
    context = {
        'username':request.POST.get('username')
    }
    return render(request, 'app/register-finish.html', context)

def home(request):
    # Equivalent of HomeController.java
    if request.session.get('username'):
        return redirect('feed')
    
    return login(request)


def login(request):
    if request.method == "GET":

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
            
            request.username = username
            request.target = target

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
            response = render(request, 'app/' + nextView + '.html', {})
        else:
            nextView = 'feed'
            response = render(request, 'app/' + nextView + '.html', {})

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

                if (row):
                    columns = [col[0] for col in cursor.description]
                    row = dict(zip(columns, row))
                    logger.info("User found")
                    response.set_cookie('username', username)
                    if (not remember is None):
                        currentUser = User(username=row["username"],
                                    hint=row["hint"], dateCreated=row["dateCreated"],
                                    lastLogin=row["lastLogin"], realName=row["realName"], 
                                    blabName=row["blabName"])
                        response = update_in_response(currentUser, response)
                    request.session['username'] = row['username']

                    update = "UPDATE app_user SET lastLogin=date('now') WHERE username='" + row['username'] + "';"
                    cursor.execute(update)
                else:
                    logger.info("User not found")

                    request.error = "Login failed. Please try again."
                    request.target = target

                    nextView = 'login'
                    response = render(request, 'app/' + nextView + '.html', {})
        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

            nextView = 'login'
            response = render(request, 'app/' + nextView + '.html', {})

        logger.info("Redirecting to view: " + nextView)
            
        return response

def logout(request):
    logger.info("Processing logout")
    request.session['username'] = None
    response = redirect('login')
    response.delete_cookie('user')
    logger.info("Redirecting to login...")
    return response

def update_in_response(user, response):
    cookie = serializers.serialize('xml', [user,])
    response.set_cookie('user', cookie)
    return response
    

def registerFinish(request):
    if(request.method == "GET"):
        return showRegisterFinish(request)
    elif(request.method == "POST"):
        return processRegisterFinish(request)

def showRegisterFinish():
    logger.info("Entering showRegisterFinish")
    pass

'''
Interprets POST request from register form, adds user to database
'''
def processRegisterFinish(request):
    logger.info("Entering processRegisterFinish")
    form = UserForm(request.POST or None)
    
    if form.is_valid():
        #form.addAttribute
        form.save()
        
    return redirect('feed')
