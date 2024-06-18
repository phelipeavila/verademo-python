# VeraDemo - Blab-a-Gag (Django-Python)

### Notice

This project is intentionally vulnerable! It contains known vulnerabilities and security errors in its code and is meant as an example project for software security scanning tools such as Veracode. Please do not report vulnerabilities in this project; the odds are they’re there on purpose :) .

## About

Blab-a-Gag is a fairly simple forum type application which allows:

- Users can post a one-liner joke.
- Users can follow the jokes of other users or not (listen or ignore).
- Users can comment on other users messages (heckle).

### URLs

- `/feed` shows the jokes/heckles that are relevant to the current user.
- `/blabbers` shows a list of all other users and allows the current user to listen or ignore.
- `/profile` allows the current user to modify their profile.
- `/login` allows you to log in to your account
- `/register` allows you to create a new user account
- `/tools` shows a tools page that shows a fortune or lets you ping a host.
- `/reset` allows the user to reset the database

## Run

If you don't already have Docker this is a prerequisite.

To build the container run this:

    docker pull cshtino/verademo;
    docker build --no-cache -t verademo-python .

To run the container for local development run this:

    docker run --rm -p 8080:8080 --name verademo verademo-python

Navigate to: `http://127.0.0.1:8080`.

Then register as a new user and add some feeds

## Run locally without Docker

To run the program locally without using docker run this:

    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    python manage.py runserver

To be able to use the fortune feature in tools (UNIX exclusive), run this:
    apt-get install -y fortune-mod

Navigate to: `http://127.0.0.1:8000`

## Exploitation Demos

See the [DEMO_NOTES](DEMO_NOTES.md) file for information on using this application with the various Veracode scan types.

Also see the `docs` folder for in-depth explanations of the various exploits exposed in this application.


## Technologies Used

- Django (Version 4.2.13)
- sqlite3 (Supported by Django)
