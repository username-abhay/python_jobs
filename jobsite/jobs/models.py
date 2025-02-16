from django.db import models

class JobListing(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    salary = models.CharField(max_length=100)
    date_scraped = models.DateField()

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-date_scraped']