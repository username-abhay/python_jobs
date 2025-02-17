from django.shortcuts import render
from .models import JobListing  # Make sure this import is correct

def home(request):
    jobs = JobListing.objects.all().order_by('-date_scraped')  # Add ordering by newest first
    query = request.GET.get('q', '')
    if query:
        jobs = jobs.filter(title__icontains=query)
    print(f"Number of jobs found: {jobs.count()}")  # Add this debug line
    return render(request, 'index.html', {'jobs': jobs})
