from flask import Blueprint, session, jsonify
import yaml
import urllib.parse
import time
import traceback
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import random

# Create the Blueprint
jobs_bp = Blueprint('jobs', __name__)

# Load resume data from YAML file
def load_resume(yaml_file):
    """Loads and parses the resume YAML file."""
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)

# Generate LinkedIn search URL based on resume preferences
def generate_linkedin_search_url(resume_data):
    """Creates a LinkedIn job search URL with appropriate filters based on resume preferences."""
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {}
    
    # Add location filter
    if resume_data['personal_information'].get('city') and resume_data['personal_information'].get('country'):
        location = f"{resume_data['personal_information']['city']}, {resume_data['personal_information']['country']}"
        params["location"] = location
    
    # Add keywords for skills (use top skills from resume)
    if resume_data.get('skills'):
        top_skills = ", ".join(resume_data['skills'][:5])  # Use top 5 skills
        params["keywords"] = top_skills
    
    query_string = urllib.parse.urlencode(params)
    return base_url + query_string

# Extract Easy Apply jobs without applying filters that require login
def extract_easy_apply_jobs(driver, job_title, max_jobs=2):
    """Extracts job listings that have the Easy Apply option without interacting with filter buttons."""
    try:
        print(f"\nExtracting Easy Apply jobs for: {job_title}")
        
        # Check if redirected to login page with more robust detection
        try:
            login_elements = driver.find_elements(By.CSS_SELECTOR, "#session_key, .login-form")
            if login_elements:
                print("Login page detected. Cannot proceed without authentication.")
                return []
        except Exception:
            pass

        # Wait for any of these job card selectors to be present
        job_card_selectors = [
            "job-card-container",
            "jobs-search-results__list-item",
            "job-card-list__title"
        ]
        
        # Try different selectors with increased timeout
        for selector in job_card_selectors:
            try:
                print(f"Trying selector: {selector}")
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CLASS_NAME, selector))
                )
                print(f"Found elements with selector: {selector}")
                break
            except Exception as e:
                print(f"Selector {selector} not found, trying next...")
                continue
        
        # Add initial pause to let dynamic content load
        time.sleep(5)
        
        # Scroll more gradually
        screen_height = driver.execute_script("return window.screen.height;")
        current_position = 0
        
        for scroll in range(5):  # Increased scroll attempts
            current_position += int(screen_height * 0.5)  # Scroll by half screen height
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(2)  # Wait after each scroll
            
            # Check if we've reached bottom
            scroll_height = driver.execute_script("return document.documentElement.scrollHeight;")
            if current_position > scroll_height:
                break
        
        # Try multiple selectors for job cards
        job_cards = []
        for selector in [
            "job-card-container",
            "jobs-search-results__list-item",
            "job-card-list"
        ]:
            cards = driver.find_elements(By.CLASS_NAME, selector)
            if cards:
                job_cards = cards
                print(f"Found {len(cards)} job cards with selector: {selector}")
                break
        
        if not job_cards:
            print("No job cards found with any selector")
            return []
            
        easy_apply_jobs = []
        for card in job_cards:
            try:
                # Updated selectors for Easy Apply button
                easy_apply_selectors = [
                    ".//button[contains(@class, 'jobs-apply-button')]",
                    ".//div[contains(@class, 'jobs-unified-top-card__content--two-pane')]//span[text()='Easy Apply']",
                    ".//div[contains(@class, 'jobs-apply-button--top-card')]//span[text()='Easy Apply']",
                    ".//div[contains(@class, 'jobs-s-apply')]//button[contains(@class, 'jobs-apply-button')]",
                    ".//div[contains(@class, 'job-card-container__footer')]//span[text()='Easy Apply']"
                ]
                
                found_easy_apply = False
                for selector in easy_apply_selectors:
                    easy_apply_label = card.find_elements(By.XPATH, selector)
                    if easy_apply_label:
                        found_easy_apply = True
                        break
                
                if found_easy_apply:
                    # Updated job title and link selectors
                    title_selectors = [
                        "h3.job-card-list__title",
                        "h3.job-card-container__title",
                        ".job-card-list__title",
                        ".jobs-unified-top-card__job-title"
                    ]
                    
                    link_selectors = [
                        "a.job-card-list__title",
                        "a.job-card-container__link",
                        "a.jobs-unified-top-card__content--two-pane",
                        ".jobs-unified-top-card__content--two-pane a"
                    ]
                    
                    job_link = None
                    for selector in link_selectors:
                        try:
                            link_element = card.find_element(By.CSS_SELECTOR, selector)
                            job_link = link_element.get_attribute("href")
                            if job_link:
                                break
                        except:
                            continue
                    
                    if job_link:
                        easy_apply_jobs.append({"title": job_title, "url": job_link})
                        print(f"Found Easy Apply job: {job_link}")
                        if len(easy_apply_jobs) >= max_jobs:
                            break
            except Exception as e:
                print(f"Error processing job card: {str(e)}")
                continue
        
        return easy_apply_jobs
        
    except TimeoutException as te:
        print(f"Timeout error while loading job cards: {str(te)}")
        print("Page source for debugging:")
        print(driver.page_source[:1000])
        return []
    except Exception as e:
        print(f"Error extracting Easy Apply jobs: {str(e)}")
        return []

# Fetch Easy Apply jobs for multiple job titles without using search box
def fetch_jobs_for_titles(driver, job_titles, base_url):
    """Fetches Easy Apply jobs for multiple job titles by appending keywords to the URL."""
    easy_apply_jobs = []
    for job_title in job_titles:
        if not job_title.strip():
            continue
        try:
            # Append job title as a keyword to the base URL
            encoded_job_title = urllib.parse.quote(job_title)
            search_url = f"{base_url}&keywords={encoded_job_title}"
            print(f"Navigating to URL for {job_title}: {search_url}")
            driver.get(search_url)
            time.sleep(random.uniform(3, 5))  # Wait for page to load
            
            # Extract Easy Apply jobs
            jobs = extract_easy_apply_jobs(driver, job_title)
            easy_apply_jobs.extend(jobs)
            time.sleep(random.uniform(2, 4))  # Avoid rate limiting
        except Exception as e:
            print(f"Error fetching jobs for {job_title}: {str(e)}")
            continue
    return easy_apply_jobs

@jobs_bp.route('/get_recommended_jobs', methods=['GET'])
def get_recommended_jobs():
    try:
        resume_file = session.get('resume_file')
        if not resume_file:
            resume_file = os.path.join(os.path.dirname(__file__), 'uploads', 'final_resume.yaml')
            
        print(f"Looking for resume file at: {resume_file}")
            
        if not os.path.exists(resume_file):
            print(f"File not found at: {resume_file}")
            return jsonify({'error': 'Please complete your information first'}), 400
            
        resume_data = load_resume(resume_file)
        
        job_suggestions = resume_data.get('recommended_jobs', [])
        
        if not job_suggestions:
            return jsonify({'error': 'No recommended jobs found in resume data'}), 400

        if 'personal_information' not in resume_data:
            print("Missing personal_information in resume data")
            resume_data['personal_information'] = {}
            
        city = resume_data['personal_information'].get('city', '')
        country = resume_data['personal_information'].get('country', '')
        
        return jsonify({
            'recommended_jobs': job_suggestions,
            'location': f"{city}, {country}".strip(', ')
        })
    except Exception as e:
        print(f"Error in get_recommended_jobs: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/get_easy_apply_jobs', methods=['GET'])
def get_easy_apply_jobs():
    try:
        resume_file = session.get('resume_file')
        if not resume_file:
            resume_file = os.path.join(os.path.dirname(__file__), 'uploads', 'final_resume.yaml')
            
        if not os.path.exists(resume_file):
            return jsonify({'error': 'Please complete your information first'}), 400
            
        resume_data = load_resume(resume_file)
        
        recommended_jobs = resume_data.get('recommended_jobs', [])
        print(f"Recommended jobs from YAML: {recommended_jobs}")
        
        if not recommended_jobs:
            return jsonify({'error': 'No recommended jobs found in resume data'}), 400
        
        # Initialize browser with options to avoid detection (headless mode)
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Generate base LinkedIn URL
        linkedin_url = generate_linkedin_search_url(resume_data)
        
        # Fetch Easy Apply jobs for all recommended job titles
        easy_apply_jobs = fetch_jobs_for_titles(driver, recommended_jobs, linkedin_url)
        
        driver.quit()
        print(f"Easy Apply jobs found: {easy_apply_jobs}")
        return jsonify(easy_apply_jobs)
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        print(f"Error in get_easy_apply_jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500