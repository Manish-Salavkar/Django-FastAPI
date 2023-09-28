# indeedapp\indeed\views.py
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.sessions.models import Session
from .models import UserProfile
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import uuid
import requests

def joblistings_view(request):
    return render(request, "indeed/job_listings.html")



def home_view(request):
    return render(request, "indeed/home.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        fname = request.POST["fname"]
        lname = request.POST["lname"]
        email = request.POST["email"]
        pass1 = request.POST["pass1"]
        pass2 = request.POST["pass2"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('home')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('home')

        try:
            myuser = User.objects.create_user(username, email, pass1)
            myuser.first_name = fname
            myuser.last_name = lname

            myuser.save()

            unique_key = uuid.uuid4().hex
            user_profile = UserProfile(user=myuser, first_name=fname, last_name=lname, email=email, unique_key=unique_key)
            user_profile.save()

            messages.success(request, "Your account has been successfully created")

            response = save_user_profile_api(request, myuser)


            return redirect('signin')
        
        except IntegrityError:
            messages.error(request, "An error occured while creating your account. Please try again")
            return redirect('signup')
    return render(request,"indeed/signup.html")



def signin_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)

            user_profile = UserProfile.objects.get(user=user)

            request.session['user_id'] = user_profile.user.id
            request.session['unique_key'] = user_profile.unique_key
            
            return redirect(reverse('user_view', args=[username]))
        
        else:
            messages.error(request, "Bad Credentials")
            return redirect('signin')
    return render(request,"indeed/signin.html")


@login_required(login_url='signin')
def user_view(request, username):
    try:
        user = User.objects.get(username=username)
        return render(request, "indeed/user.html", {'user': user})
    except User.DoesNotExist:
        return redirect('signin')



def signout_view(request):
    logout(request)
    messages.add_message(request, messages.SUCCESS, "Logged Out Successfully", extra_tags="success")
    return redirect('home')


def save_user_profile_api(request, myuser):
    user_id = myuser.id
    first_name = myuser.first_name
    last_name = myuser.last_name
    unique_key = myuser.userprofile.unique_key

    user_profile_data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "unique_key": unique_key,
    }

    response = requests.post("http://127.0.0.1:8000/save_user_profile", json=user_profile_data)

    return response

@require_POST
def bookmark_view(request):
    if request.method == 'POST':
        fccid = request.POST.get('fccid')
        user_profile_id = request.session.get('user_id')
        user_unique_key = request.session.get('unique_key')

        if request.user.is_authenticated:
            bookmark_data = {
                "user_id": user_profile_id,
                "fccid": fccid,
                "unique_key": user_unique_key,
            }

            response = requests.post("http://127.0.0.1:8000/save_bookmark", json=bookmark_data)
        
            if response.status_code == 200:
                return JsonResponse({"message": "Bookmark added successfully"})
            else:
                return JsonResponse({"message": "Failed to add bookmark"})

        else:
            return JsonResponse({"message": "Please Sign in to bookmark"})
        
@require_POST
def remove_bookmark_view(request):
    if request.method == 'POST':
        fccid = request.POST.get('fccid')
        user_profile_id = request.session.get('user_id')
        user_unique_key = request.session.get('unique_key')

        if request.user.is_authenticated:
            bookmark_data = {
                "user_id": user_profile_id,
                "fccid": fccid,
                "unique_key": user_unique_key,
            }

            response = requests.post("http://127.0.0.1:8000/remove_bookmark", json=bookmark_data)
        
            if response.status_code == 200:
                return JsonResponse({"message": "Bookmark removed successfully"})
            else:
                return JsonResponse({"message": "Failed to remove bookmark"})

        

