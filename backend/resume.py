from flask import Blueprint, request, session, jsonify
import os
import PyPDF2
import google.generativeai as genai
from datetime import datetime
from werkzeug.utils import secure_filename
import re

resume_bp = Blueprint('resume', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure Google Gemini API
genai.configure(api_key='AIzaSyAfAZy6iQYSoTnUNegAfIGY2ZekI5K3x20')

def extract_text_from_pdf(file_path):
    """Extract text from the uploaded PDF file."""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        return text

def analyze_text_with_gemini(text):
    """Analyze the extracted text using Google Gemini API."""
    print("Extracted resume text:", text)
    prompt = f"""
    Analyze the following resume text and extract the following details:
    - Name
    - Phone Number
    - Address (including City, State, Country, Pin Code)
    - Gender
    - Education Details (degrees, institutions, years)
    - Projects (titles and dates if available)
    - Experience (job titles, companies, dates)
    - Achievements
    - Skills (list all technologies and skills mentioned)
    - Calculate years of experience for each skill/technology:
      - If mentioned in coursework, assign 4 years of experience.
      - For projects or work experience, calculate based on dates provided (e.g., 'Jan 2020 - Dec 2022' = 2 years).
      - Use today's date ({datetime.today().strftime('%Y-%m-%d')}) for ongoing roles (e.g., 'Jan 2020 - Present').
    - Recommend 10-15 suitable jobs based on the skills (just give the names of he jobs).

    Resume Text:
    {text}
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        if not response or not hasattr(response, 'text'):
            print("API response is empty or invalid")
            raise ValueError("No valid response from Gemini API")
        analyzed_text = response.text
        print("Gemini API response:", analyzed_text)
    except Exception as e:
        print(f"Gemini API call failed: {str(e)}")
        raise

    # Initialize the data dictionary
    data = {
        'Name': '',
        'Phone Number': '',
        'Address': '',
        'City': '',
        'State': '',
        'Country': '',
        'Pin Code': '',
        'Gender': '',
        'Education Details': [],
        'Projects': [],
        'Experience': [],
        'Achievements': [],
        'Skills': [],
        'Experience Per Skill': {},
        'Recommended Jobs': []
    }
    
    # Parse the response
    lines = analyzed_text.split('\n')
    current_section = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Define regex patterns
        single_value_regex = r'^\*\s*(?:\*\*|)(.*?)(?:\*\*|)[:\-]\s*(.*)'
        multi_value_regex = r'\*\s*\*\*(.*?)\*\*:\s*(.*)'

        # Process both regex patterns
        single_match = re.match(single_value_regex, line)
        multi_match = re.match(multi_value_regex, line)
        
        processed = False

        # Handle single-value regex
        if single_match:
            field = single_match.group(1).strip()
            value = single_match.group(2).strip()
            if field in data:
                if field == 'Address':
                    address_line = value
                    address_parts = [part.strip() for part in address_line.split(',') if part.strip()]
                    if address_parts:
                        data['Address'] = address_parts[0]
                        if len(address_parts) > 1:
                            data['City'] = address_parts[-3] if len(address_parts) >= 3 else ''
                            data['State'] = address_parts[-2] if len(address_parts) >= 2 else ''
                            data['Country'] = address_parts[-1].split('(')[0].strip()
                            if 'Pin Code' in address_line or 'Pin code' in address_line:
                                pin_code_part = address_line.split('Pin Code')[-1].strip('() ') if 'Pin Code' in address_line else address_line.split('Pin code')[-1].strip('() ')
                                # Handle 'not provided' case
                                data['Pin Code'] = '' if 'not provided' in pin_code_part.lower() else pin_code_part
                elif field == "Skills":
                    data['Skills'].extend([s.strip() for s in value.split(',') if s.strip()])
                    processed = True
                else:
                    data[field] = value
                    processed = True
            elif field.startswith("Skills"):
                data['Skills'].extend([s.strip() for s in value.split(',') if s.strip()])
                processed = True

        # Handle multi-value regex
        if multi_match and not processed:
            field = multi_match.group(1).strip()
            value = multi_match.group(2).strip()
            if field in data:
                if field == 'Address':
                    address_line = value
                    address_parts = [part.strip() for part in address_line.split(',') if part.strip()]
                    if address_parts:
                        data['Address'] = address_parts[0]
                        if len(address_parts) > 1:
                            data['City'] = address_parts[-3] if len(address_parts) >= 3 else ''
                            data['State'] = address_parts[-2] if len(address_parts) >= 2 else ''
                            data['Country'] = address_parts[-1].split('(')[0].strip()
                            if 'Pin Code' in address_line or 'Pin code' in address_line:
                                pin_code_part = address_line.split('Pin Code')[-1].strip('() ') if 'Pin Code' in address_line else address_line.split('Pin code')[-1].strip('() ')
                                # Handle 'not provided' case
                                data['Pin Code'] = '' if 'not provided' in pin_code_part.lower() else pin_code_part
                elif field == "Skills":
                    data['Skills'].extend([s.strip() for s in value.split(',') if s.strip()])
                    processed = True
                else:
                    data[field] = value
                    processed = True
            elif field.startswith("Skills"):
                data['Skills'].extend([s.strip() for s in value.split(',') if s.strip()])
                processed = True

        # If neither regex matched or processed the line, check for section headers and list items
        if not processed:
            # Detect section headers
            if line.startswith('**') and line.endswith(':**'):
                section_name = line.replace('**', '').replace(':', '').strip()
                if 'Education' in section_name:
                    current_section = 'Education Details'
                elif 'Projects' in section_name:
                    current_section = 'Projects'
                elif 'Experience' in section_name or 'Work Experience' in section_name:
                    current_section = 'Experience'
                elif 'Achievements' in section_name:
                    current_section = 'Achievements'
                elif 'Skills' in section_name:
                    current_section = 'Skills'
                elif 'Experience' in section_name and 'Skill' in section_name:
                    current_section = 'Experience Per Skill'
                elif 'Recommended Jobs' in section_name:
                    current_section = 'Recommended Jobs'
                else:
                    current_section = None

            # Handle list items under sections
            elif current_section:
                if line.startswith('*'):
                    item = line.lstrip('*').strip()
                    if current_section == 'Skills' and ':' in item:
                        _, skills = item.split(':', 1)
                        skills_list = [s.strip().lstrip('*').strip() for s in skills.split(',') if s.strip()]
                        data['Skills'].extend(skills_list)
                    elif current_section == 'Experience Per Skill' and ':' in item:
                        skill_part, exp = item.split(':', 1)
                        skill = skill_part.strip()
                        exp = exp.strip()
                        
                        # Extract years from different formats
                        years = 0
                        if 'Coursework assumption' in exp:
                            years = 4
                        elif '~' in exp:
                            # Handle approximate years (e.g., "~1 year")
                            match = re.search(r'~?\s*(\d+(\.\d+)?)', exp)
                            if match:
                                years = float(match.group(1))
                        elif '<1' in exp or 'less than 1' in exp.lower():
                            years = 0.5
                        else:
                            # Try to extract numeric years
                            match = re.search(r'(\d+(\.\d+)?)', exp)
                            if match:
                                years = float(match.group(1))
                        
                        # Store the experience years
                        skill = skill.strip('*: ').replace('**', '')  # Clean up skill name
                        data['Experience Per Skill'][skill] = years
                        
                        # Add skill to Skills list if not already present
                        if skill not in data['Skills']:
                            data['Skills'].append(skill)
                    elif current_section in ['Education Details', 'Projects', 'Experience', 'Achievements']:
                        data[current_section].append(item)
                elif current_section == 'Recommended Jobs' and line[0].isdigit() and '.' in line:
                    job = line.split('.', 1)[1].strip()
                    # Only keep the job title, remove explanations
                    job = job.split('-')[0].strip()
                    job = job.split(',')[0].strip()
                    data['Recommended Jobs'].append(job)

        i += 1

    print("Parsed data:", data)
    return data

@resume_bp.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload and analysis."""
    print("Request files:", request.files)
    try:
        if 'resumeFile' not in request.files:
            return jsonify({'message': 'No file uploaded'}), 400

        file = request.files['resumeFile']

        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(file_path)

            text = extract_text_from_pdf(file_path)
            info = analyze_text_with_gemini(text)
            session['info'] = info

            return jsonify({'message': 'Resume analyzed successfully'})

        return jsonify({'message': 'Invalid file type'}), 400

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@resume_bp.route('/api/get_info', methods=['GET'])
def get_info():
    info = session.get('info', {})
    return jsonify(info)