from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.db import connection
import sqlite3
import logging
import base64
import hashlib
from django.views.generic import TemplateView
from app.models import User, Blabber, Blab
from django.core import serializers
from datetime import datetime
import sys

from .forms import UserForm, RegisterForm

# Get logger
logger = logging.getLogger("__name__")

sqlBlabsByMe = ('''SELECT blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid
			    FROM blabs LEFT JOIN comments ON blabs.blabid = comments.blabid
			    WHERE blabs.blabber = ? GROUP BY blabs.blabid ORDER BY blabs.timestamp DESC;''')

sqlBlabsForMe = ('''SELECT users.username, users.blab_name, blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid
			    FROM blabs INNER JOIN users ON blabs.blabber = users.username INNER JOIN listeners ON blabs.blabber = listeners.blabber
			    LEFT JOIN comments ON blabs.blabid = comments.blabid WHERE listeners.listener = ?
			    GROUP BY blabs.blabid ORDER BY blabs.timestamp DESC LIMIT %d OFFSET %d;''')

def feed(request):
    if request.method == "GET":
        username = request.session.get('username')
        if not username:
            logger.info("User is not Logged In - redirecting...")
            return redirect('/login?target=feed')
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        try:
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:

                # TODO: Find the Blabs that this user listens to

                logger.info("Executing query to get all 'Blabs for me'")
                # cursor.execute(sqlBlabsForMe, username)
                # blabsForMeResults = cursor.fetchall()

                feedBlabs = []
                # for blab in blabsForMeResults:
                #     author = Blabber()
                    
                #     # TODO: Add all blabs in results to feedBlabs list
                
                request.blabsByOthers = feedBlabs
                request.currentUser = username

                # Find the Blabs by this user

                logger.info("Executing query to get all of user's Blabs")
                # cursor.execute(sqlBlabsByMe, username)
                # blabsByMeResults = cursor.fetchall()

                myBlabs = []
                # for blab in myBlabs:
                #     post = Blab()

                #     # TODO: Add all blabs in results to myBlabs list
                    
                request.blabsByMe = myBlabs

        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

            nextView = 'login'
            response = render(request, 'app/' + nextView + '.html', {})
            
        return render(request, 'app/feed.html', {})

    if request.method == "POST":
        blab = request.POST.get('blab')
        response = redirect('feed')
        logger.info("Processing Blabs")

        username = request.session.get('username')
        if (not username):
            logger.info("User is not Logged In - redirecting...")
            return redirect('/login?target=feed')
        
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        try :
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:

                logger.info("Creating query to add new Blab")
                addBlabSql = "INSERT INTO blabs (blabber, content, timestamp) values (?, ?, datetime('now'));"

                logger.info("Executing query to add new blab")
                # addBlabResult = cursor.execute(addBlabSql, (username, blab))

                # if addBlabResult:
                #     request.error = "Failed to add comment"

                response = redirect("feed")

        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

        return response
    
def morefeed(request):
    count = request.GET.get('count')
    length = request.GET.get('len')

    template = ("<li><div>" + "\t<div class=\"commenterImage\">" + "\t\t<img src=\"resources/images/{username}.png\">" +
				"\t</div>" + "\t<div class=\"commentText\">" + "\t\t<p>{content}</p>" +
				"\t\t<span class=\"date sub-text\">by {blab_name} on {timestamp}</span><br>" +
				"\t\t<span class=\"date sub-text\"><a href=\"blab?blabid={blabid}\">{count} Comments</a></span>" + "\t</div>" +
				"</div></li>")
    
    try:
        cnt = int(count)
        len = int(length)
    except ValueError:
        redirect('feed')

    username = request.session.get('username')

    try :
        logger.info("Creating the Database connection")
        with connection.cursor() as cursor:

            logger.info("Executing query to see more Blabs")
            # cursor.execute(sqlBlabsForMe, username)
            # results = cursor.fetchall()
            # ret = ""
            # for blab in results:


            

    except:

        # TODO: Implement exceptions

        logger.error("Unexpected error:", sys.exc_info()[0])



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
    logger.info('Entering processRegister')
    username = request.POST.get('username')
    request.session['username'] = username

    # Get the Database Connection
    logger.info("Creating the Database connection")
    try:
        
        with connection.cursor() as cursor:
            sqlQuery = "SELECT username FROM app_user WHERE username = '" + username + "'"
            cursor.execute(sqlQuery)
            row = cursor.fetchone()
            if (row):
                request.error = "Username '" + username + "' already exists!"
                return render(request, 'app/register.html')
            else:
                return render(request, 'app/register-finish.html')
    except sqlite3.Error as ex :
        logger.error(ex.sqlite_errorcode, ex.sqlite_errorname)
    
    
    
    return render(request, 'app/register.html')

def registerFinish(request):
    if(request.method == "GET"):
        return showRegisterFinish(request)
    elif(request.method == "POST"):
        return processRegisterFinish(request)

'''TODO: This shouldn't pass'''
def showRegisterFinish():
    logger.info("Entering showRegisterFinish")
    pass

'''
Interprets POST request from register form, adds user to database
TODO:Manually input registrations using SQL statements.
- may not work because of change to username field
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
                #mysqlCurrentDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #create query
                query = ''
                query += "insert into app_user (username, password, created_at, real_name, blab_name) values("
                query += ("'" + username + "',")
                query += ("'" + hashlib.md5(password.encode('utf-8')).hexdigest() + "',")
                
                #query += ("'" + mysqlCurrentDateTime + "',")
                query += ("datetime('now'),")
                query += ("'" + realName + "',")
                query += ("'" + blabName + "'")
                query += (");")
                #execute query
                cursor.execute(query)
                sqlStatement = cursor.fetchone() #<- variable for response
                logger.info(query)
                # END EXAMPLE VULNERABILITY
        #TODO: Implement exceptions and final statement
        except sqlite3.Error as er:
            logger.error(er.sqlite_errorcode,er.sqlite_errorname)
        # except ClassNotFoundException as
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

            return render(request, 'app/login.html')

        else:
            logger.info("User details were remembered")
            unencodedUserDetails = next(serializers.deserialize('xml', userDetailsCookie))

            logger.info("User details were retrieved for user: " + unencodedUserDetails.object.username)
            
            request.session['username'] = unencodedUserDetails.object.username

            if (target != None) and (target) and (not target == "null"):
                return redirect(target)
            else:
                return redirect('feed')

    
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

                sqlQuery = "select username, password, hint, created_at, last_login, \
                            real_name, blab_name from app_user where username='" + username + "' \
                            and password='" + hashlib.md5(password.encode('utf-8')).hexdigest() + "';"
                
                cursor.execute(sqlQuery)
                row = cursor.fetchone()

                if (row):
                    columns = [col[0] for col in cursor.description]
                    row = dict(zip(columns, row))
                    logger.info("User found")
                    response.set_cookie('username', username)
                    if (not remember is None):
                        currentUser = User(username=row["username"],
                                    hint=row["hint"], created_at=row["created_at"],
                                    last_login=row["last_login"], real_name=row["real_name"], 
                                    blab_name=row["blab_name"])
                        response = update_in_response(currentUser, response)
                    request.session['username'] = row['username']

                    update = "UPDATE app_user SET last_login=datetime('now') WHERE username='" + row['username'] + "';"
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
    
def notImplemented(request):
    return render(request, 'app/notImplemented.html')

def reset(request):
    return render(request, 'app/reset.html')
