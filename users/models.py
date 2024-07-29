from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.


class User(AbstractUser):
    school_name = models.CharField(max_length=255, null=True, blank=True)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return self.email
