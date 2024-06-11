from django.shortcuts import render

import logging
import subprocess

logger = logging.getLogger("VeraDemo:toolsController")

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

    return render(request, 'app/tools.html')

def ping(host):
    output = ""
    
    try:
        p = subprocess.Popen(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = p.communicate(timeout=5)
    
        output = stdout.decode() if stdout else ""
        logger.info("Exit Code:" + str(p.returncode))
    except subprocess.TimeoutExpired:
        logger.error("Ping request timed out")
    except Exception as e:
        logger.error("Error occurred:", e)
    # TO FIX ERROR, CRASH ON PING
    # return render(output, 'app/tools.html')
    return output

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