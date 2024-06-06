from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.db import connection
import sqlite3
import logging
import base64
import subprocess
import hashlib
from django.views.generic import TemplateView
from app.models import User, Blabber, Blab, Blabber
from django.core import serializers
from datetime import datetime
import sys, os

from .forms import UserForm, RegisterForm

# Get logger
logger = logging.getLogger("__name__")

sqlBlabsByMe = ("SELECT blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid "
			    "FROM blabs LEFT JOIN comments ON blabs.blabid = comments.blabid "
			    "WHERE blabs.blabber = %s GROUP BY blabs.blabid ORDER BY blabs.timestamp DESC;")

sqlBlabsForMe = ("SELECT users.username, users.blab_name, blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid "
			    "FROM blabs INNER JOIN users ON blabs.blabber = users.username INNER JOIN listeners ON blabs.blabber = listeners.blabber "
			    "LEFT JOIN comments ON blabs.blabid = comments.blabid WHERE listeners.listener = %s "
			    "GROUP BY blabs.blabid ORDER BY blabs.timestamp DESC LIMIT {} OFFSET {};")

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

                logger.info("Executing query to get all 'Blabs for me'")
                blabsForMe = sqlBlabsForMe.format(10, 0)
                cursor.execute(blabsForMe, (username,))
                blabsForMeResults = cursor.fetchall()

                feedBlabs = []
                for blab in blabsForMeResults:
                    author = Blabber()
                    author.username = blab[0]
                    author.blabName = blab[1]
                    
                    post = Blab()
                    post.setId(blab[5])
                    post.setContent(blab[2])
                    post.setPostDate(blab[3])
                    post.setCommentCount(blab[4])
                    post.setAuthor(author)

                    feedBlabs.append(post)
                    
                request.blabsByOthers = feedBlabs
                request.currentUser = username

                # Find the Blabs by this user

                logger.info("Executing query to get all of user's Blabs")
                cursor.execute(sqlBlabsByMe, (username,))
                blabsByMeResults = cursor.fetchall()

                myBlabs = []
                for blab in blabsByMeResults:
                    post = Blab()
                    post.setId(blab[3])
                    post.setContent(blab[0])
                    post.setPostDate(blab[1])
                    post.setCommentCount(blab[2])

                    myBlabs.append(post)
                    
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
                addBlabSql = "INSERT INTO blabs (blabber, content, timestamp) values (%s, %s, datetime('now'));"

                logger.info("Executing query to add new blab")
                cursor.execute(addBlabSql, (username, blab))

                if not cursor.rowcount:
                    request.error = "Failed to add comment"

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
            blabsForMe = sqlBlabsForMe.format(len, cnt)
            cursor.execute(blabsForMe, (username,))
            results = cursor.fetchall()
            ret = ""
            for blab in results:
                ret += template.format(username = blab[0], content = blab[2], blab_name = blab[1],
                                       timestamp = blab[3], blabid = blab[5], count = blab[4])
    except:

        # TODO: Implement exceptions

        logger.error("Unexpected error:", sys.exc_info()[0])

    return ret


def blabbers(request):
    return render(request, 'app/blabbers.html', {})

def tools(request):
    return render(request, 'app/tools.html', {})

def profile(request):
    if(request.method == "GET"):
        return showProfile(request)
    elif(request.method == "POST"):
        return processProfile(request)
    
def showProfile(request):
    logger.info("Entering showProfile")
    username = request.session.get('username')
    if not username:
        logger.info("User is not Logged In - redirecting...")
        return redirect("login?target=profile")
    myHecklers = None
    myInfo = None
    sqlMyHecklers = ''
    sqlMyHecklers += "SELECT users.username, users.blab_name, users.created_at " 
    sqlMyHecklers += "FROM users LEFT JOIN listeners ON users.username = listeners.listener " 
    sqlMyHecklers += "WHERE listeners.blabber='%s' AND listeners.status='Active';"
    try:
          
        logger.info("Getting Database connection")
        with connection.cursor() as cursor:    
            # Find the Blabbers that this user listens to
            logger.info(sqlMyHecklers)
            cursor.execute(sqlMyHecklers % username)
            myHecklersResults = cursor.fetchall()
            hecklers=[]
            for i in myHecklersResults:
                
                heckler = Blabber()
                heckler.setUsername(i[0])
                heckler.setBlabName(i[1])
                heckler.setCreatedDate(i[2])
                hecklers.add(heckler)
            

            # Get the audit trail for this user
            events = []

            # START EXAMPLE VULNERABILITY 
            sqlMyEvents = "select event from users_history where blabber=\"" + username + "\" ORDER BY eventid DESC; "
            logger.info(sqlMyEvents)
            cursor.execute(sqlMyEvents)
            userHistoryResult = cursor.fetchall()
            # END EXAMPLE VULNERABILITY 

            for result in userHistoryResult :
                events.add(result[0])

            # Get the users information
            sql = "SELECT username, real_name, blab_name FROM users WHERE username = '" + username + "'"
            logger.info(sql)
            cursor.execute(sql)
            myInfoResults = cursor.fetchone()

            # Send these values to our View
            request.hecklers = hecklers
            request.events = events
            request.username = myInfoResults[0]
            request.image = getProfileImageNameFromUsername(myInfoResults[0])
            request.realName = myInfoResults[1]
            request.blabName = myInfoResults[2]
    except sqlite3.Error as ex :
        logger.error(ex.sqlite_errorcode, ex.sqlite_errorname)
    '''
    finally:    
        try:
            if not myHecklers :
                myHecklers.close()
        
        except sqlite3.Error as exceptSql :
            logger.error(exceptSql.sqlite_errorcode, exceptSql.sqlite_errorname)
        
        try:
            if (connect != null) {
                connect.close();
            }
        except sqlite3.Error as exceptSql :
            logger.error(exceptSql.sqlite_errorcode, exceptSql.sqlite_errorname)
    ''' 
        
    return render(request, 'app/profile.html', {})

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
    logger.info("Entering showRegister")
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
            sqlQuery = "SELECT username FROM users WHERE username = '" + username + "'"
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
def showRegisterFinish(request):
    logger.info("Entering showRegisterFinish")
    return render(request, 'app/register-finish', {})

'''
Interprets POST request from register form, adds user to database
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
                query += "insert into users (username, password, created_at, real_name, blab_name) values("
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

                sqlQuery = "select username, password, password_hint, created_at, last_login, \
                            real_name, blab_name from users where username='" + username + "' \
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

                    update = "UPDATE users SET last_login=datetime('now') WHERE username='" + row['username'] + "';"
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

def getProfileImageNameFromUsername(username):
    f = os.path.realpath("./resources/images")
    matchingFiles = [file for file in os.listdir(f) if file.startswith(username + ".")]

    if not matchingFiles:
        return None
    return matchingFiles[0]


def notImplemented(request):
    return render(request, 'app/notImplemented.html')

def reset(request):
    return render(request, 'app/reset.html')

def processTools(request):
    value = request.POST.get('tools')
    method = request.POST.get('method')
    host = request.POST.get('host')
    fortuneFile =request.GET.get('fortuneFile')
    model = model.setattr("ping", host != None, host = ' ')

    if (fortuneFile== None):
        fortuneFile = "literature"
    
    model.setattr("fortunes", fortune(fortuneFile))

    return 'tools'

def fortune(fortuneFile):
    cmd = "/bin/fortune" + fortuneFile
    output = " "

    while True:
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                output += line
                output += "\n"
        except IOError as e:
            logger.error(e)
        else:
            logger.error(e)

        return output
    
def ping(host):
    output = ""
    logger.info("Pinging: " + host)

    while True:
        try:
            p = subprocess.Popen("ping -c 1 " + host, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                output += line
                output += "\n"

            logger.info(p.__exit__)
        except IOError as e:
            logger.error(e)

        else:
            logger.error(e)

        return output