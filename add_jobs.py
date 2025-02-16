# save this as 'add_jobs.py' in your jobsite folder
import os
import django
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
import time

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')
django.setup()

# Import our Job model
from jobs.models import JobListing

def check_mongodb_connection():
    """Try to connect to MongoDB and return True if successful"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()  # This will raise an exception if can't connect
        print("✓ Successfully connected to MongoDB!")
        return True
    except Exception as e:
        print("\n❌ Cannot connect to MongoDB! Make sure it's running!")
        print("\nTo fix this:")
        print("1. Open Services (Run -> services.msc)")
        print("2. Find 'MongoDB' in the list")
        print("3. Right-click and select 'Start'")
        print("4. Try running this script again")
        print(f"\nTechnical error: {str(e)}")
        return False

def create_sample_jobs():
    # Create sample jobs
    jobs = [
        {
            "title": "Junior Python Developer",
            "company": "Tech Solutions Inc",
            "location": "New York, NY",
            "salary": "$75,000 per year",
            "date_scraped": datetime.now() - timedelta(days=1)
        },
        {
            "title": "Python Backend Developer",
            "company": "StartUp Hub",
            "location": "New York, NY",
            "salary": "$95,000 per year",
            "date_scraped": datetime.now()
        },
        {
            "title": "Python Full Stack Developer",
            "company": "Big Corp Technologies",
            "location": "Brooklyn, NY",
            "salary": "$85,000 - $110,000 per year",
            "date_scraped": datetime.now()
        },
        {
            "title": "Python Data Engineer",
            "company": "Data Systems LLC",
            "location": "Manhattan, NY",
            "salary": "$90,000 per year",
            "date_scraped": datetime.now() - timedelta(days=2)
        },
        {
            "title": "Django Developer",
            "company": "Web Solutions Co",
            "location": "Queens, NY",
            "salary": "Not listed",
            "date_scraped": datetime.now()
        }
    ]
    
    return jobs

def save_to_mongodb(jobs):
    """Save jobs to MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['job_database']
        collection = db['python_jobs']
        
        # Delete old jobs
        collection.delete_many({})
        
        # Convert datetime objects to strings for MongoDB
        jobs_for_mongo = []
        for job in jobs:
            job_copy = job.copy()
            job_copy['date_scraped'] = job_copy['date_scraped'].strftime('%Y-%m-%d')
            jobs_for_mongo.append(job_copy)
        
        # Insert jobs
        collection.insert_many(jobs_for_mongo)
        print(f"✓ Saved {len(jobs)} jobs to MongoDB!")
        
    except Exception as e:
        print(f"❌ Error saving to MongoDB: {str(e)}")
        return False
    
    return True

def save_to_django(jobs):
    """Save jobs to Django database"""
    try:
        # Clear old jobs
        JobListing.objects.all().delete()
        
        # Add new jobs
        for job in jobs:
            JobListing.objects.create(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                salary=job['salary'],
                date_scraped=job['date_scraped']
            )
        print(f"✓ Saved {len(jobs)} jobs to Django database!")
        
    except Exception as e:
        print(f"❌ Error saving to Django: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("\nChecking MongoDB connection...")
    if not check_mongodb_connection():
        print("\nExiting... Please start MongoDB and try again!")
        sys.exit(1)
    
    print("\nCreating sample jobs...")
    jobs = create_sample_jobs()
    print(f"✓ Created {len(jobs)} sample jobs!")
    
    print("\nSaving to MongoDB...")
    mongo_success = save_to_mongodb(jobs)
    
    print("\nSaving to Django database...")
    django_success = save_to_django(jobs)
    
    if mongo_success and django_success:
        print("\n✓ All done! You can now:")
        print("1. View jobs in Django admin: http://127.0.0.1:8000/admin")
        print("2. View jobs in MongoDB Compass by connecting to: mongodb://localhost:27017")
    else:
        print("\n❌ There were some errors. Please check the messages above.")