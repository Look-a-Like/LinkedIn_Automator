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
import requests
from data_access_layer import RepositoryFactory

API_BASE = "http://localhost:8000"

# Fetch resume data
def fetch_resume(user_id):
    try:
        response = requests.get(f"{API_BASE}/resumes/latest", headers={"X-User-ID": user_id})
        if response.status_code == 200:
            resume_data = response.json()["resume"]["data"]
            return resume_data
        else:
            st.warning("No resume found or error fetching resume.")
            return None
    except Exception as e:
        st.error(f"Error fetching resume: {e}")
        return None


if "user_data" not in st.session_state:
    st.session_state["user_data"] = {
        "user_id": None,
        "resume_id": None
    }

global extracted_data
extracted_data = {}

def main():
    global extracted_data
    st.title("Automated Resume Analyzer & LinkedIn Job Application")

    if "user_data" not in st.session_state:
        st.session_state.user_data = {
            "user_id": None,
            "resume_id": None
        }

    def deep_merge(default, extracted):
        """Recursively merge extracted data into default structure."""
        for key, value in extracted.items():
            if isinstance(value, dict) and key in default:
                deep_merge(default[key], value)
            else:
                default[key] = value
        return default

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
            "gender": "", "pronouns": "", "disability": "", "ethnicity": ""
        },
        "legal_authorization": {
            "work_authorization": "", "requires_visa": "",
            "legally_allowed_to_work_in_india": "", "requires_sponsorship": ""
        },
        "work_preferences": {
            "remote_work": "", "in_person_work": "", "open_to_relocation": "", "willing_to_undergo_drug_tests": "",
            "willing_to_undergo_background_checks": ""
        },
        "skills": []
    }

    query_params = st.query_params
    if "user_id" in query_params:
        user_id = query_params["user_id"][0]
        st.session_state.user_data["user_id"] = user_id
        st.success(f"User ID detected from login: {user_id}")

        if "fetched_resume" not in st.session_state:
            resume_data = fetch_resume(user_id)
            if resume_data:
                st.session_state.analysis = resume_data
                st.session_state.fetched_resume = True
                merged_data = deep_merge(extracted_data, resume_data)
                st.session_state["merged_data"] = merged_data

    # Initialize DAL repository
    resume_repo = RepositoryFactory.create_resume_repository()

    # Initialize session states if they don't exist
    if "page" not in st.session_state:
        st.session_state["page"] = "Upload Resume"

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "jobs_fetched" not in st.session_state:
        st.session_state["jobs_fetched"] = False

    driver = None  # Initialize driver to avoid UnboundLocalError
    suggested_jobs = []

    # Radio button for direct application
    apply_directly = st.radio("Do you want to apply directly with your resume?", ("Yes", "No"))

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        # Save current page before changing it
        current_page = st.session_state["page"]

        # Navigation radio buttons
        selected_page = st.radio(
            "Go to:",
            ["Upload Resume", "Job Search", "LinkedIn Login", "Auto Apply", "Application History"]
        )

        # Only update the page if the user has selected a different one
        if selected_page != current_page:
            st.session_state["page"] = selected_page
            # Force rerun to apply the page change immediately
            st.rerun()

    # Merge extracted data into default structure


    # Page content
    if st.session_state["page"] == "Upload Resume":
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

        # Merge the data
        merged_data = st.session_state.get("merged_data", deep_merge(default_data.copy(), extracted_data))

        # Display form fields
        with st.expander("📋 Personal Information"):
            st.subheader("Personal Information")
            for key, value in merged_data["personal_information"].items():
                merged_data["personal_information"][key] = st.text_input(key.replace("_", " ").title(), value)

        with st.expander("Education Details"):
            st.subheader("Education Details")
            education_entries = []
            for index, edu in enumerate(merged_data["education_details"]):
                edu_entry = {
                    "education_level": st.text_input("Education Level", edu.get("education_level", ""),
                                                     key=f"education_level_{index}"),
                    "institution": st.text_input("Institution", edu.get("institution", ""), key=f"institution_{index}"),
                    "field_of_study": st.text_input("Field of Study", edu.get("field_of_study", ""),
                                                    key=f"field_of_study_{index}"),
                    "final_evaluation_grade": st.text_input("Final Grade", edu.get("final_evaluation_grade", ""),
                                                            key=f"final_evaluation_grade_{index}"),
                    "start_date": st.text_input("Start Date", edu.get("start_date", ""), key=f"start_date_{index}"),
                    "year_of_completion": st.text_input("Year of Completion", edu.get("year_of_completion", ""),
                                                        key=f"year_of_completion_{index}")
                }
                education_entries.append(edu_entry)
            merged_data["education_details"] = education_entries

        with st.expander("Experience Details"):
            st.subheader("Experience Details")
            experience_entries = []
            for index, exp in enumerate(merged_data["experience_details"]):
                exp_entry = {
                    "position": st.text_input("Position", exp.get("position", ""), key=f"position_{index}"),
                    "company": st.text_input("Company", exp.get("company", ""), key=f"company_{index}"),
                    "employment_period": st.text_input("Employment Period", exp.get("employment_period", ""),
                                                       key=f"employment_period_{index}"),
                    "location": st.text_input("Location", exp.get("location", ""), key=f"location_{index}")
                }
                experience_entries.append(exp_entry)
            merged_data["experience_details"] = experience_entries

        with st.expander("Show Projects"):
            st.subheader("Projects")
            project_entries = []
            for index, proj in enumerate(merged_data["projects"]):
                proj_entry = {
                    "name": st.text_input("Project Name", proj.get("name", ""), key=f"proj_name_{index}"),
                    "description": st.text_area("Project Description", proj.get("description", ""),
                                                key=f"proj_desc_{index}"),
                    "link": st.text_input("Project Link", proj.get("link", ""), key=f"proj_link_{index}")
                }
                project_entries.append(proj_entry)
            merged_data["projects"] = project_entries

        with st.expander("Show Achievements"):
            st.subheader("Achievements")
            achievement_entries = []
            for index, ach in enumerate(merged_data["achievements"]):
                ach_entry = {
                    "name": st.text_input("Achievement Name", ach.get("name", ""), key=f"ach_name_{index}"),
                    "description": st.text_area("Achievement Description", ach.get("description", ""),
                                                key=f"ach_desc_{index}")
                }
                achievement_entries.append(ach_entry)
            merged_data["achievements"] = achievement_entries

        with st.expander("Skills"):
            st.subheader("Skills")
            skills_text = st.text_area("Skills (comma-separated)",
                                       ", ".join(merged_data["skills"]) if merged_data["skills"] else "")
            merged_data["skills"] = [skill.strip() for skill in skills_text.split(",") if skill.strip()]

        # For the "Job Preferences" section
        with st.expander("Job Preferences", expanded=True):  # Set to expanded by default
            st.subheader("Job Preferences (Required)")

            # Add required indicators to field labels
            date_availability = st.text_input("Date Available to Start *",
                                              merged_data["job_preferences"].get("date_availability", ""))

            experience_levels = ["Entry Level", "Associate", "Mid-Senior Level", "Director", "Executive"]
            selected_exp_levels = st.multiselect("Experience Level *",
                                                 experience_levels,
                                                 default=merged_data["job_preferences"].get("experience_level", []))

            company_preferences = ["Startup", "Small Business", "Mid-size", "Large Enterprise", "Non-profit"]
            selected_companies = st.multiselect("Company Preferences *",
                                                company_preferences,
                                                default=merged_data["job_preferences"].get("company_preferences", []))

            workplace_types = ["On-site", "Hybrid", "Remote"]
            selected_workplace = st.multiselect("Workplace Type *",
                                                workplace_types,
                                                default=merged_data["job_preferences"].get("workplace_type", []))

            easy_apply_preferred = st.selectbox("Easy Apply Preferred *",
                                                ["Yes", "No"],
                                                index=0 if merged_data["job_preferences"].get(
                                                    "easy_apply_preferred") == "Yes" else 1)

            # Update the merged data
            merged_data["job_preferences"]["date_availability"] = date_availability
            merged_data["job_preferences"]["experience_level"] = selected_exp_levels
            merged_data["job_preferences"]["company_preferences"] = selected_companies
            merged_data["job_preferences"]["workplace_type"] = selected_workplace
            merged_data["job_preferences"]["easy_apply_preferred"] = easy_apply_preferred

        with st.expander("Salary Details  "):
            st.subheader("Salary Expectations")
            merged_data["salary_expectations"]["salary_range_usd"] = st.text_input(
                "Expected Salary (USD)", merged_data["salary_expectations"].get("salary_range_usd", ""),
                key="salary_range"
            )

        # For the "Self Identification" section
        with st.expander("Self Identification", expanded=True):
            st.subheader("Self Identification (Required)")

            self_id_fields = {}

            # Handle gender as dropdown
            gender_options = ["", "Male(he/him)", "Female(she/her)", "Non-binary(they/them)", "Prefer not to say"]
            current_gender = merged_data["self_identification"].get("gender", "")

            # Find index of current gender in options, default to last option if not found
            gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0

            self_id_fields["gender"] = st.selectbox(
                "Gender *(selection required)",
                gender_options,
                index=gender_index,
                key="self_id_gender"
            )

            # Automatically set pronouns based on gender selection
            if self_id_fields["gender"] == "Male":
                self_id_fields["pronouns"] = "He/Him"
            elif self_id_fields["gender"] == "Female":
                self_id_fields["pronouns"] = "She/Her"
            elif self_id_fields["gender"] == "Non-binary":
                self_id_fields["pronouns"] = "They/Them"
            elif self_id_fields["gender"] == "Prefer not to say":
                self_id_fields["pronouns"] = "Prefer not to say"
            else:
                self_id_fields["pronouns"] = ""

            # Handle disability as dropdown with conditional text area
            disability_options = ["", "Yes", "No"]
            current_disability = "Yes" if merged_data["self_identification"].get("disability", "") else "No"
            current_disability_index = disability_options.index(
                current_disability) if current_disability in disability_options else 0

            has_disability = st.selectbox(
                "Disability *(selection required)",
                disability_options,
                index=current_disability_index,
                key="self_id_disability_selection"
            )

            # Store basic Yes/No response
            self_id_fields["has_disability"] = has_disability

            # If user selects "Yes", show text area for disability description
            if has_disability == "Yes":
                disability_description = st.text_area(
                    "Describe your disability *",
                    value=merged_data["self_identification"].get("disability_description", ""),
                    key="self_id_disability_description"
                )
                self_id_fields["disability_description"] = disability_description
            else:
                # Set empty description if "No" is selected
                self_id_fields["disability_description"] = ""

            # Handle ethnicity as dropdown with expanded options
            ethnicity_options = [
                "",
                "Asian - East Asian (Chinese, Japanese, Korean, etc.)",
                "Asian - South Asian (Indian, Pakistani, Bangladeshi, etc.)",
                "Asian - Southeast Asian (Vietnamese, Filipino, Thai, etc.)",
                "Asian - Indian - North Indian",
                "Asian - Indian - South Indian",
                "Asian - Indian - East Indian",
                "Asian - Indian - West Indian",
                "Asian - Indian - Northeast Indian",
                "Asian - Indian - Central Indian",
                "Black or African American",
                "Hispanic or Latino",
                "Middle Eastern or North African",
                "Native American or Alaska Native",
                "Native Hawaiian or Pacific Islander",
                "White - European",
                "White - North American",
                "White - Other",
                "Two or More Races",
                "Other",
                "Prefer not to say"
            ]

            current_ethnicity = merged_data["self_identification"].get("ethnicity", "")

            # Find index of current ethnicity in options, default to first (blank) option if not found
            ethnicity_index = 0
            if current_ethnicity in ethnicity_options:
                ethnicity_index = ethnicity_options.index(current_ethnicity)

            self_id_fields["ethnicity"] = st.selectbox(
                "Ethnicity *(selection required)",
                ethnicity_options,
                index=ethnicity_index,
                key="self_id_ethnicity"
            )

            # If user selects "Other", show text input for specifying ethnicity
            if self_id_fields["ethnicity"] == "Other":
                other_ethnicity = st.text_input(
                    "Please specify your ethnicity *",
                    value=merged_data["self_identification"].get("other_ethnicity", ""),
                    key="self_id_other_ethnicity"
                )
                self_id_fields["other_ethnicity"] = other_ethnicity

            # Handle other fields as text inputs (except those we've already handled)
            for key, value in merged_data["self_identification"].items():
                if key not in ["gender", "pronouns", "veteran", "disability", "disability_description",
                               "has_disability", "ethnicity", "other_ethnicity"]:
                    field_value = st.text_input(f"{key.replace('_', ' ').title()} *", value, key=f"self_id_{key}")
                    self_id_fields[key] = field_value

            # Update the merged data structure with all self identification fields
            merged_data["self_identification"] = self_id_fields

        # For the "Legal Authorization" section
        with st.expander("Legal Authorization", expanded=True):
            st.subheader("Legal Authorization (Required)")

            legal_auth_fields = {}
            for key, value in merged_data["legal_authorization"].items():
                field_value = st.selectbox(f"{key.replace('_', ' ').title()} *",
                                           ["Yes", "No", ""],
                                           index=0 if value == "Yes" else (1 if value == "No" else 2),
                                           key=f"legal_{key}")
                legal_auth_fields[key] = field_value

            merged_data["legal_authorization"] = legal_auth_fields

        with st.expander("Work Preferences", expanded=True):
            st.subheader("Work Preferences (Required)")

            work_pref_fields = {}
            for key, value in merged_data["work_preferences"].items():
                # Skip the willing_to_complete_assessments field
                if key != "willing_to_complete_assessments":
                    field_value = st.selectbox(f"{key.replace('_', ' ').title()} *",
                                               ["Yes", "No", ""],
                                               index=0 if value == "Yes" else (1 if value == "No" else 2),
                                               key=f"work_pref_{key}")
                    work_pref_fields[key] = field_value

            merged_data["work_preferences"] = work_pref_fields

        # Validation function
        def validate_required_sections():
            """Validate that all required fields are filled"""
            validation_errors = []

            # Check Job Preferences
            if not merged_data["job_preferences"]["date_availability"]:
                validation_errors.append("Date Available to Start is required")
            if not merged_data["job_preferences"]["experience_level"]:
                validation_errors.append("Experience Level selection is required")
            if not merged_data["job_preferences"]["company_preferences"]:
                validation_errors.append("Company Preferences selection is required")
            if not merged_data["job_preferences"]["workplace_type"]:
                validation_errors.append("Workplace Type selection is required")

            # Check Self Identification with special handling for conditionally required fields
            for key, value in merged_data["self_identification"].items():
                # Skip pronouns check as it's automatically set based on gender
                if key == "pronouns":
                    continue

                # Special handling for disability fields
                if key == "has_disability" and value == "Yes":
                    # Check if disability description is provided when disability is "Yes"
                    if not merged_data["self_identification"].get("disability_description"):
                        validation_errors.append("Disability Description in Self Identification is required")
                elif key == "disability_description" and merged_data["self_identification"].get(
                        "has_disability") != "Yes":
                    # Skip disability description check if disability is not "Yes"
                    continue
                elif key not in ["disability_description"]:
                    # Check all other non-special fields normally
                    if not value:
                        validation_errors.append(f"{key.replace('_', ' ').title()} in Self Identification is required")

            # Check Legal Authorization
            for key, value in merged_data["legal_authorization"].items():
                if not value or value == "":
                    validation_errors.append(f"{key.replace('_', ' ').title()} in Legal Authorization is required")

            # Check Work Preferences
            for key, value in merged_data["work_preferences"].items():
                if not value or value == "":
                    validation_errors.append(f"{key.replace('_', ' ').title()} in Work Preferences is required")

            return validation_errors

        # Display notice about required fields
        st.markdown("""
        <div style="background-color: #fffae6; padding: 10px; border-radius: 5px; margin-bottom: 10px; color: #000000;">
        <strong>Note:</strong> Fields marked with * are required. All sections must be completed before saving.
        </div>
        """, unsafe_allow_html=True)

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

        if st.button("🚀 Save Resume Data"):
            validation_errors = validate_required_sections()

            if validation_errors:
                st.error("Please fix the following errors before saving:")
                for error in validation_errors:
                    st.warning(error)
            else:
                with st.spinner("⏳ Saving resume to backend..."):
                    try:
                        user_id = st.session_state.user_data["user_id"]
                        headers = {
                            "Content-Type": "application/json",
                            "X-User-ID": st.session_state.user_data["user_id"]  # ✅ Pass the user_id here
                        }

                        # Send to backend
                        response = requests.post(
                            f"http://localhost:8000/resumes/",
                            json=merged_data,
                            headers=headers
                        )

                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.user_data["resume_id"] = data["resume_id"]

                            st.success(f"✅ Resume saved with ID: {data['resume_id']}")

                            # Prompt to continue
                            if st.button("Continue to Job Search", key="continue_to_job_search"):
                                st.session_state["page"] = "Job Search"
                                st.rerun()
                        else:
                            st.error(f"❌ Failed to save resume: {response.text}")
                    except Exception as e:
                        st.error(f"Exception occurred while saving: {e}")


    # Store merged_data in session state for access by other pages
    if "merged_data" not in st.session_state and 'extracted_data' in locals():
        merged_data = deep_merge(default_data.copy(), extracted_data)
        st.session_state["merged_data"] = merged_data

    # Job Search page
    elif st.session_state["page"] == "Job Search":
        st.subheader("🔎 Find Relevant Jobs")

        # Extract location or use default
        location = st.session_state.get("analysis", {}).get("location", "United States")

        if st.button("Find Relevant Jobs"):
            if "analysis" not in st.session_state:
                st.error("No resume data found. Please upload and analyze your resume first.")
                if st.button("Go to Upload Resume"):
                    st.session_state["page"] = "Upload Resume"
                    st.rerun()
            else:
                location = "India"  # Hardcoded location as in original code
                with st.spinner("Finding relevant jobs..."):
                    suggested_jobs = suggest_jobs(st.session_state["analysis"])
                    job_links = [{"Job Title": job, "Apply Link": generate_linkedin_url(job, location)} for job in
                                 suggested_jobs]

                    time.sleep(2)
                    # Store in session state
                    st.session_state["job_links"] = [
                        {"Job Title": "Full Stack Developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4210857136"},

                        {"Job Title": "Java Full Stack Developer",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4209321490"},

                        {"Job Title": "Software engineer",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4211525738"},

                        {"Job Title": "Software engineer ",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4199382263&start=24"},

                        {"Job Title": "Android Engineer",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4206211199&start=24"},

                        {"Job Title": "Full Stack Developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4208061397&start=24"},

                        {"Job Title": "Software Developer",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4209959557&start=24"},

                        {"Job Title": "Software developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4207720563&start=48"},

                        {"Job Title": "Java developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/search/?currentJobId=4210547652&distance=25&geoId=102713980&keywords=rust&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"},

                        {"Job Title": "Python developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/search/?currentJobId=4213226622&distance=25&geoId=102713980&keywords=python&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"},

                        {"Job Title": "Software developer ",
                         "Apply Link": "https://www.linkedin.com/jobs/search/?currentJobId=4202520671&distance=25&geoId=102713980&keywords=python&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"},

                        {"Job Title": "Python backend developer 2",
                         "Apply Link": "https://www.linkedin.com/jobs/search/?currentJobId=4193206734&distance=25&geoId=102713980&keywords=python&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"},

                        {"Job Title": "AWS Engineer",
                         "Apply Link": "https://www.linkedin.com/jobs/search/?currentJobId=4205587140&distance=25&geoId=102713980&keywords=python&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"}

                    ]
                    st.session_state["jobs_fetched"] = True
                    st.success("Jobs found successfully!")
                    st.rerun()  # Refresh to show the results

        # Display job listings if they exist
        if st.session_state.get("jobs_fetched"):
            st.subheader("Recommended Jobs")
            df = pd.DataFrame(st.session_state["job_links"])
            table_md = "| Job Title | Apply Link |\n|-----------|------------|\n"
            for _, row in df.iterrows():
                corrected_url = row["Apply Link"].replace(" ", "+")
                table_md += f"| {row['Job Title']} | [🔗 Apply Here]({corrected_url}) |\n"
            st.markdown(table_md, unsafe_allow_html=True)

            # Add a button to login
            if st.button("Continue to LinkedIn Login"):
                st.session_state["page"] = "LinkedIn Login"
                st.rerun()

    # LinkedIn Login page
    elif st.session_state["page"] == "LinkedIn Login":
        st.subheader("🔐 Login to LinkedIn")

        if not st.session_state.get("logged_in"):  # Only show login form if not logged in
            username = st.text_input("Enter LinkedIn Username (Email):")
            password = st.text_input("Enter LinkedIn Password:", type="password", key="password_input")

            if st.button("Submit and Login"):
                with st.spinner("Logging in to LinkedIn..."):
                    driver, wait = setup_and_login(username, password)
                    if driver:
                        st.session_state["driver"] = driver
                        st.session_state["wait"] = wait
                        st.session_state["logged_in"] = True
                        st.success("Logged in successfully!")
                        # Add auto-redirect button
                        if st.button("Continue to Auto Apply"):
                            st.session_state["page"] = "Auto Apply"
                            st.rerun()
                    else:
                        st.error("Login failed. Check your credentials and try again.")
        else:
            st.success("You are already logged in to LinkedIn.")
            if st.button("Continue to Auto Apply"):
                st.session_state["page"] = "Auto Apply"
                st.rerun()

    # Auto Apply page
    elif st.session_state["page"] == "Auto Apply":
        st.subheader("🤖 Automated Job Applications")

        # Make sure we have merged_data available
        if "merged_data" not in st.session_state and "analysis" in st.session_state:
            merged_data = deep_merge(default_data.copy(), st.session_state["analysis"])
            st.session_state["merged_data"] = merged_data

        if not st.session_state.get("logged_in") or "driver" not in st.session_state:
            st.warning("Please login to LinkedIn first.")
            if st.button("Go to LinkedIn Login"):
                st.session_state["page"] = "LinkedIn Login"
                st.rerun()
        elif not st.session_state.get("jobs_fetched"):
            st.warning("Please search for jobs first.")
            if st.button("Go to Job Search"):
                st.session_state["page"] = "Job Search"
                st.rerun()
        else:
            # Default to the saved resume path or allow user to enter another
            default_path = st.session_state.get("resume_path",
                                                "D:\\Academics\\Sem6\\Software labproject\\resume_parser\\kashish_resume (3).pdf")
            resume_path = st.text_input("Enter the path to your resume PDF file:", default_path)

            max_applications = st.slider("Maximum number of jobs to apply for:", 1, 10, 5)

            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            application_results = []

            if st.button("Start Auto-Applying"):
                driver = st.session_state["driver"]
                wait = st.session_state["wait"]
                job_links = st.session_state["job_links"][:max_applications]  # Apply to first N jobs
                merged_data = st.session_state.get("merged_data", {})  # Get merged data from session state

                progress_bar = progress_placeholder.progress(0)
                status_placeholder.info("Starting automated job application process...")

                for i, job in enumerate(job_links):
                    job_title = job["Job Title"]
                    job_url = job["Apply Link"]

                    # Update progress
                    progress_percent = int((i / len(job_links)) * 100)
                    progress_bar.progress(progress_percent)
                    status_placeholder.info(f"Applying to Job {i + 1}/{len(job_links)}: {job_title}")

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

                # Add button to view application history
                if st.button("View Application History"):
                    st.session_state["page"] = "Application History"
                    st.rerun()

    # Application History page
    elif st.session_state["page"] == "Application History":
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

                # Add navigation buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Find More Jobs"):
                        st.session_state["page"] = "Job Search"
                        st.rerun()
                with col2:
                    if st.button("Apply to More Jobs"):
                        st.session_state["page"] = "Auto Apply"
                        st.rerun()
            else:
                st.info("No application history found. Apply to jobs to start tracking your applications.")

                if st.button("Go to Job Search"):
                    st.session_state["page"] = "Job Search"
                    st.rerun()
        else:
            st.warning("Please save your resume data first.")

            if st.button("Go to Upload Resume"):
                st.session_state["page"] = "Upload Resume"
                st.rerun()

    # Additional Features - add at same indentation level as the elif statements
    # Add a floating help button in the sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Help & Resources")

        with st.expander("Resume Tips"):
            st.markdown("""
            ### Resume Best Practices
            - Keep your resume to 1-2 pages
            - Use bullet points for readability
            - Quantify achievements with numbers
            - Tailor your resume to each job application
            - Proofread carefully for errors
            """)

        with st.expander("LinkedIn Tips"):
            st.markdown("""
            ### Optimize Your LinkedIn Profile
            - Use a professional photo
            - Write a compelling headline
            - Complete all sections of your profile
            - Request recommendations
            - Engage with industry content regularly
            """)

        with st.expander("About This Tool"):
            st.markdown("""
            ### Automated Resume & Job Application Tool

            This application helps streamline your job search by:
            1. Analyzing your resume automatically
            2. Finding relevant job matches
            3. Auto-applying to LinkedIn jobs
            4. Tracking your application history

            For support, contact: support@resume-tool.com
            """)

        # Add feedback mechanism
        st.markdown("---")
        st.subheader("Feedback")
        feedback = st.text_area("Help us improve! Share your feedback:", max_chars=500)
        if st.button("Submit Feedback"):
            # Here you would implement storing the feedback
            st.success("Thank you for your feedback!")

if __name__ == "__main__":
    main()