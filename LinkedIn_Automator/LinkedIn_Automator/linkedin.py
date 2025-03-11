import urllib.parse

def generate_linkedin_url(job_title, location="India"):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": job_title.strip(),
        "location": location.strip(),
        "f_AL": "true",  # ✅ Ensures only Easy Apply jobs appear
    }
    return base_url + urllib.parse.urlencode(params)

# Example usage:
job_url = generate_linkedin_url("Software Engineer", "India")
print("Generated LinkedIn URL:", job_url)
