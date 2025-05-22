import fitz  # PyMuPDF for PDF reading
import google.generativeai as genai
import yaml
import re
import streamlit as st

# Configure Gemini API key
GENAI_API_KEY = "AIzaSyAfAZy6iQYSoTnUNegAfIGY2ZekI5K3x20"
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

def analyze_resume(text, links):
    """
    Analyze the resume text and extract relevant information with improved structure
    """
    data = {
        'personal_information': {
            'name': '',
            'surname': '',
            'email': ''
        },
        'skills': [],
        'experience': [],
        'education': [],
        'projects': []
    }
    
    try:
        lines = text.split('\n')
        current_section = ''
        current_project = None
        current_experience = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            lower_line = line.lower()
            if 'projects' in lower_line:
                current_section = 'projects'
                continue
            elif 'experience' in lower_line:
                current_section = 'experience'
                continue
            elif 'education' in lower_line:
                current_section = 'education'
                continue
            elif 'skills' in lower_line:
                current_section = 'skills'
                continue
            
            # Process projects
            if current_section == 'projects':
                if '|' in line:  # Project title line
                    if current_project:
                        data['projects'].append(current_project)
                    
                    parts = line.split('|')
                    current_project = {
                        'title': parts[0].strip(),
                        'technologies': parts[1].strip() if len(parts) > 1 else '',
                        'duration': '',
                        'description': []
                    }
                elif current_project:
                    if line.startswith('•'):
                        current_project['description'].append(line.strip('• '))
                    elif any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                        current_project['duration'] = line
            
            # Process experience
            elif current_section == 'experience':
                if not line.startswith('•'):
                    if current_experience:
                        data['experience'].append(current_experience)
                    current_experience = {
                        'title': line,
                        'company': '',
                        'duration': '',
                        'description': []
                    }
                elif current_experience:
                    current_experience['description'].append(line.strip('• '))
            
            # Process skills
            elif current_section == 'skills' and ',' in line:
                skills = [skill.strip() for skill in line.split(',')]
                data['skills'].extend(skills)
        
        # Add last project/experience if exists
        if current_project:
            data['projects'].append(current_project)
        if current_experience:
            data['experience'].append(current_experience)
        
    except Exception as e:
        print(f"Error in analyze_resume: {str(e)}")
    
    return data
    
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

            "job_preferences:\n"
            "  date_availability: \"[Date Available to Start]\"\n"
            "  experience_level: []\n"
            "  company_preferences: []\n"
            "  workplace_type: []\n"
            "  easy_apply_preferred: \"\"\n\n"

            "skills: [\"Skill 1\", \"Skill 2\", \"Skill 3\"]\n\n"
            
            "certifications: []\n"
            "languages: []\n"
            "interests: []\n"
            "availability: {}\n"
            
            "salary_expectations:\n"
            "  salary_range_usd: \"[Expected Salary Range]\"\n\n"
            
            "self_identification:\n"
            "  gender: \"[Gender]\"\n"
            "  pronouns: \"[Pronouns]\"\n"
            "  veteran: \"[Veteran Status]\"\n"
            "  disability: \"[Disability Status]\"\n"
            "  ethnicity: \"[Ethnicity]\"\n\n"
            
            "legal_authorization:\n"
            "  work_authorization: \"[Work Authorization Status]\"\n"
            "  requires_visa: \"[Requires Visa Sponsorship]\"\n"
            "  legally_allowed_to_work_in_india: \"[Legally Allowed to Work in India]\"\n"
            "  requires_sponsorship: \"[Requires Sponsorship]\"\n\n"
            
            "work_preferences:\n"
            "  remote_work: \"[Preference for Remote Work]\"\n"
            "  in_person_work: \"[Preference for In-Person Work]\"\n"
            "  open_to_relocation: \"[Open to Relocation]\"\n"
            "  willing_to_complete_assessments: \"[Willing to Complete Assessments]\"\n"
            "  willing_to_undergo_drug_tests: \"[Willing to Undergo Drug Tests]\"\n"
            "  willing_to_undergo_background_checks: \"[Willing to Undergo Background Checks]\"\n\n"

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