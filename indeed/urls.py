# indeedapp\indeed\urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("joblistings", views.joblistings_view, name="job_listings"),
    path("signup", views.signup_view, name="signup"),
    path("signin", views.signin_view, name="signin"),
    path("signout", views.signout_view, name="signout"),
    path('user/<str:username>/', views.user_view, name='user_view'),
    path('bookmark_view', views.bookmark_view, name='bookmark_view'),
]
    