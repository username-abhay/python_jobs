# save as 'scrape_jobs.py'
import os
import django
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from pymongo import MongoClient
import time
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')
django.setup()

# Import our Job model
from jobs.models import JobListing

def scrape_indeed_jobs(max_pages=2):
    """Scrape jobs and save directly to MongoDB"""
    print("\nStarting the scraper...")
    
    # Connect to MongoDB first
    client = MongoClient('mongodb://localhost:27017/')
    db = client['job_database']
    raw_jobs = db['raw_scraped_jobs']  # Collection for raw data
    
    # Clear old scraped data
    raw_jobs.delete_many({})
    
    driver = uc.Chrome(options=uc.ChromeOptions())
    
    try:
        for page in range(max_pages):
            print(f"\nScraping page {page + 1}...")
            
            url = f"https://www.indeed.com/jobs?q=Python+Developer&l=New+York&start={page*10}"
            driver.get(url)
            time.sleep(random.uniform(2, 5))
            
            job_cards = driver.find_elements(By.CLASS_NAME, 'job_seen_beacon')
            
            for card in job_cards:
                try:
                    job_data = {
                        'title': card.find_element(By.CLASS_NAME, 'jobTitle').text,
                        'company': card.find_element(By.CLASS_NAME, 'companyName').text,
                        'location': card.find_element(By.CLASS_NAME, 'companyLocation').text,
                        'salary': 'Not listed',
                        'raw_html': card.get_attribute('innerHTML'),  # Save raw HTML for later processing
                        'date_scraped': datetime.now(),
                        'processed': False  # Flag to track which jobs we've processed
                    }
                    
                    # Try to get salary
                    try:
                        job_data['salary'] = card.find_element(By.CLASS_NAME, 'salary-snippet').text
                    except:
                        pass
                    
                    # Save directly to MongoDB
                    raw_jobs.insert_one(job_data)
                    print(f"Scraped: {job_data['title']} at {job_data['company']}")
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"Error processing a job card: {str(e)}")
                    continue
            
            time.sleep(random.uniform(3, 7))
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    finally:
        driver.quit()
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
    num_scraped = scrape_indeed_jobs(max_pages=2)
    print(f"\n✓ Scraped {num_scraped} jobs to MongoDB!")
    
    # Step 2: Process and add to Django
    print("\nProcessing jobs for display...")
    num_processed = process_and_display_jobs()
    print(f"✓ Added {num_processed} jobs to Django admin!")
    
    print("\nDone! You can now:")
    print("1. View processed jobs in Django admin: http://127.0.0.1:8000/admin")
    print("2. View raw scraped data in MongoDB Compass")