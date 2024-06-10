from django.shortcuts import redirect, render
from django.db import connection, transaction

from app.models import User
from app.views import create

import logging, random
# START VULNERABLE PACKAGE
import moment
# END

##################RESET CONTROLLER#####################
logger = logging.getLogger("__name__")

users = [create("admin", "admin", "Thats Mr Administrator to you."),
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
'''
    rand = random.random()

    # Drop existing tables and recreate from schema file
    #recreateDatabaseSchema()

    try:
        logger.info("Getting Database connection")
        # Get the Database Connection
        with transaction.atomic():
            with connection.cursor() as cursor:

                # Add the users
                logger.info("Preparing the Stetement for adding users")
                usersStatement = "INSERT INTO users (username, password, password_hint, created_at, last_login, real_name, blab_name) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s');"
                for user in users:
                    logger.info("Adding user " + user.username)
                    cursor.execute(usersStatement % (user.username, user.password, user.password_hint,
                                                     user.last_login, user.real_name, user.blab_name))

        # Add the listeners
        logger.info("Preparing the Stetement for adding listeners")
        listenersStatement = "INSERT INTO listeners (blabber, listener, status) values ('%s', '%s', 'Active');"
        for (int i = 1; i < users.length; i++) {
            for (int j = 1; j < users.length; j++) {
                if (rand.nextBoolean() && i != j) {
                    String blabber = user.getUserName();
                    String listener = users[j].getUserName();

                    logger.info("Adding " + listener + " as a listener of " + blabber);

                    listenersStatement.setString(1, blabber);
                    listenersStatement.setString(2, listener);

                    listenersStatement.executeUpdate();
                }
            }
        }
        connect.commit();

        // Fetch pre-loaded Blabs
        logger.info("Reading blabs from file");
        String[] blabsContent = loadFile("blabs.txt");

        // Add the blabs
        logger.info("Preparing the Statement for adding blabs");
        blabsStatement = connect
                .prepareStatement("INSERT INTO blabs (blabber, content, timestamp) values ('%s', '%s', '%s');");
        for (String blabContent : blabsContent) {
            // Get the array offset for a random user, except admin who's offset 0.
            int randomUserOffset = rand.nextInt(users.length - 2) + 1;

            // get the number or seconds until some time in the last 30 days.
            long vary = rand.nextInt(30 * 24 * 3600);

            String username = users[randomUserOffset].getUserName();
            logger.info("Adding a blab for " + username);

            blabsStatement.setString(1, username);
            blabsStatement.setString(2, blabContent);
            blabsStatement.setTimestamp(3, new Timestamp(now.getTime() - (vary * 1000)));

            blabsStatement.executeUpdate();
        }
        connect.commit();

        // Fetch pre-loaded Comments
        logger.info("Reading comments from file");
        String[] commentsContent = loadFile("comments.txt");

        // Add the comments
        logger.info("Preparing the Statement for adding comments");
        commentsStatement = connect.prepareStatement(
                "INSERT INTO comments (blabid, blabber, content, timestamp) values ('%s', '%s', '%s', '%s');");
        for (int i = 1; i <= blabsContent.length; i++) {
            // Add a random number of comment
            int count = rand.nextInt(6); // (between 0 and 6)

            for (int j = 0; j < count; j++) {
                // Get the array offset for a random user, except admin who's offset 0.
                int randomUserOffset = rand.nextInt(users.length - 2) + 1;
                String username = users[randomUserOffset].getUserName();

                // Pick a random comment to add
                int commentNum = rand.nextInt(commentsContent.length);
                String comment = commentsContent[commentNum];

                // get the number or seconds until some time in the last 30 days.
                long vary = rand.nextInt(30 * 24 * 3600);

                logger.info("Adding a comment from " + username + " on blab ID " + String.valueOf(i));
                commentsStatement.setInt(1, i);
                commentsStatement.setString(2, username);
                commentsStatement.setString(3, comment);
                commentsStatement.setTimestamp(4, new Timestamp(now.getTime() - (vary * 1000)));

                commentsStatement.executeUpdate();
            }
        }
        connect.commit();
    except SQLException | ClassNotFoundException ex :
        logger.error(ex);
    return redirect("reset");



#Drop and recreate the entire database schema

def recreateDatabaseSchema():
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
def create(userName, blabName,realName):
    password = userName
    dateCreated = moment.now().format("YYYY-MM-DD hh:mm:ss")
    lastLogin = None

    return User(userName, password, dateCreated, lastLogin, blabName, realName)