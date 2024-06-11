from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse
from django.db import connection, transaction, IntegrityError
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
import logging, sys, os
import sqlite3, hashlib

from app.models import User, Blabber, Blabber
from app.forms import RegisterForm


# Get logger
logger = logging.getLogger("VeraDemo:userController")
image_dir = os.path.join(os.path.dirname(__file__), '../../resources/images')

###LOGIN###
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
        imageDir = image_dir
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


def updateInResponse(user, response):
    cookie = serializers.serialize('xml', [user,])
    response.set_cookie('user', cookie)
    return response

def downloadImage(request):
    imageName = request.GET.get('image')
    logger.info("Entering downloadImage")

    username = request.session.get('username')
    if not username:
        logger.info("User is not Logged In - redirecting...")
        return redirect('/login?target=profile')
    logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

    f = image_dir
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
            path = image_dir
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

'''
Takes a username and searches for the profile image for that user
'''
def getProfileImageNameFromUsername(username):
    f = image_dir
    # f = os.path.realpath("./resources/images")
    matchingFiles = [file for file in os.listdir(f) if file.startswith(username + ".")]

    if not matchingFiles:
        return None
    return matchingFiles[0]

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'