from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.UrlToParse)
admin.site.register(models.ParsedUrl)
