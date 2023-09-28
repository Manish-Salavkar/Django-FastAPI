# indeedapp\indeedapp\urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include("indeed.urls")),
    path('admin/', admin.site.urls),
    # path('api/', include('jobapi_app.urls')),
]