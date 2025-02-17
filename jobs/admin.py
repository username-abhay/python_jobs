from django.contrib import admin
from .models import JobListing

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'salary', 'date_scraped')
    search_fields = ('title', 'company', 'location')
    list_filter = ('date_scraped', 'location')
    fields = ('title', 'company', 'location', 'salary', 'date_scraped')
