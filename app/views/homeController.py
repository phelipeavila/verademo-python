from django.shortcuts import redirect, render

def home(request):
    # Equivalent of HomeController.java
    if request.session.get('username'):
        return redirect('feed')
    
    return render(request, 'app/login.html')