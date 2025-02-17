# save as 'scrape_jobs.py'
import os
import django
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import MongoClient
import time
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')
django.setup()

# Import our Job model
from jobs.models import JobListing

# Your ScraperAPI key - replace with your actual key
SCRAPER_API_KEY = '70fa9b5ea300ee044d538daf4ed16ade' 

def scrape_indeed_jobs(max_pages=2):
    """Scrape jobs using ScraperAPI"""
    print("\nStarting the scraper...")
    
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['job_database']
    raw_jobs = db['raw_scraped_jobs']
    
    # Clear old scraped data
    raw_jobs.delete_many({})
    
    total_jobs = 0
    
    for page in range(max_pages):
        try:
            print(f"\nScraping page {page + 1}...")
            
            # Using Indian Indeed website instead and simplified URL structure
            payload = {
                'api_key': SCRAPER_API_KEY,
                'url': f'https://in.indeed.com/jobs?q=Python+Developer&l=India&start={page*10}',
                'device_type': 'desktop'  # Added this parameter
            }
            
            response = requests.get('https://api.scraperapi.com/', params=payload)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in job_cards:
                    try:
                        # Updated class names to match Indeed India
                        title = card.find('h2', class_='jobTitle')
                        company = card.find('span', class_='css-1h7lukg')
                        location = card.find('div', class_='company_location')
                        salary = card.find('div', class_='salary-snippet-container')
                        
                        job_data = {
                            'title': title.text.strip() if title else 'Unknown Title',
                            'company': company.text.strip() if company else 'Unknown Company',
                            'location': location.text.strip() if location else 'Unknown Location',
                            'salary': salary.text.strip() if salary else 'Not listed',
                            'raw_html': str(card),
                            'date_scraped': datetime.now(),
                            'processed': False
                        }
                        
                        # Save to MongoDB
                        raw_jobs.insert_one(job_data)
                        print(f"Scraped: {job_data['title']} at {job_data['company']}")
                        total_jobs += 1
                        
                    except Exception as e:
                        print(f"Error processing a job card: {str(e)}")
                        continue
                
                # Sleep between pages
                time.sleep(2)
                
            else:
                print(f"Error: Got status code {response.status_code}")
                print(f"Error details: {response.text}")
                
        except Exception as e:
            print(f"Error scraping page {page + 1}: {str(e)}")
    
    return total_jobs

# Rest of your code remains the same...

def process_and_display_jobs():
    """Process jobs from MongoDB and display in Django admin"""
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['job_database']
        raw_jobs = db['raw_scraped_jobs']
        
        JobListing.objects.all().delete()
        unprocessed_jobs = raw_jobs.find({'processed': False})
        
        jobs_added = 0
        
        for job in unprocessed_jobs:
            cleaned_job = {
                'title': job['title'].strip(),
                'company': job['company'].strip(),
                'location': job['location'].strip(),
                'salary': job['salary'].strip() if job['salary'] != 'Not listed' else 'Not listed',
                'date_scraped': job['date_scraped']
            }
            
            JobListing.objects.create(**cleaned_job)
            
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
    print("Starting job scraping...")
    num_scraped = scrape_indeed_jobs(max_pages=2)
    print(f"\n✓ Scraped {num_scraped} jobs to MongoDB!")
    
    print("\nProcessing jobs for display...")
    num_processed = process_and_display_jobs()
    print(f"✓ Added {num_processed} jobs to Django admin!")