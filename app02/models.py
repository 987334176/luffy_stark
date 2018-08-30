from django.db import models

# Create your models here.
class Role(models.Model):
    title = models.CharField(verbose_name="名称", max_length=32)
