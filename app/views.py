from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden, JsonResponse
from django.db import connection, transaction, IntegrityError
from django.core.files.storage import FileSystemStorage
import sqlite3
import logging
import base64
import subprocess
import hashlib
from django.views.generic import TemplateView
from app.models import User, Blabber, Blab, Blabber, Comment
from django.core import serializers
from datetime import datetime
from django.http import HttpResponse
from app.commands.BlabberCommand import BlabberCommand
from app.commands.ListenCommand import ListenCommand
from app.commands.IgnoreCommand import IgnoreCommand
from django.views.decorators.csrf import csrf_exempt

import sys, os, moment

from app.forms import UserForm, RegisterForm
'''
General Note: '%s' should have surrounding quotes removed to prevent SQL injection.
'''
# Get logger
logger = logging.getLogger("__name__")

sqlBlabsByMe = ("SELECT blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid "
                "FROM blabs LEFT JOIN comments ON blabs.blabid = comments.blabid "
                "WHERE blabs.blabber = '%s' GROUP BY blabs.blabid ORDER BY blabs.timestamp DESC;")
#NOTE: Tried adding quotes around %s, and it didn't work. Possible filtering in the blabsForMe format?
sqlBlabsForMe = ("SELECT users.username, users.blab_name, blabs.content, blabs.timestamp, COUNT(comments.blabber), blabs.blabid "
                "FROM blabs INNER JOIN users ON blabs.blabber = users.username INNER JOIN listeners ON blabs.blabber = listeners.blabber "
                "LEFT JOIN comments ON blabs.blabid = comments.blabid WHERE listeners.listener = '%s' "
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
                cursor.execute(blabsForMe % (username,))
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
                cursor.execute(sqlBlabsByMe % (username,))
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
                addBlabSql = "INSERT INTO blabs (blabber, content, timestamp) values ('%s', '%s', datetime('now'));"

                logger.info("Executing query to add new blab")
                cursor.execute(addBlabSql % (username, blab))

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
            cursor.execute(blabsForMe % (username,))
            results = cursor.fetchall()
            ret = ""
            for blab in results:
                ret += template.format(username = blab[0], content = blab[2], blab_name = blab[1],
                                       timestamp = blab[3], blabid = blab[5], count = blab[4])
    except:

        # TODO: Implement exceptions

        logger.error("Unexpected error:", sys.exc_info()[0])

    return HttpResponse(ret)

def blab(request):
    if request.method == "GET":
        blabid = request.GET.get('blabid')
        response = redirect('feed')
        logger.info("Showing Blab")
        
        username = request.session.get('username')
        if not username:
            logger.info("User is not Logged In - redirecting...")
            return redirect("login?target=feed")
        
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        blabDetailsSql = ("SELECT blabs.content, users.blab_name "
                "FROM blabs INNER JOIN users ON blabs.blabber = users.username " + "WHERE blabs.blabid = '%s';")

        blabCommentsSql = ("SELECT users.username, users.blab_name, comments.content, comments.timestamp "
                "FROM comments INNER JOIN users ON comments.blabber = users.username "
                "WHERE comments.blabid = '%s' ORDER BY comments.timestamp DESC;")
        
        try :
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:

                logger.info("Executing query to see Blab details")
                cursor.execute(blabDetailsSql % (blabid,))
                blabDetailsResults = cursor.fetchone()

                if (blabDetailsResults):
                    request.content = blabDetailsResults[0]
                    request.blab_name = blabDetailsResults[1]
                    request.blabid = blabid

                    # Get comments
                    logger.info("Executing query to get all comments")
                    cursor.execute(blabCommentsSql % (blabid,))
                    blabCommentsResults = cursor.fetchall()

                    comments = []
                    for blab in blabCommentsResults:
                        author = Blabber()
                        author.setUsername(blab[0])
                        author.setBlabName(blab[1])

                        comment = Comment()
                        comment.setContent(blab[2])
                        comment.setTimestamp(blab[3])
                        comment.setAuthor(author)

                        comments.append(comment)
                    request.comments = comments

                    response = render(request, 'app/blab.html', {})

        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

        return response
    
    if request.method == "POST":
        comment = request.POST.get('comment')
        blabid = request.POST.get('blabid')

@csrf_exempt
def blabbers(request):
    if request.method == "GET":
        sort = request.GET.get('sort')
        if (sort is None or not sort):
            sort = "blab_name ASC"
        response = redirect('feed')
        logger.info("Showing Blabbers")

        username = request.session.get('username')
        if not username:
            logger.info("User is not Logged In - redirecting...")
            return redirect("login?target=blabbers")
        
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        blabbersSql = ("SELECT users.username," + " users.blab_name," + " users.created_at,"
                    " SUM(iif(listeners.listener='%s', 1, 0)) as listeners,"
                    " SUM(iif(listeners.status='Active',1,0)) as listening"
                    " FROM users LEFT JOIN listeners ON users.username = listeners.blabber"
                    " WHERE users.username NOT IN (\"admin\",'%s')" + " GROUP BY users.username" + " ORDER BY " + sort + ";")

        try:
            logger.info("Creating database connection")
            with connection.cursor() as cursor:

                logger.info(blabbersSql)
                logger.info("Executing query to see Blab details")
                cursor.execute(blabbersSql % (username, username))
                blabbersResults = cursor.fetchall()

                blabbers = []
                for b in blabbersResults:
                    blabber = Blabber()
                    blabber.setBlabName(b[1])
                    blabber.setUsername(b[0])
                    blabber.setCreatedDate(b[2])
                    blabber.setNumberListeners(b[3])
                    blabber.setNumberListening(b[4])

                    blabbers.append(blabber)

                request.blabbers = blabbers

                response = render(request, 'app/blabbers.html', {})
        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

        return response
    
    if request.method == "POST":
        blabberUsername = request.POST.get('blabberUsername')
        command = request.POST.get('command')

        response = redirect('feed')
        logger.info("Processing Blabbers")

        username = request.session.get('username')
        if not username:
            logger.info("User is not Logged In - redirecting...")
            return redirect("login?target=blabbers")
        
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        if (command is None or not command):
            logger.info("Empty command provided...")
            response = redirect('login?target=blabbers')
        logger.info("blabberUsername = " + blabberUsername)
        logger.info("command = " + command)

        try:
            logger.info("Creating database connection")
            with connection.cursor() as cursor:
                module = command.capitalize()[:-1] + "Command"
                cmdClass = eval(module)
                cmdObj = cmdClass(cursor, username)
                cmdObj.execute(blabberUsername)
                return redirect('blabbers')
        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])
        
        return response


    


###########USER CONTROLLER################
def profile(request):
    if(request.method == "GET"):
        return showProfile(request)
    elif(request.method == "POST" and is_ajax(request)):
        return processProfile(request)
    else:
        return JsonResponse({'message':'Expected ajax request, got none'})
    
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
                hecklers.append(heckler)
            

            # Get the audit trail for this user
            events = []

            # START EXAMPLE VULNERABILITY 
            sqlMyEvents = "select event from users_history where blabber=\"" + username + "\" ORDER BY eventid DESC; "
            logger.info(sqlMyEvents)
            cursor.execute(sqlMyEvents)
            userHistoryResult = cursor.fetchall()
            # END EXAMPLE VULNERABILITY 

            for result in userHistoryResult :
                events.append(result[0])

            # Get the users information
            sql = "SELECT username, real_name, blab_name FROM users WHERE username = '" + username + "'"
            logger.info(sql)
            cursor.execute(sql)
            myInfoResults = cursor.fetchone()
            if not myInfoResults:
                return JsonResponse({'Error, no Inforesults found'})
            # Send these values to our View
            request.hecklers = hecklers
            request.events = events
            request.username = myInfoResults[0]
            request.image = getProfileImageNameFromUsername(myInfoResults[0])
            request.realName = myInfoResults[1]
            request.blabName = myInfoResults[2]
    except sqlite3.Error as ex :
        logger.error(ex.sqlite_errorcode, ex.sqlite_errorname)
        
    return render(request, 'app/profile.html', {})

'''TODO: Connect form to profile update
TODO: Test sqlite3 error handling
NOTE: This saves images to the local images folder, but it would be much easier and more secure to
store profile images in the database.
'''
def processProfile(request):
    realName = request.POST.get('realName')
    blabName = request.POST.get('blabName')
    username = request.POST.get('username')
    file = request.FILES.get('file')
    #TODO: Experiment with safe=False on JsonResponse, send in non-dict objects for serialization
    # Initial response only get returns if everything else succeeds.
    # This must be here in order to use set_cookie later in the program
    msg = f"<script>alert('Successfully changed values!\\nusername: {username.lower()}\\nReal Name: {realName}\\nBlab Name: {blabName}');</script>"
    response = JsonResponse({'values':{"username": username.lower(), "realName": realName, "blabName": blabName}, 'message':msg},status=200)
    
    logger.info("entering processProfile")
    sessionUsername = request.session.get('username')

    # Ensure user is logged in
    if not sessionUsername:
        logger.info("User is not Logged In = redirecting...")
        response = JsonResponse({'message':"<script>alert('Error - please login');</script>"},status=403)
        #response.status_code = 403
        return response
        #TODO: Resolve request/response status and ensure same funcitonality
        
    logger.info("User is Logged In - continuing... UA=" + request.headers['User-Agent'] + " U=" + sessionUsername)
    oldUsername = sessionUsername

    # Update user information

    try:
        logger.info("Getting Database connection")
        # Get the Database Connection
        # TODO: Error in SQL execution
        with connection.cursor() as cursor:
            logger.info("Preparing the update Prepared Statement")
            update = "UPDATE users SET real_name='%s', blab_name='%s' WHERE username='%s';"
            logger.info("Executing the update Prepared Statement")
            cursor.execute(update % (realName,blabName,sessionUsername))
            updateResult = cursor.fetchone()

            # If there is a record...
            if updateResult:
                # failure
                
                response = JsonResponse({'message':"<script>alert('An error occurred, please try again.');</script>"},status=500)
                #response.status_code = 500
                return response
            
    except sqlite3.Error as ex :
        logger.error(ex.sqlite_errorcode, ex.sqlite_errorname)

    # Rename profile image if username changes
    if username != oldUsername :
        
        if usernameExists(username):
            
            response = JsonResponse({'message':"<script>alert('That username already exists. Please try another.');</script>"},status=409)
            #response.status_code = 409
            return response

        if not updateUsername(oldUsername, username):
            
            response = JsonResponse({'message':"<script>alert('An error occurred, please try again.');</script>"},status=500)
            #response.status_code = 500
            return response
        
        # Update all session and cookie logic
        request.session['username'] = username
        response.set_cookie('username',username)
        

        # Update remember me functionality
        userDetailsCookie = request.COOKIES.get('user')
        if userDetailsCookie is not None:
            unencodedUserDetails = next(serializers.deserialize('xml', userDetailsCookie))
            unencodedUserDetails.object.username = username
            response = updateInResponse(unencodedUserDetails.object, response)
        

        # Update user profile image
    if file:
        dir_path = os.path.dirname(__file__)
        imageDir = os.path.join(dir_path, '../resources/images')
        # imageDir = os.path.realpath("./resources/images/")
        

        # Get old image name, if any, to delete
        oldImage = getProfileImageNameFromUsername(username)
        if oldImage:
            os.remove(os.path.join(imageDir,oldImage))
        

        # TODO: check if file is png first //Done?
        try:
            #Potential VULN? ending with .png, having different file type
            extension = file.name.lower().endswith('.png')
            if extension:
                path = imageDir + '/' + username + '.png'
            else:
                
                response = JsonResponse({'message':"<script>alert('File must end in .png');</script>"},status=422)
                #response.status_code = 422
                return response
            logger.info("Saving new profile image: " + path)

            with open(path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

        except Exception as ex :
            logger.error(ex)
        '''
        except IllegalStateException as e:
            logger.error(e)
        '''
    
    return response

@csrf_exempt
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

@csrf_exempt
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
        
        return redirect('/login?username=' + username)
    else:
        logger.info("Form is invalid")
        request.error = "Please fill out all fields"
        return render(request, 'app/register.html')
        
    # return render (request, 'app/feed.html')

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
                                    password_hint=row["password_hint"], created_at=row["created_at"],
                                    last_login=row["last_login"], real_name=row["real_name"], 
                                    blab_name=row["blab_name"])
                        response = updateInResponse(currentUser, response)
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

def updateInResponse(user, response):
    cookie = serializers.serialize('xml', [user,])
    response.set_cookie('user', cookie)
    return response


'''
Takes a username and searches for the profile image for that user
'''
def getProfileImageNameFromUsername(username):
    dir_path = os.path.dirname(__file__)
    f = os.path.join(dir_path, '../resources/images')
    # f = os.path.realpath("./resources/images")
    matchingFiles = [file for file in os.listdir(f) if file.startswith(username + ".")]

    if not matchingFiles:
        return None
    return matchingFiles[0]

def downloadImage(request):
    imageName = request.GET.get('image')
    logger.info("Entering downloadImage")

    username = request.session.get('username')
    if not username:
        logger.info("User is not Logged In - redirecting...")
        return redirect('/login?target=profile')
    logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

    dir_path = os.path.dirname(__file__)
    f = os.path.join(dir_path, '../resources/images/')
    path = f + imageName

    logger.info("Fetching profile image: " + path)

    try:
        if os.path.exists(path):
            with open(path, 'rb') as file:
                response = HttpResponse(file.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
                return response

    except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

    return render(request, "app/profile.html", {})

def notImplemented(request):
    return render(request, 'app/notImplemented.html')

def reset(request):
    return render(request, 'app/reset.html')

def tools(request):
    if(request.method == "GET"):
        return showTools(request)
    elif(request.method == "POST"):
        return processTools(request)
    
def showTools(request):
    return render(request, 'app/tools.html', {})

def processTools(request):
    host = request.POST.get('host')
    fortuneFile = request.POST.get('fortuneFile')
    ping_result = ping(host) if host else ""
    
    if not fortuneFile:
        fortuneFile = 'literature'
        fortune(fortuneFile)

    # Previous Logic
    '''logger.info("Processing tools")
    toolMenu = request.POST.get('/tools')
    host = request.POST.get('host')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        cHost = form.cleaned_data.get('host')
        if host is not None:
            logger.info("Host: " + host)
            ping(host) '''






    return render(request, 'app/tools.html')

def fortune(fortuneFile):
    cmd = "/bin/fortune" + fortuneFile
    output = " "

    try: 
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            b'output += line + "\n"'.decode("utf-8")
            
    except IOError as e:
        print("Error occurred:", e)
        logger.error(e)

        return output


    '''while True:
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                output += line
                output += "\n"
        except IOError as e:
            logger.error(e)
        else:
            logger.error(e)

        return output'''
    

def ping(host):
    output = ""
    
    try:
        p = subprocess.Popen(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = p.communicate(timeout=5)
    
        output = stdout.decode() if stdout else ""
        print("Exit Code:", p.returncode)
    except subprocess.TimeoutExpired:
        print("Ping request timed out")
    except Exception as e:
        print("Error occurred:", e)
    # TO FIX ERROR, CRASH ON PING
    # return render(output, 'app/tools.html')
    return output

   
   
''' output = ""
    logger.info("Pinging: " + host)

    while True:
        try:
            p = os.system("ping -c 1 -w2 " + host + " > /dev/null 2>&1")
            for line in p.stdout.readlines():
                output += line
                output += "\n"

            logger.info(p.__exit__)
        except IOError as e:
            logger.error(e)

        else:
            logger.error(e)

        return output '''

def usernameExists(username):
    username = username.lower()
    # Check is the username already exists
    try:
        # Get the Database Connection
        logger.info("Getting Database connection")
        with connection.cursor() as cursor:
            logger.info("Preparing the duplicate username check Prepared Statement")
            sqlStatement = "SELECT username FROM users WHERE username='%s'"
            cursor.execute(sqlStatement % (username,))
            result = cursor.fetchone()
            if not result:
                # username does not exist
                return False
            
    except sqlite3.Error as er:
            logger.error(er.sqlite_errorcode,er.sqlite_errorname)
    except ModuleNotFoundError as ex:
        logger.error(ex)
    logger.info("Username: " + username + " already exists. Try again.")
    return True

def updateUsername(oldUsername, newUsername):
    # Enforce all lowercase usernames
    oldUsername = oldUsername.lower()
    newUsername = newUsername.lower()

    # Check is the username already exists
    try:
        logger.info("Getting Database connection")
        # Get the Database Connection
        with transaction.atomic():
            with connection.cursor() as cursor:

                # Update all references to this user
                sqlStrQueries = [
                    "UPDATE users SET username='%s' WHERE username='%s'",
                    "UPDATE blabs SET blabber='%s' WHERE blabber='%s'",
                    "UPDATE comments SET blabber='%s' WHERE blabber='%s'",
                    "UPDATE listeners SET blabber='%s' WHERE blabber='%s'",
                    "UPDATE listeners SET listener='%s' WHERE listener='%s'",
                    "UPDATE users_history SET blabber='%s' WHERE blabber='%s'" ]
        
                # Execute updates as part of a batch transaction
                # This will roll back all changes if one query fails
                for query in sqlStrQueries:
                    cursor.execute(query % (newUsername,oldUsername))


        # Rename the user profile image to match new username
        oldImage = getProfileImageNameFromUsername(oldUsername)
        if oldImage:
            extension = '.png'

            logger.info("Renaming profile image from " + oldImage + " to " + newUsername + extension)
            dir_path = os.path.dirname(__file__)
            path = os.path.join(dir_path, '../resources/images')
            # path = os.path.realpath("./resources/images")
            oldPath = path + '/' + oldImage
            newPath = path + '/' + newUsername + extension
            os.rename(oldPath, newPath)
        return True
    except (sqlite3.Error, ModuleNotFoundError) as ex:
        logger.error(ex)
    except IntegrityError as er:
        logger.error(er)
    # Error occurred
    return False

def create(userName, blabName,realName):
    password = userName
    dateCreated = moment.now().format("YYYY-MM-DD hh:mm:ss")
    lastLogin = None
    return User(userName, password, dateCreated, lastLogin, blabName, realName)

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'