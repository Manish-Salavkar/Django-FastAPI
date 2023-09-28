# indeedapp\indeed\models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

def generate_unique_key():
    return str(uuid.uuid4())

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    unique_key = models.CharField(max_length=36, default=generate_unique_key,unique=True)

    def __str__(self):
        return self.user.username
