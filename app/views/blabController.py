from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.db import connection, transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt


import logging, sys

from app.models import User, Blabber, Blab, Blabber, Comment

# Get logger

logger = logging.getLogger("VeraDemo:blabController")

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

        response = redirect('feed')
        logger.info("Processing Blab")

        username = request.session.get('username')
        if not username:
            logger.info("User is not Logged In - redirecting...")
            return redirect("login?target=feed")
        
        logger.info("User is Logged In - continuing... UA=" + request.headers["User-Agent"] + " U=" + username)

        addCommentSql = "INSERT INTO comments (blabid, blabber, content, timestamp) values (%s, %s, %s, %s);"

        try :
            logger.info("Creating the Database connection")
            with connection.cursor() as cursor:

                now = moment.now().format("YYYY-MM-DD hh:mm:ss")
                logger.info("Preparing the addComment Prepared Statement")

        except:

            # TODO: Implement exceptions

            logger.error("Unexpected error:", sys.exc_info()[0])

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
