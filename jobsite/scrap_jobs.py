# save as 'scrape_jobs.py'
import os
import django
import subprocess
import json
from datetime import datetime
from pymongo import MongoClient
import time
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')
django.setup()

# Import our Job model
from jobs.models import JobListing

def fetch_jobs():
    """Fetch jobs using ScrapingDog API via curl."""
    api_key = "67b12f27b835588da42c318d"
    indeed_url = "https://in.indeed.com/jobs?q=python+developer&l=&from=searchOnDesktopSerp&vjk=d534c8f4505aa945"

    # Construct the cURL command
    curl_command = [
        "curl", "https://api.scrapingdog.com/indeed",
        "-d", f"api_key={api_key}",
        "-d", f"url={indeed_url}"
    ]

    # Execute the cURL command
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)  # Parse the JSON response
        
        if data:
            return data
        else:
            print("No jobs found.")
            return []
    
    except subprocess.CalledProcessError as e:
        print(f"Error fetching jobs: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to parse JSON response.")
        return []

def scrape_indeed_jobs():
    """Scrape jobs and save directly to MongoDB"""
    print("\nStarting the scraper...")
    
    # Connect to MongoDB first
    client = MongoClient('mongodb://localhost:27017/')
    db = client['job_database']
    raw_jobs = db['raw_scraped_jobs']  # Collection for raw data
    
    # Clear old scraped data
    raw_jobs.delete_many({})
    
    # Fetch jobs from API
    jobs = fetch_jobs()
    
    # Store fetched jobs in MongoDB
    for job in jobs:
        job_data = {
            'title': job.get('title', 'Unknown'),
            'company': job.get('company', 'Unknown'),
            'location': job.get('location', 'Unknown'),
            'salary': job.get('salary', 'Not listed'),
            'date_scraped': datetime.now(),
            'processed': False  # Flag to track which jobs we've processed
        }
        raw_jobs.insert_one(job_data)
        print(f"Scraped: {job_data['title']} at {job_data['company']}")
    
    return raw_jobs.count_documents({})  # Return number of jobs scraped

def process_and_display_jobs():
    """Process jobs from MongoDB and display in Django admin"""
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['job_database']
        raw_jobs = db['raw_scraped_jobs']
        
        # Clear existing jobs from Django
        JobListing.objects.all().delete()
        
        # Get all unprocessed jobs
        unprocessed_jobs = raw_jobs.find({'processed': False})
        
        jobs_added = 0
        
        for job in unprocessed_jobs:
            # Clean and process the data
            cleaned_job = {
                'title': job['title'].strip(),
                'company': job['company'].strip(),
                'location': job['location'].strip(),
                'salary': job['salary'].strip() if job['salary'] != 'Not listed' else 'Not listed',
                'date_scraped': job['date_scraped']
            }
            
            # Add to Django database
            JobListing.objects.create(**cleaned_job)
            
            # Mark as processed in MongoDB
            raw_jobs.update_one(
                {'_id': job['_id']},
                {'$set': {'processed': True}}
            )
            
            jobs_added += 1
            
        return jobs_added
        
    except Exception as e:
        print(f"Error processing jobs: {str(e)}")
        return 0

if __name__ == "__main__":
    # Step 1: Scrape and save to MongoDB
    print("Starting job scraping...")
    num_scraped = scrape_indeed_jobs()
    print(f"\n✓ Scraped {num_scraped} jobs to MongoDB!")
    
    # Step 2: Process and add to Django
    print("\nProcessing jobs for display...")
    num_processed = process_and_display_jobs()
    print(f"✓ Added {num_processed} jobs to Django admin!")
    
    print("\nDone! You can now:")
    print("1. View processed jobs in Django admin: http://127.0.0.1:8000/admin")
    print("2. View raw scraped data in MongoDB Compass")
