import google.generativeai as genai
import yaml
import requests
import webbrowser
import urllib.parse
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configure Gemini API key
GENAI_API_KEY = "AIzaSyAfAZy6iQYSoTnUNegAfIGY2ZekI5K3x20"
genai.configure(api_key=GENAI_API_KEY)

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
    
    # Construct the basic URL - we'll apply other filters via Selenium
    query_string = urllib.parse.urlencode(params)
    return base_url + query_string

# AI-Powered Job Suggestions
def suggest_jobs(resume_data):
    """
    Suggest jobs based on resume data
    """
    # Extract skills and experience
    skills = resume_data.get('skills', [])
    projects = resume_data.get('projects', [])
    experience = resume_data.get('experience', [])
    
    # Collect all technologies from projects
    tech_stack = []
    for project in projects:
        if project.get('technologies'):
            techs = project['technologies'].split(',')
            tech_stack.extend([t.strip() for t in techs])
    
    # Combine all skills
    all_skills = set(skills + tech_stack)
    
    # Define job suggestions based on skills
    job_suggestions = []
    
    # Check for development roles
    dev_skills = {'python', 'javascript', 'react', 'typescript', 'flask', 'selenium'}
    if any(skill.lower() in dev_skills for skill in all_skills):
        job_suggestions.extend([
            'Software Developer',
            'Full Stack Developer',
            'Python Developer',
            'React Developer'
        ])
    
    # Check for AI/ML roles
    ai_skills = {'pytorch', 'machine learning', 'ai', 'hugging face', 'nlp'}
    if any(skill.lower() in ai_skills for skill in all_skills):
        job_suggestions.extend([
            'Machine Learning Engineer',
            'AI Developer',
            'NLP Engineer',
            'Deep Learning Engineer'
        ])
    
    # Check for automation roles
    auto_skills = {'selenium', 'automation', 'testing'}
    if any(skill.lower() in auto_skills for skill in all_skills):
        job_suggestions.extend([
            'Automation Engineer',
            'QA Automation Engineer',
            'Test Automation Developer'
        ])
    
    # Add some general roles based on the skill set
    job_suggestions.extend([
        'Software Engineer',
        'Backend Developer',
        'Frontend Developer'
    ])
    
    # Remove duplicates and return
    return list(set(job_suggestions))

def generate_linkedin_search_url(job_title, location):
    """
    Generate LinkedIn job search URL with Easy Apply filter
    """
    # Format job title and location for URL
    formatted_title = urllib.parse.quote(job_title)
    formatted_location = urllib.parse.quote(location)
    
    # Create LinkedIn search URL with Easy Apply filter
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = f"keywords={formatted_title}&location={formatted_location}&f_TPR=r86400&f_AL=true&position=1&pageNum=0"
    
    return base_url + params

# Click a button safely with fallbacks
def safe_click(driver, element, wait_time=2):
    """Attempts to click an element safely with multiple methods."""
    try:
        # Try direct click first
        element.click()
        time.sleep(wait_time)
        return True
    except Exception:
        try:
            # Try JavaScript click if direct click fails
            driver.execute_script("arguments[0].click();", element)
            time.sleep(wait_time)
            return True
        except Exception:
            return False

# Apply Experience Level filter dynamically
def apply_experience_level_filter(driver, resume_data):
    """Dynamically applies Experience Level filter by finding and clicking DOM elements."""
    try:
        print("Applying Experience Level filter...")
        
        # Find and click the Experience level dropdown button
        exp_level_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-pill') and contains(., 'Experience level')]"))
        )
        safe_click(driver, exp_level_button)
        time.sleep(2)
        
        # Map resume experience levels to text that will appear in the dropdown
        # This addresses the need to match against visible text rather than fixed IDs
        experience_map = {
            "Entry Level": "Entry level",
            "Internship": "Internship",
            "Associate": "Associate",
            "Mid-Senior level": "Mid-Senior level",
            "Director": "Director",
            "Executive": "Executive"
        }
        
        # Check the desired experience levels from resume
        if resume_data['job_preferences'].get('experience_level'):
            for level in resume_data['job_preferences']['experience_level']:
                if level in experience_map:
                    level_text = experience_map[level]
                    try:
                        # Find the checkbox by looking for the label text
                        level_option = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, 
                                f"//span[contains(text(), '{level_text}')]/ancestor::label/preceding-sibling::input[@type='checkbox']"))
                        )
                        safe_click(driver, level_option)
                        print(f"Selected experience level: {level_text}")
                    except Exception as e:
                        # Alternative approach: find label first, then click
                        try:
                            level_label = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{level_text}')]/ancestor::label"))
                            )
                            safe_click(driver, level_label)
                            print(f"Selected experience level (via label): {level_text}")
                        except Exception as e:
                            print(f"Could not select experience level {level}: {str(e)}")
        
        # Click Show results button
        show_results = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show results')]"))
        )
        safe_click(driver, show_results)
        print("Applied Experience Level filter successfully")
        return True
    
    except Exception as e:
        print(f"Error applying experience level filter: {str(e)}")
        traceback.print_exc()
        return False

# Apply Remote/On-site filter dynamically
def apply_workplace_filter(driver, resume_data):
    """Dynamically applies Remote/On-site filter based on resume preferences."""
    try:
        print("Applying Workplace filter...")
        
        # Find and click the Remote dropdown button
        remote_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-pill') and contains(., 'Remote')]"))
        )
        safe_click(driver, remote_button)
        time.sleep(2)
        
        # Map work preferences to visible text in the dropdown
        workplace_map = {
            "On-site": "On-site",
            "Remote": "Remote",
            "Hybrid": "Hybrid"
        }
        
        # Select appropriate workplace type based on resume preferences
        if resume_data['work_preferences'].get('remote_work') == 'No' and resume_data['work_preferences'].get('in_person_work') == 'Yes':
            workplace_text = "On-site"
        elif resume_data['work_preferences'].get('remote_work') == 'Yes':
            workplace_text = "Remote"
        else:
            # Default case
            workplace_text = "On-site"
        
        try:
            # Find the checkbox by looking for the label text
            workplace_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    f"//span[contains(text(), '{workplace_text}')]/ancestor::label/preceding-sibling::input[@type='checkbox']"))
            )
            safe_click(driver, workplace_option)
            print(f"Selected workplace type: {workplace_text}")
        except Exception as e:
            # Alternative approach: find label first, then click
            try:
                workplace_label = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{workplace_text}')]/ancestor::label"))
                )
                safe_click(driver, workplace_label)
                print(f"Selected workplace type (via label): {workplace_text}")
            except Exception as e:
                print(f"Could not select workplace type {workplace_text}: {str(e)}")
        
        # Click Show results button
        show_results = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show results')]"))
        )
        safe_click(driver, show_results)
        print("Applied Workplace filter successfully")
        return True
    
    except Exception as e:
        print(f"Error applying workplace filter: {str(e)}")
        traceback.print_exc()
        return False

# Apply Date Posted filter
def apply_date_posted_filter(driver):
    """Applies Date Posted filter to show recent jobs."""
    try:
        print("Applying Date Posted filter...")
        
        # Find and click the Date posted dropdown
        date_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-pill') and contains(., 'Date posted')]"))
        )
        safe_click(driver, date_button)
        time.sleep(2)
        
        # Try to find and click "Past month" using text
        try:
            month_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Past month')]/ancestor::label/preceding-sibling::input[@type='radio']"))
            )
            safe_click(driver, month_option)
            print("Selected 'Past month' option")
        except Exception:
            # Alternative: try the label approach
            try:
                month_label = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Past month')]/ancestor::label"))
                )
                safe_click(driver, month_label)
                print("Selected 'Past month' option via label")
            except Exception as e:
                print(f"Could not select 'Past month' option: {str(e)}")
        
        # Click Show results button
        show_results = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show results')]"))
        )
        safe_click(driver, show_results)
        print("Applied Date Posted filter successfully")
        return True
        
    except Exception as e:
        print(f"Error applying date posted filter: {str(e)}")
        traceback.print_exc()
        return False

# Apply Easy Apply filter
def apply_easy_apply_filter(driver, resume_data):
    """Applies Easy Apply filter if preferred in resume."""
    if resume_data['job_preferences'].get('easy_apply_preferred') == 'Yes':
        try:
            print("Applying Easy Apply filter...")
            
            # Find and click the Easy Apply button directly
            easy_apply_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-pill') and contains(., 'Easy Apply')]"))
            )
            safe_click(driver, easy_apply_button)
            print("Applied Easy Apply filter successfully")
            return True
            
        except Exception as e:
            print(f"Error applying Easy Apply filter: {str(e)}")
            return False
    return False

# Apply all LinkedIn filters
def apply_linkedin_filters(driver, resume_data):
    """Applies all filters to LinkedIn job search based on resume preferences."""
    try:
        print("\nStarting to apply filters based on resume data...")
        
        # Wait for page to load fully
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'artdeco-pill')]"))
        )
        time.sleep(2)  # Additional wait to ensure page is fully loaded
        
        # Apply filters in sequence with waits between each
        apply_easy_apply_filter(driver, resume_data)
        time.sleep(2)
        
        apply_date_posted_filter(driver)
        time.sleep(2)
        
        apply_experience_level_filter(driver, resume_data)
        time.sleep(2)
        
        apply_workplace_filter(driver, resume_data)
        time.sleep(2)
        
        print("All filters applied successfully!")
        
    except Exception as e:
        print(f"Error during filter application: {str(e)}")
        traceback.print_exc()

# Function to search for a specific job title
def search_job_title(driver, job_title):
    """Searches for a specific job title on LinkedIn."""
    try:
        print(f"\nSearching for job title: {job_title}")
        
        # Clear any existing search - look for the clear button first
        try:
            clear_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Clear search query']"))
            )
            safe_click(driver, clear_button)
        except:
            pass  # No clear button, proceed to fill the search box
        
        # Find the search box - try multiple possible selectors
        search_box = None
        selectors = [
            "//input[@aria-label='Search by title, skill, or company']",
            "//input[contains(@placeholder, 'Search by title')]",
            "//input[contains(@id, 'jobs-search-box-keyword')]",
            "//form[contains(@class, 'jobs-search-box')]//input"
        ]
        
        for selector in selectors:
            try:
                search_box = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                break
            except:
                continue
        
        if search_box:
            search_box.clear()
            search_box.send_keys(job_title)
            
            # Try to find the search button
            try:
                search_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Search' or contains(@class, 'jobs-search-box__submit')]"))
                )
                safe_click(driver, search_button)
            except:
                # If button not found, try pressing Enter on the search box
                from selenium.webdriver.common.keys import Keys
                search_box.send_keys(Keys.RETURN)
            
            time.sleep(3)  # Wait for results to load
            
            # Save the current URL
            job_search_url = driver.current_url
            print(f"Search URL for '{job_title}': {job_search_url}")
            return job_search_url
        else:
            print("Could not find search box")
            return None
    except Exception as e:
        print(f"Error searching for job title: {str(e)}")
        return None

def main():
    # Load resume data
    resume_file = "final_resume.yaml"
    resume_data = load_resume(resume_file)
    
    # Get AI job suggestions (10 suggestions)
    job_suggestions = suggest_jobs(resume_data)
    print("\nAI Suggested Job Titles:")
    for i, job in enumerate(job_suggestions, 1):
        print(f"{i}. {job}")
    
    # Generate basic LinkedIn search URL
    linkedin_url = generate_linkedin_search_url(resume_data)
    print(f"\nBase LinkedIn Search URL:")
    print(linkedin_url)
    
    # Ask user if they want to perform browser automation to apply filters
    proceed = input("\nDo you want to open LinkedIn and apply filters automatically? (y/n): ")
    if proceed.lower() == 'y':
        try:
            # Initialize browser with options for better stability
            print("Initializing browser...")
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            driver = webdriver.Chrome(options=options)
            
            # Open LinkedIn search page
            driver.get(linkedin_url)
            time.sleep(5)  # Wait for page to fully load
            
            # Apply filters based on resume data
            print("Applying filters based on your resume preferences...")
            apply_linkedin_filters(driver, resume_data)
            
            # Search for each suggested job
            print("\nSearching for each suggested job title...")
            job_urls = {}
            for job_title in job_suggestions:
                job_url = search_job_title(driver, job_title)
                if job_url:
                    job_urls[job_title] = job_url
                    print(f"- Added search for: {job_title}")
                time.sleep(2)  # Avoid rate limiting
                
                # Re-apply filters after each search to ensure they stay applied
                apply_linkedin_filters(driver, resume_data)
            
            # Keep browser open for user to interact
            print("\nBrowser will remain open for you to interact with the results.")
            print("Close the browser window when you're done.")
            
            # Wait for user to manually close the browser
            input("Press Enter to close the browser and exit the program...")
            driver.quit()
            
        except Exception as e:
            print(f"Error during browser automation: {e}")
            traceback.print_exc()
    else:
        print("\nSkipping browser automation. Here are your job suggestions:")
        for i, job in enumerate(job_suggestions, 1):
            # Create manual search URLs
            job_search = urllib.parse.quote(job)
            search_url = f"{linkedin_url}&keywords={job_search}"
            print(f"{i}. {job}")
            print(f"   Search URL: {search_url}")

if __name__ == "__main__":
    main()