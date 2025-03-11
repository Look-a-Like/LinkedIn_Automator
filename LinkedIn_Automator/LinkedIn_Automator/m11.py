import streamlit as st
import pandas as pd
import urllib
from resume_processing import extract_text_from_pdf, analyze_resume
from job_suggestion import suggest_jobs
from linkedin import generate_linkedin_url
from linkedin_auth import setup_and_login
from job_navigation import navigate_to_job
import yaml

def main():
    st.title("Automated Resume Analyzer & LinkedIn Job Application")

    driver = None  # ✅ Initialize driver to avoid UnboundLocalError


    suggested_jobs =[]
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
            location = "India"
            suggested_jobs = suggest_jobs(extracted_data)
            job_links = [{"Job Title": job, "Apply Link": generate_linkedin_url(job, location)} for job in suggested_jobs]

            # Store in session state
            st.session_state["job_links"] = job_links
            st.session_state["jobs_fetched"] = True  # ✅ Track job listing state

    # ✅ Persist job listings across reruns
    if st.session_state.get("jobs_fetched"):
        st.subheader("Recommended Jobs")
        df = pd.DataFrame(st.session_state["job_links"])
        table_md = "| Job Title | Apply Link |\n|-----------|------------|\n"
        for _, row in df.iterrows():
            corrected_url = row["Apply Link"].replace(" ", "+")
            table_md += f"| {row['Job Title']} | [🔗 Apply Here]({corrected_url}) |\n"
        st.markdown(table_md, unsafe_allow_html=True)

        # ✅ Ensure "Login to LinkedIn" button always appears
    if st.session_state.get("jobs_fetched"):
        if st.button("Login to LinkedIn"):
            st.session_state["show_login_form"] = True  # ✅ Preserve login form state

    if st.session_state.get("show_login_form"):
        username = st.text_input("Enter LinkedIn Username (Email):")
        password = st.text_input("Enter LinkedIn Password:", type="password", key="password_input")
        
    if st.button("Submit and Login"):
            driver, wait = setup_and_login(username, password)  
            if driver:
                st.session_state["driver"] = driver  
                st.session_state["wait"] = wait  
                st.success("Logged in successfully! Navigating to the first job...")

                # Auto-Navigate to First Job Posting After Login
                if "job_links" in st.session_state and st.session_state["job_links"]:
                    first_job_url = st.session_state["job_links"][0]["Apply Link"]
                    success = navigate_to_job(driver, wait, first_job_url)

                    if success:
                        st.success("Opened job posting & clicked 'Easy Apply' if available.")
                    else:
                        st.error("Could not find 'Easy Apply' button on the job page.")
            else:
                st.error("Login failed. Check your credentials and try again.")


if __name__ == "__main__":
    main()
