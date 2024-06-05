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
    request.session['username'] = request.POST.get('username')
    return render(request, 'app/register-finish.html')

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
'''
TODO:Handle Exceptions
'''
def processRegisterFinish(request):
    logger.info("Entering processRegisterFinish")
    #create variables
    username = request.session.get('username')
    cpassword = request.POST.get('cpassword')
    #fill in required username field
    form = RegisterForm(request.POST or None)
    #user now should have all the required fields

    if form.is_valid():
        password = form.cleaned_data.get('password')
        #Check if passwords from form match
        if password != cpassword:
            logger.info("Password and Confirm Password do not match")
            request.error = "The Password and Confirm Password values do not match. Please try again."
            return render(request, 'app/register.html')
        sqlStatement = None
        try:
            # Get the Database Connection
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:
                # START EXAMPLE VULNERABILITY 
                # Execute the query

                #set variables to make easier to use
                realName = form.cleaned_data.get('realName')
                blabName = form.cleaned_data.get('blabName')
                mysqlCurrentDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #create query
                query = ''
                query += "insert into app_user (username, password, dateCreated, realName, blabName) values("
                query += ("'" + username + "',")
                query += ("'" + password + "',")
                query += ("'" + mysqlCurrentDateTime + "',")
                query += ("'" + realName + "',")
                # TODO: Implement hashing
                #query += ("'" + BCrypt.hashpw(password, BCrypt.gensalt()) + "',")
                query += ("'" + blabName + "'")
                query += (");")
                #execute query
                #test
                cursor.execute(query)
                sqlStatement = cursor.fetchone() #<- variable for response
                logger.info(query)
                # END EXAMPLE VULNERABILITY
        #TODO: Implement exceptions and final statement
        except: # SQLException, ClassNotFoundException as e:
            logger.info("error") #<- temporary
            #logger.error("error")
        '''
        finally:
            try:
                if sqlStatement != None:
                    #sqlStatement.close();
                
            except SQLException as exceptSql
                logger.error(exceptSql)
            try:
                if (connect != null) {
                    connect.close();
                }
            } catch (SQLException exceptSql) {
                logger.error(exceptSql);
            }
        '''
        

        
    return render (request, 'app/feed.html')

def home(request):
    # Equivalent of HomeController.java
    if request.session.get('username'):
        return redirect('feed')
    
    return login(request)

def feed(request):
    return render(request, 'app/feed.html', {})

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
        
    return redirect('feed')