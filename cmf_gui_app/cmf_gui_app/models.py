from django.db import models
class Consumer(models.Model):
    username = models.CharField(max_length=100, null=True)
    phone = models.BigIntegerField(null=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
        
    def __str__(self):
        return self.first_name
