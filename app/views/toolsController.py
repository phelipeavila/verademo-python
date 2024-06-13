# toolsController.py deals with the 'Tools' page and calls the tool functions used in the page
import logging
import subprocess
import sys
import shutil

from django.shortcuts import render



logger = logging.getLogger("VeraDemo:toolsController")

# Redirects request based on type
def tools(request):
    if(request.method == "GET"):
        return showTools(request)
    elif(request.method == "POST"):
        return processTools(request)

# Loads the tool webpage    
def showTools(request):
    host = request.META['SERVER_NAME']
    return render(request, 'app/tools.html', { 'host' : host })

# Performs the actions on the tool page, updating output accordingly
def processTools(request):
    host = request.POST.get('host')
    fortunefile = request.POST.get('fortunefile')
    request.file = fortune(fortunefile) if fortunefile else ""
    request.ping = ping(host) if host else ""
    
    

    return render(request, 'app/tools.html', {"host" : host})

# pings selected host and outputs the result
def ping(host):
    output = ""
    print("Pinging", host)
    try:
        p = subprocess.Popen(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = p.communicate(timeout=5)
    
        output = stdout.decode() if stdout else ""
        print("Exit Code:", p.returncode)
    except subprocess.TimeoutExpired:
        print("Ping timed out")
    except Exception as e:
        print("Error:", e)

    return output

'''
def pingView(request):
    host = request.POST.get('host')
    result =""
    if host:
        try:
            result = ping(host)
        except Exception as e:
            result = f"Error: {e}"
            print("Error:", e)


    return render(request, 'app/tools.html', {'result': result, 'host': host})
'''

# Produces a fortune based on the submitted selection
def fortune(file):
    cmd = f"/usr/games/fortune {file}"
    output = ""
    logger.info(output)
    logger.info("fortune:\n")
    sys.stdout.flush()

    if shutil.which("fortune") is None:
        logger.info("After")
        sys.stdout.flush()
        return "fortune not found"

    try: 
        p = subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("fortune after try1:\n")
        sys.stdout.flush()
        try:
            stdout, stderr = p.communicate(timeout=5)
            output = stdout.decode() if stdout else ""
            logger.info("fortune output:\n")
            sys.stdout.flush()
        except subprocess.TimeoutExpired:
            logger.info("Fortune timed out")
            sys.stdout.flush()
        except Exception as e:
            logger.info("Error:", e)
            sys.stdout.flush()
    except Exception as e:
        logger.info("Error:", e)
        sys.stdout.flush()
        
    return output

'''
def fortuneView(request):
    file = request.POST.get('file')
    result = ""
    if file:
        try:
            result = fortune(file)
        except Exception as e:
            result = f"Error: {e}"
            print("Error:", e)

    return render(request, 'app/tools.html', {'result': result, 'file': file})
'''



   