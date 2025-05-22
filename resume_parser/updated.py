import fitz  # PyMuPDF for PDF reading
import google.generativeai as genai
import streamlit as st
import yaml
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import urllib.parse

# Configure Gemini API key (hardcoded)
GENAI_API_KEY = "AIzaSyDbYMP5crT9_QrEsETyCdjgeUN1FLuohS8"
genai.configure(api_key=GENAI_API_KEY)

def extract_text_from_pdf(uploaded_file):
    """Extract text and hyperlinks from an uploaded PDF file."""
    text = ""
    links = []

    try:
        # Open the PDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for page in doc:
            text += page.get_text("text") + "\n"  # Extract text
            for link in page.get_links():
                if "uri" in link:
                    links.append(link["uri"])  # Store extracted URLs
        
    except Exception as e:
        st.error(f"Error extracting text or links: {e}")

    return text, links

def analyze_resume(resume_text, links):
    """Analyze resume and extract key details using Gemini AI in YAML format."""
    
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Include extracted links in the prompt
        link_text = "\nExtracted Links from PDF:\n" + "\n".join(links) if links else ""

        prompt = (
            "Analyze the following resume and extract key details in the exact YAML format below. "
            "Ensure that URLs for LinkedIn, GitHub, and project links are extracted if available in the resume.\n\n"
            + link_text +
            "\n\npersonal_information:\n"
            "  name: \"[Your Name]\"\n"
            "  surname: \"[Your Surname]\"\n"
            "  date_of_birth: \"[Your Date of Birth]\"\n"
            "  country: \"[Your Country]\"\n"
            "  city: \"[Your City]\"\n"
            "  address: \"[Your Address]\"\n"
            "  zip_code: \"[Your zip code]\"\n"
            "  phone_prefix: \"[Your Phone Prefix]\"\n"
            "  phone: \"[Your Phone Number]\"\n"
            "  email: \"[Your Email Address]\"\n"
            "  github: \"[Your GitHub Profile URL]\"\n"
            "  linkedin: \"[Your LinkedIn Profile URL]\"\n\n"
            
            "education_details:\n"
            "  - education_level: \"[Your Education Level]\"\n"
            "    institution: \"[Your Institution]\"\n"
            "    field_of_study: \"[Your Field of Study]\"\n"
            "    final_evaluation_grade: \"[Your Final Evaluation Grade]\"\n"
            "    start_date: \"[Start Date]\"\n"
            "    year_of_completion: \"[Year of Completion]\"\n"
            "    exam: {}\n\n"

            "experience_details:\n"
            "  - position: \"[Your Position]\"\n"
            "    company: \"[Company Name]\"\n"
            "    employment_period: \"[Employment Period]\"\n"
            "    location: \"[Location]\"\n"
            "    industry: \"[Industry]\"\n"
            "    key_responsibilities:\n"
            "      - \"[Responsibility Description]\"\n"
            "    skills_acquired:\n"
            "      - \"[Skill]\"\n\n"

            "projects:\n"
            "  - name: \"[Project Name]\"\n"
            "    description: \"[Project Description]\"\n"
            "    link: \"[Project Link]\"\n\n"

            "achievements:\n"
            "  - name: \"[Achievement Name]\"\n"
            "    description: \"[Achievement Description]\"\n\n"

            "certifications: []\n"
            "languages: []\n"
            "interests: []\n"
            "availability: {}\n"
            "salary_expectations: {}\n"
            "self_identification: {}\n"
            "legal_authorization: {}\n"
            "work_preferences: {}\n\n"

            "Analyze the given resume text and return structured details in this YAML format:\n\n"
            "Resume:\n" + resume_text
        )

        response = model.generate_content(prompt)
        analysis = response.text.strip() if response else "No response received"

        # ✅ Remove triple backticks (` ```yaml `) from the response
        cleaned_analysis = re.sub(r"```[a-zA-Z]*", "", analysis).strip()

        return yaml.safe_load(cleaned_analysis)  # Convert YAML string to dictionary

    except Exception as e:
        st.error(f"Error analyzing resume: {e}")
        return {}



# Load resume data from YAML file
def load_resume(yaml_file):
    """Loads and parses the resume YAML file."""
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)

# Generate LinkedIn job search URL
def generate_linkedin_url(job_title, location="India"):
    """Creates a LinkedIn job search URL based on job title and location."""
    base_url = "https://www.linkedin.com/jobs/search?"
    params = {
        "keywords": job_title,
        "location": location
    }
    search_url = base_url + urllib.parse.urlencode(params)
    return search_url

# AI-Powered Job Suggestions
def suggest_jobs(yaml_data):
    """Uses Gemini AI to suggest relevant jobs based on resume data."""
    prompt = f"""
    Based on the following resume details, suggest 5 most relevant job roles:
    
    {yaml.dump(yaml_data)}

    Provide results in this format:
    1. Job Title
    2. Job Title

    No other details or description just job title with apply link
    """
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)

    # Extract job titles from AI response
    job_titles = [line.split(". ", 1)[-1] for line in response.text.split("\n") if line.strip()]
    return job_titles[:5]  # Return top 5 job suggestions


def main():
    st.title("Automated Resume Analyzer & LinkedIn Job Application")

    apply_directly = st.radio("Do you want to apply directly with your resume?", ("Yes", "No"))

    extracted_data = {}  # ✅ Initialize extracted_data to avoid UnboundLocalError

    if apply_directly == "Yes":
        uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

        if uploaded_file:
            if "resume_text" not in st.session_state:
                resume_text, links = extract_text_from_pdf(uploaded_file)
                st.session_state.resume_text = resume_text
                st.session_state.links = links
            else:
                resume_text, links = st.session_state.resume_text, st.session_state.links

            if not resume_text.strip():
                st.error("No text extracted from the PDF. Please try another file.")
                return

            # Analyze the resume once
            if "analysis" not in st.session_state:
                st.info("Analyzing resume...")
                extracted_data = analyze_resume(resume_text, links)
                st.session_state.analysis = extracted_data  # Store in session state
            else:
                extracted_data = st.session_state.analysis  # Use cached data

    # ✅ Ensure extracted_data is always defined
    extracted_data = extracted_data if extracted_data else {}

    # Default structure for form fields
    default_data = {
        "personal_information": {
            "name": "", "surname": "", "date_of_birth": "", "country": "",
            "city": "", "address": "", "zip_code": "", "phone_prefix": "",
            "phone": "", "email": "", "github": "", "linkedin": ""
        },
        "education_details": [{}],
        "experience_details": [{}],
        "projects": [{}],
        "achievements": [{}],
        "certifications": [],
        "languages": [],
        "interests": [],
        "availability": {},
        "salary_expectations": {"salary_range_usd": ""},
        "self_identification": {
            "gender": "", "pronouns": "", "disability": "", "ethnicity": ""
        },
        "legal_authorization": {
            "work_authorization": "", "requires_visa": "",
            "legally_allowed_to_work_in_india": "", "requires_sponsorship": ""
        },
        "work_preferences": {
            "remote_work": "", "in_person_work": "", "open_to_relocation": "",
        },
    }

    # ✅ Merge extracted data into default structure
    def deep_merge(default, extracted):
        """Recursively merge extracted data into default structure."""
        for key, value in extracted.items():
            if isinstance(value, dict) and key in default:
                deep_merge(default[key], value)
            else:
                default[key] = value
        return default

    merged_data = deep_merge(default_data, extracted_data)

    # 🎯 Pre-fill form fields with extracted values
    st.subheader("Personal Information")
    for key, value in merged_data["personal_information"].items():
        merged_data["personal_information"][key] = st.text_input(key.replace("_", " ").title(), value)

    st.subheader("Education Details")
    education_entries = []
    for index, edu in enumerate(merged_data["education_details"]):
        with st.expander(f"Education Entry {index + 1}"):
            edu_entry = {
                "education_level": st.text_input("Education Level", edu.get("education_level", ""), key=f"education_level_{index}"),
                "institution": st.text_input("Institution", edu.get("institution", ""), key=f"institution_{index}"),
                "field_of_study": st.text_input("Field of Study", edu.get("field_of_study", ""), key=f"field_of_study_{index}"),
                "final_evaluation_grade": st.text_input("Final Grade", edu.get("final_evaluation_grade", ""), key=f"final_evaluation_grade_{index}"),
                "start_date": st.text_input("Start Date", edu.get("start_date", ""), key=f"start_date_{index}"),
                "year_of_completion": st.text_input("Year of Completion", edu.get("year_of_completion", ""), key=f"year_of_completion_{index}")
            }
            education_entries.append(edu_entry)
    merged_data["education_details"] = education_entries

    st.subheader("Experience Details")
    experience_entries = []
    for index, exp in enumerate(merged_data["experience_details"]):
        with st.expander(f"Experience Entry {index + 1}"):
            exp_entry = {
                "position": st.text_input("Position", exp.get("position", ""), key=f"position_{index}"),
                "company": st.text_input("Company", exp.get("company", ""), key=f"company_{index}"),
                "employment_period": st.text_input("Employment Period", exp.get("employment_period", ""), key=f"employment_period_{index}"),
                "location": st.text_input("Location", exp.get("location", ""), key=f"location_{index}")
            }
            experience_entries.append(exp_entry)
    merged_data["experience_details"] = experience_entries

    st.subheader("Salary Expectations")
    merged_data["salary_expectations"]["salary_range_usd"] = st.text_input(
        "Expected Salary (USD)", merged_data["salary_expectations"].get("salary_range_usd", ""), key="salary_range"
    )

    st.subheader("Self Identification")
    for key, value in merged_data["self_identification"].items():
        merged_data["self_identification"][key] = st.text_input(key.replace("_", " ").title(), value)

    st.subheader("Legal Authorization")
    for key, value in merged_data["legal_authorization"].items():
        merged_data["legal_authorization"][key] = st.selectbox(key.replace("_", " ").title(), ["Yes", "No"], index=0 if value == "Yes" else 1)

    st.subheader("Work Preferences")
    for key, value in merged_data["work_preferences"].items():
        merged_data["work_preferences"][key] = st.selectbox(key.replace("_", " ").title(), ["Yes", "No"], index=0 if value == "Yes" else 1)

    if st.button("Generate YAML File"):
        with open("final_resume.yaml", "w", encoding="utf-8") as file:
            yaml.dump(merged_data, file, default_flow_style=False)
        st.success("YAML file generated: 'final_resume.yaml' ✅")

 # Extract location (set default if not found)
    location = extracted_data.get("location", "United States")  # Ensure location is defined

    if st.button("Find Relevant Jobs"):
        if not extracted_data:
            st.error("No resume data found. Please upload and analyze your resume first.")
        else:
            # Extract location (set default if not found)
            location = extracted_data.get("personal_information", {}).get("city", "United States")  # Ensure location is defined
            
            # AI-Generated Job Suggestions
            suggested_jobs = suggest_jobs(extracted_data)  # Use correct resume data

            # Generate LinkedIn Search Links
            job_links = [{"Job Title": job, "Apply Link": generate_linkedin_url(job, location)} for job in suggested_jobs]

            # Convert to DataFrame & Display
            df = pd.DataFrame(job_links)
            df["Apply Link"] = df["Apply Link"].apply(lambda x: f"[🔗 Apply Here]({x})")

            st.subheader("Recommended Jobs")
            st.table(df)

# Get LinkedIn credentials
username = st.text_input("Enter your LinkedIn Username (Email):")
password = st.text_input("Enter your LinkedIn Password:", type="password")

if st.button("Apply for Jobs on LinkedIn"):
    if "job_links" in st.session_state and st.session_state["job_links"]:
        st.info("Applying to jobs on LinkedIn...")
      #  apply_to_jobs_on_linkedin(st.session_state["job_links"], username, password)
    else:
        st.error("No job links available. Please fill the response form first and generate a yaml file and click on 'Find Relevant Jobs' first and than apply")

if __name__ == "__main__":
    main()
