from django.shortcuts import redirect, render
from django.db import connection, transaction, IntegrityError

from app.models import User
from app.views import create

import sqlite3
import logging
import random as rand
# START 3rd PARTY PACKAGE
import moment
# END

##################RESET CONTROLLER#####################
logger = logging.getLogger("__name__")
# Did not include admin in users list due to pre-existing admin functionality with DJango
users = [
			create("john", "John", "John Smith"),
			create("paul", "Paul", "Paul Farrington"),
			create("chrisc", "Chris", "Chris Campbell"),
			create("laurie", "Laurie", "Laurie Mercer"),
			create("nabil", "Nabil", "Nabil Bousselham"),
			create("julian", "Julian", "Julian Totzek-Hallhuber"),
			create("joash", "Joash", "Joash Herbrink"),
			create("andrzej", "Andrzej", "Andrzej Szaryk"),
			create("april", "April", "April Sauer"),
			create("armando", "Armando", "Armando Bioc"),
			create("ben", "Ben", "Ben Stoll"),
			create("brian", "Brian", "Brian Pitta"),
			create("caitlin", "Caitlin", "Caitlin Johanson"),
			create("christraut", "Chris Trautwein", "Chris Trautwein"),
			create("christyson", "Chris Tyson", "Chris Tyson"),
			create("clint", "Clint", "Clint Pollock"),
			create("cody", "Cody", "Cody Bertram"),
			create("derek", "Derek", "Derek Chowaniec"),
			create("glenn", "Glenn", "Glenn Whittemore"),
			create("grant", "Grant", "Grant Robinson"),
			create("gregory", "Gregory", "Gregory Wolford"),
			create("jacob", "Jacob", "Jacob Martel"),
			create("jeremy", "Jeremy", "Jeremy Anderson"),
			create("johnny", "Johnny", "Johnny Wong"),
			create("kevin", "Kevin", "Kevin Rise"),
			create("scottrum", "Scott Rumrill", "Scott Rumrill"),
			create("scottsim", "Scott Simpson", "Scott Simpson")]

def reset(request):
    if(request.method == "GET"):
        return showReset(request)
    elif(request.method == "POST"):
        return processReset(request)
    
def showReset(request):
    logger.info("Entering showReset")
    return render(request, 'app/reset.html',{})

def processReset(request):
    confirm = ''
    primary = ''
    logger.info("Entering processReset")
    
    usersStatement = None
    listenersStatement = None
    blabsStatement = None
    commentsStatement = None
    now = moment.now().format("YYYY-MM-DD")

    # Drop existing tables and recreate from schema file
    #recreateDatabaseSchema()

    try:
        logger.info("Getting Database connection")
        # Get the Database Connection
        with connection.cursor() as cursor:
            with transaction.atomic():
                # Add the users
                logger.info("Preparing the Stetement for adding users")
                usersStatement = "INSERT INTO users (username, password, password_hint, created_at, last_login, real_name, blab_name) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s');"
                for user in users:
                    logger.info("Adding user " + user.username)
                    cursor.execute(usersStatement % (user.username, user.password, user.password_hint,
                                                     user.last_login, user.real_name, user.blab_name))

            # Add the listeners
            logger.info("Preparing the Statement for adding listeners")
            with transaction.atomic():
                listenersStatement = "INSERT INTO listeners (blabber, listener, status) values ('%s', '%s', 'Active');"
                for blabber in users:
                    for listener in users:
                        if rand.choice([False, True]) and (blabber != listener):
                            

                            logger.info("Adding " + listener.username + " as a listener of " + blabber.username)

                            cursor.execute(listenersStatement % (blabber.username, listener.username))    

            # Fetch pre-loaded Blabs
            logger.info("Reading blabs from file")
            with transaction.atomic():
                blabsContent = loadFile("blabs.txt")

                # Add the blabs
                logger.info("Preparing the Statement for adding blabs")
                blabsStatement = "INSERT INTO blabs (blabber, content, timestamp) values ('%s', '%s', '%s');"
                for blabContent in blabsContent:
                    # Get the array offset for a random user
                    randomUserOffset = rand.randint(len(users) - 1)

                    # get the number or seconds until some time in the last 30 days.
                    vary = rand.randint(0,(30 * 24 * 3600)+1)

                    username = users[randomUserOffset].username
                    logger.info("Adding a blab for " + username)
                    cursor.execute(blabsStatement % (username, blabContent, moment.now().sub(seconds=(vary*1000)).format("YYYY-MM-DD hh:mm:ss")))

            # Fetch pre-loaded Comments
            logger.info("Reading comments from file")
            commentsContent = loadFile("comments.txt")

            # Add the comments
            with transaction.atomic():
                logger.info("Preparing the Statement for adding comments")
                commentsStatement = "INSERT INTO comments (blabid, blabber, content, timestamp) values ('%s', '%s', '%s', '%s');"
                for i in range(len(blabsContent)):
                    # Add a random number of comment
                    count = rand.randint(0,5) # between 0 and 6

                    for j in range(len(count)) :
                        # Get the array offset for a random user
                        randomUserOffset = rand.randint(0,users.length-1) #removed +1 cause no admin,  removed -2 because no admin and inclusive.
                        username = users[randomUserOffset].username

                        # Pick a random comment to add
                        commentNum = rand.randint(0,len(commentsContent)-1)
                        comment = commentsContent[commentNum]

                        # get the number or seconds until some time in the last 30 days.
                        vary = rand.randint(0,(30 * 24 * 3600)+1)

                        logger.info("Adding a comment from " + username + " on blab ID " + str(i))

                        cursor.execute(commentsStatement % (i,username,comment,moment.now().sub(seconds=(vary*1000)).format("YYYY-MM-DD hh:mm:ss")))      
    except IntegrityError as er:
         logger.error(er)
    except sqlite3.Error as ex :
        logger.error(ex.sqlite_errorcode, ex.sqlite_errorname)

    return redirect("reset")



#Drop and recreate the entire database schema

def recreateDatabaseSchema():
    pass
'''
        # Fetch database schema
        logger.info("Reading database schema from file")
        String[] schemaSql = loadFile("blab_schema.sql", new String[] { "--", "/*" }, ";");

        Connection connect = None;
        Statement stmt = None;
        try {
            // Get the Database Connection
            logger.info("Getting Database connection");
            Class.forName("com.mysql.jdbc.Driver");
            connect = DriverManager.getConnection(Constants.create().getJdbcConnectionString());

            stmt = connect.createStatement();

            for (String sql : schemaSql) {
                sql = sql.trim(); // Remove any remaining whitespace
                if (!sql.isEmpty()) {
                    logger.info("Executing: " + sql);
                    System.out.println("Executing: " + sql);
                    stmt.executeUpdate(sql);
                }
            }
        } catch (ClassNotFoundException | SQLException ex) {
            logger.error(ex);
        } finally {
            try {
                if (stmt != None) {
                    stmt.close();
                }
            } catch (SQLException ex) {
                logger.error(ex);
            }
            try {
                if (connect != None) {
                    connect.close();
                }
            } catch (SQLException ex) {
                logger.error(ex);
            }
        }
    }
'''

def loadFile(filename, skipCharacters='', delimiter='/'):
    pass
'''
		path = "/app/src/main/resources" + File.separator + filename;

		regex = ""
		if len(skipCharacters) > 0 :
			skipString = String.join("|", skipCharacters);
			skipString = skipString.replaceAll("(?=[]\\[+&!(){}^\"~*?:\\\\])", "\\\\");
			regex = "^(" + skipString + ").*?";
		}

		String[] lines = null;
		StringBuffer sb = new StringBuffer();
		BufferedReader br = null;
		try {
			br = new BufferedReader(new FileReader(path));

			String line = br.readLine();
			while (line != null) {
				if (line.matches(regex)) {
					line = br.readLine();
					continue;
				}

				sb.append(line);
				sb.append(System.lineSeparator());

				line = br.readLine();
			}

			// Break content by delimiter
			lines = sb.toString().split(delimiter);
		} catch (IOException ex) {
			logger.error(ex);
		} finally {
			try {
				if (br != null) {
					br.close();
				}
			} catch (IOException ex) {
				logger.error(ex);
			}
		}

		return lines;
	}
    '''