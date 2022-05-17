from django.db import models


class UrlToParse(models.Model):
    url_id = models.AutoField(primary_key=True)
    url_to_parse = models.URLField(max_length=400, unique=True, null=True)

    def __lt__(a, b):
        return b if a.url_id < b.url_id else a

    def __str__(self):
        return self.url_to_parse


class ParsedUrl(models.Model):
    from_url = models.ForeignKey(UrlToParse, on_delete=models.CASCADE, null=True, blank=True, related_name='entries')
    found_url = models.URLField(max_length=400, null=True)
    domain = models.CharField(max_length=200, null=True)
    create_date = models.CharField(max_length=100, null=True)
    update_date = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=30, null=True)
    isDead = models.CharField(max_length=100, null=True)
    A = models.CharField(max_length=500, null=True)
    NS = models.CharField(max_length=500, null=True)
    CNAME = models.CharField(max_length=500, null=True)
    MX = models.CharField(max_length=500, null=True)
    TXT = models.CharField(max_length=500, null=True)

    def __lt__(a, b):
        return b if a.found_url < b.found_url else a

    def __str__(self):
        return self.found_url
