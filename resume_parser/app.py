from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
import pdfminer
from pdfminer.high_level import extract_text
from resume_processing import analyze_resume
from job_suggestion import suggest_jobs, generate_linkedin_search_url
from linkedin_automation import LinkedInAutomation

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf_improved(file_path):
    """
    Enhanced PDF text extraction with multiple fallback methods
    """
    text = ""
    links = []
    
    # First attempt: Using pdfminer
    try:
        text = extract_text(file_path)
        if text.strip():
            return text, links
    except Exception as e:
        print(f"pdfminer extraction failed: {str(e)}")
    
    # Second attempt: Using PyPDF2
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        if text.strip():
            return text, links
    except Exception as e:
        print(f"PyPDF2 extraction failed: {str(e)}")
    
    raise Exception("Failed to extract text using multiple methods")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            # Save the file first
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the resume from saved file
            try:
                resume_text, links = extract_text_from_pdf_improved(filepath)
                print("Extracted text:", resume_text[:500])  # Print first 500 characters for debugging
                if not resume_text or not resume_text.strip():
                    return jsonify({'error': 'PDF appears to be empty or contains no extractable text'}), 400
            except Exception as e:
                return jsonify({'error': f'PDF text extraction failed: {str(e)}'}), 400
            
            # Analyze the resume
            try:
                extracted_data = analyze_resume(resume_text, links)
                session['analysis'] = extracted_data
                
                return jsonify({
                    'success': True,
                    'data': extracted_data
                })
            except Exception as e:
                return jsonify({'error': f'Resume analysis failed: {str(e)}'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Error processing PDF: {str(e)}'}), 400
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
    else:
        return jsonify({'error': 'Please upload a PDF file'}), 400

@app.route('/suggest_jobs', methods=['POST'])
def get_job_suggestions():
    if 'analysis' not in session:
        return jsonify({'error': 'No resume analysis found'}), 400
    
    extracted_data = session['analysis']
    try:
        # Get job suggestions
        suggested_jobs = suggest_jobs(extracted_data)
        
        # Generate LinkedIn URLs for each job
        job_links = []
        for job in suggested_jobs:
            job_links.append({
                'title': job,
                'url': generate_linkedin_search_url(job, 'India')
            })
        
        return jsonify({
            'success': True,
            'jobs': job_links
        })
    except Exception as e:
        return jsonify({'error': f'Error generating job suggestions: {str(e)}'}), 400

@app.route('/start_automation', methods=['POST'])
def start_automation():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        job_urls = data.get('jobUrls', [])
        resume_data = data.get('resumeData', {})
        
        if not all([email, password, job_urls]):
            return jsonify({'error': 'Missing required information'}), 400
        
        # Initialize LinkedIn automation
        automation = LinkedInAutomation()
        try:
            automation.setup_driver()
            
            # Login to LinkedIn
            if not automation.login(email, password):
                return jsonify({'error': 'Failed to login to LinkedIn'}), 400
            
            # Apply to each job
            results = []
            for job_url in job_urls:
                try:
                    success = automation.apply_to_job(job_url, resume_data)
                    results.append({
                        'url': job_url,
                        'success': success
                    })
                except Exception as e:
                    print(f"Error applying to job {job_url}: {str(e)}")
                    results.append({
                        'url': job_url,
                        'success': False,
                        'error': str(e)
                    })
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            automation.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)