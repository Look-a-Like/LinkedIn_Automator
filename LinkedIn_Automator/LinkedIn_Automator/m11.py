import streamlit as st
import pandas as pd
import urllib
from resume_processing import extract_text_from_pdf, analyze_resume
from job_suggestion import suggest_jobs
from linkedin import generate_linkedin_url
from linkedin_auth import setup_and_login
from job_navigation import navigate_to_job
from form_filling import fill_linkedin_form
import yaml
import time
import os
from data_access_layer import RepositoryFactory

def main():
    st.title("Automated Resume Analyzer & LinkedIn Job Application")

    # Initialize DAL repository
    resume_repo = RepositoryFactory.create_resume_repository()
    
    driver = None  # Initialize driver to avoid UnboundLocalError
    suggested_jobs = []
    apply_directly = st.radio("Do you want to apply directly with your resume?", ("Yes", "No"))

    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to:", ["Upload Resume", "Job Search", "LinkedIn Login", "Auto Apply", "Application History"])

    # Initialize session state for user data
    if "user_data" not in st.session_state:
        st.session_state.user_data = {
            "user_id": None,
            "resume_id": None
        }
    
    extracted_data = {}  # Initialize extracted_data to avoid UnboundLocalError

    if page == "Upload Resume":
        st.subheader("📄 Upload Your Resume")
        
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
                
                # Save the uploaded file
                if "file_saved" not in st.session_state:
                    file_bytes = uploaded_file.getvalue()
                    file_name = uploaded_file.name
                    save_path = os.path.join("uploads", file_name)
                    
                    # Create directory if it doesn't exist
                    os.makedirs("uploads", exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(file_bytes)
                    
                    st.session_state.resume_path = save_path
                    st.session_state.file_saved = True

    # Ensure extracted_data is always defined
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
        "job_preferences": {
            "date_availability": "",
            "experience_level": [],
            "company_preferences": [],
            "workplace_type": [],
            "easy_apply_preferred": ""
        },
        "salary_expectations": {"salary_range_usd": ""},
        "self_identification": {
            "gender": "", "pronouns": "", "veteran": "", "disability": "", "ethnicity": ""
        },
        "legal_authorization": {
            "work_authorization": "", "requires_visa": "",
            "legally_allowed_to_work_in_india": "", "requires_sponsorship": ""
        },
        "work_preferences": {
            "remote_work": "", "in_person_work": "", "open_to_relocation": "",
            "willing_to_complete_assessments": "", "willing_to_undergo_drug_tests": "",
            "willing_to_undergo_background_checks": ""
        },
        "skills": []
    }

    # Merge extracted data into default structure
    def deep_merge(default, extracted):
        """Recursively merge extracted data into default structure."""
        for key, value in extracted.items():
            if isinstance(value, dict) and key in default:
                deep_merge(default[key], value)
            else:
                default[key] = value
        return default

    merged_data = deep_merge(default_data, extracted_data)

    # Pre-fill form fields with extracted values
    with st.expander("📋 Personal Information"):
        st.subheader("Personal Information")
        for key, value in merged_data["personal_information"].items():
            merged_data["personal_information"][key] = st.text_input(key.replace("_", " ").title(), value)

    with st.expander("Education Details"):
        st.subheader("Education Details")
        education_entries = []
        for index, edu in enumerate(merged_data["education_details"]):
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

    # Other form sections continue as in the original code...
    # [Code omitted for brevity but would include all the other form sections]

    # Custom CSS for styling the button
    custom_css = """
        <style>
        div.stButton > button {
            background-color: #4CAF50;  /* Green */
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 24px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;  /* Full-width */
            transition: background-color 0.3s;
        }

        div.stButton > button:hover {
            background-color: #45a049;  /* Darker green on hover */
        }
        </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    # Save data to database when generating YAML file
    if st.button("🚀 Save Resume Data"):
        with st.spinner("⏳ Saving data to database and generating YAML file..."):
            # Save user data
            user_data = {
                "email": merged_data["personal_information"]["email"],
                "name": merged_data["personal_information"]["name"],
                "surname": merged_data["personal_information"]["surname"],
                "phone": merged_data["personal_information"]["phone"]
            }
            
            user_id = resume_repo.save_user(user_data)
            st.session_state.user_data["user_id"] = user_id
            
            # Save resume data if we have a file path
            if "resume_path" in st.session_state:
                resume_id = resume_repo.save_resume(
                    user_id, 
                    st.session_state.resume_path, 
                    merged_data
                )
                st.session_state.user_data["resume_id"] = resume_id
                
                # Also save to YAML
                resume_repo.save_resume_as_yaml(merged_data, "final_resume.yaml")
                
                st.success("✅ Data saved to database and YAML file generated: **'final_resume.yaml'**")
            else:
                st.warning("No resume file uploaded. Please upload a resume first.")

    # Extract location (set default if not found)
    location = extracted_data.get("location", "United States")  # Ensure location is defined

    if page == "Job Search":
        st.subheader("🔎 Find Relevant Jobs")
        
        if st.button("Find Relevant Jobs"):
            if not extracted_data:
                st.error("No resume data found. Please upload and analyze your resume first.")
            else:
                location = "India"
                suggested_jobs = suggest_jobs(extracted_data)
                job_links = [{"Job Title": job, "Apply Link": generate_linkedin_url(job, location)} for job in suggested_jobs]

                # Store in session state
                st.session_state["job_links"] = job_links
                st.session_state["jobs_fetched"] = True  # Track job listing state

        # Persist job listings across reruns
        if st.session_state.get("jobs_fetched"):
            st.subheader("Recommended Jobs")
            df = pd.DataFrame(st.session_state["job_links"])
            table_md = "| Job Title | Apply Link |\n|-----------|------------|\n"
            for _, row in df.iterrows():
                corrected_url = row["Apply Link"].replace(" ", "+")
                table_md += f"| {row['Job Title']} | [🔗 Apply Here]({corrected_url}) |\n"
            st.markdown(table_md, unsafe_allow_html=True)

    # Ensure "Login to LinkedIn" button always appears
    if st.session_state.get("jobs_fetched"):
        if not st.session_state.get("show_login_form"):
            if st.button("Login to LinkedIn"):
                st.session_state["show_login_form"] = True

        if st.session_state.get("show_login_form"):
            st.subheader("🔐 Login to LinkedIn")
            username = st.text_input("Enter LinkedIn Username (Email):")
            password = st.text_input("Enter LinkedIn Password:", type="password", key="password_input")

    if page == "LinkedIn Login":
        st.subheader("🔐 Login to LinkedIn")

        if st.session_state.get("show_login_form") or page == "LinkedIn Login":
            username = st.text_input("Enter LinkedIn Username (Email):")
            password = st.text_input("Enter LinkedIn Password:", type="password", key="password_input")
            
            if st.button("Submit and Login"):
                driver, wait = setup_and_login(username, password)  
                if driver:
                    st.session_state["driver"] = driver  
                    st.session_state["wait"] = wait  
                    st.success("Logged in successfully! You can now navigate to Auto Apply section.")
                else:
                    st.error("Login failed. Check your credentials and try again.")

    # Auto Apply page for automated job applications
    if page == "Auto Apply":
        st.subheader("🤖 Automated Job Applications")
        
        if "driver" not in st.session_state or st.session_state["driver"] is None:
            st.warning("Please login to LinkedIn first from the LinkedIn Login section.")
        elif "job_links" not in st.session_state or not st.session_state["job_links"]:
            st.warning("Please search for jobs first from the Job Search section.")
        else:
            resume_path = st.text_input("Enter the path to your resume PDF file:", 
                                        st.session_state.get("resume_path", ""))
            
            max_applications = st.slider("Maximum number of jobs to apply for:", 1, 10, 5)
            
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            application_results = []
            
            if st.button("Start Auto-Applying"):
                if "user_data" not in st.session_state or not st.session_state["user_data"]["resume_id"]:
                    st.error("Please save your resume data first.")
                    return
                    
                driver = st.session_state["driver"]
                wait = st.session_state["wait"]
                job_links = st.session_state["job_links"][:max_applications]  # Apply to first N jobs
                
                progress_bar = progress_placeholder.progress(0)
                status_placeholder.info("Starting automated job application process...")
                
                for i, job in enumerate(job_links):
                    job_title = job["Job Title"]
                    job_url = job["Apply Link"]
                    
                    # Update progress
                    progress_percent = int((i / len(job_links)) * 100)
                    progress_bar.progress(progress_percent)
                    status_placeholder.info(f"Applying to Job {i+1}/{len(job_links)}: {job_title}")
                    
                    try:
                        # Navigate to the job
                        success = navigate_to_job(driver, wait, job_url)
                        
                        if success:
                            # Fill and submit the application
                            try:
                                fill_linkedin_form(driver, merged_data["personal_information"], resume_path)
                                
                                # Save to database
                                job_data = {
                                    "job_title": job_title,
                                    "job_url": job_url,
                                    "status": "Successfully Applied"
                                }
                                resume_repo.save_job_application(
                                    st.session_state["user_data"]["resume_id"], 
                                    job_data
                                )
                                
                                application_results.append({
                                    "Job Title": job_title,
                                    "Status": "✅ Successfully Applied",
                                    "URL": job_url
                                })
                                status_placeholder.success(f"Successfully applied to: {job_title}")
                            except Exception as e:
                                # Save to database
                                job_data = {
                                    "job_title": job_title,
                                    "job_url": job_url,
                                    "status": f"Form Filling Error: {str(e)}"
                                }
                                resume_repo.save_job_application(
                                    st.session_state["user_data"]["resume_id"], 
                                    job_data
                                )
                                
                                application_results.append({
                                    "Job Title": job_title,
                                    "Status": f"❌ Form Filling Error: {str(e)}",
                                    "URL": job_url
                                })
                                status_placeholder.error(f"Error filling form for {job_title}: {str(e)}")
                        else:
                            # Save to database
                            job_data = {
                                "job_title": job_title,
                                "job_url": job_url,
                                "status": "Easy Apply not available"
                            }
                            resume_repo.save_job_application(
                                st.session_state["user_data"]["resume_id"], 
                                job_data
                            )
                            
                            application_results.append({
                                "Job Title": job_title,
                                "Status": "❌ Easy Apply not available",
                                "URL": job_url
                            })
                            status_placeholder.warning(f"Easy Apply not available for: {job_title}")
                        
                        # Wait between applications to avoid rate limiting
                        time.sleep(3)
                        
                    except Exception as e:
                        # Save to database
                        job_data = {
                            "job_title": job_title,
                            "job_url": job_url,
                            "status": f"Error: {str(e)}"
                        }
                        resume_repo.save_job_application(
                            st.session_state["user_data"]["resume_id"], 
                            job_data
                        )
                        
                        application_results.append({
                            "Job Title": job_title,
                            "Status": f"❌ Error: {str(e)}",
                            "URL": job_url
                        })
                        status_placeholder.error(f"Error applying to {job_title}: {str(e)}")
                
                # Completed all applications
                progress_bar.progress(100)
                status_placeholder.success("Completed auto-application process!")
                
                # Display results table
                st.subheader("Application Results")
                results_df = pd.DataFrame(application_results)
                st.table(results_df)
                
                # Store results in session state for future reference
                st.session_state["application_results"] = application_results
    
    # New Application History page
    if page == "Application History":
        st.subheader("📊 Application History")
        
        # Get application history from database
        if "user_data" in st.session_state and st.session_state["user_data"]["resume_id"]:
            applications = resume_repo.get_job_applications(st.session_state["user_data"]["resume_id"])
            
            if applications:
                # Display application history
                st.write(f"Found {len(applications)} job applications.")
                
                # Format for display
                display_data = []
                for app in applications:
                    display_data.append({
                        "Job Title": app["job_title"],
                        "Status": app["status"],
                        "Date Applied": app["applied_at"],
                        "View Job": f"[Link]({app['job_url']})"
                    })
                
                df = pd.DataFrame(display_data)
                st.table(df)
            else:
                st.info("No application history found. Apply to jobs to start tracking your applications.")
        else:
            st.warning("Please save your resume data first.")

if __name__ == "__main__":
    main()