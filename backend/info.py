from flask import Blueprint, session, request, jsonify
import os
import uuid
import yaml

info_bp = Blueprint('info', __name__)

@info_bp.route('/get_info', methods=['GET'])
def get_info():
    # Existing endpoint to fetch initial data (assumed to be session-based)
    return jsonify(session.get('info', {}))

@info_bp.route('/save_info', methods=['POST'])
def save_info():
    data = request.json
    # Restructure the data to match expected format
    formatted_data = {
        'personal_information': {
            'name': data.get('Name', ''),
            'phone': data.get('Phone Number', ''),
            'address': data.get('Address', ''),
            'city': data.get('City', ''),
            'state': data.get('State', ''),
            'country': data.get('Country', ''),
            'pin_code': data.get('Pin Code', ''),
            'gender': data.get('Gender', '')
        },
        'education': data.get('Education Details', []),
        'projects': data.get('Projects', []),
        'experience': data.get('Experience', []),
        'achievements': data.get('Achievements', []),
        'skills': data.get('Skills', []),
        'recommended_jobs': data.get('Recommended Jobs', [])
    }
    
    filename = "final_resume.yaml"
    # Update path to use backend/uploads
    os.makedirs(os.path.join(os.path.dirname(__file__), 'uploads'), exist_ok=True)
    filepath = os.path.join(os.path.dirname(__file__), 'uploads', filename)
    
    with open(filepath, 'w') as f:
        yaml.dump(formatted_data, f, default_flow_style=False)
    
    session['resume_file'] = filepath
    return jsonify({'status': 'success'})