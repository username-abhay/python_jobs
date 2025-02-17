from django.shortcuts import render
from .models import JobListing  # ✅ Correct import

def home(request):
    query = request.GET.get('q', '')
    jobs = JobListing.objects.filter(title__icontains=query) if query else JobListing.objects.all()  # ✅ Use JobListing
    return render(request, 'index.html', {'jobs': jobs})
