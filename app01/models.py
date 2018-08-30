from django.db import models

# Create your models here.
class UserInfo(models.Model):
    username = models.CharField(verbose_name="用户名",max_length=32)