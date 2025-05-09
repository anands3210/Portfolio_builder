from flask import Flask, render_template, request, send_file, jsonify
import os, shutil, zipfile
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Directories
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'generated_portfolios'


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# List of available templates
TEMPLATES = ['template1', 'template2', 'template3', 'template4', 'template5'] 


def parse_dynamic_entries(form_data, prefix, fields):
    entries = []
    i = 1
    while True:
        entry_data = {}

        key_for_check = f"{prefix}_{fields[0]}_{i}"
        
        if key_for_check not in form_data:
            break 

        has_data_in_entry = False
        for field in fields:
            key = f"{prefix}_{field}_{i}"
            value = form_data.get(key, '').strip()
            entry_data[field] = value
            if value:
                has_data_in_entry = True
        
        if has_data_in_entry:
            entries.append(entry_data)
        
        i += 1
    return entries


@app.route('/')
def form():
    return render_template('form.html', templates=TEMPLATES)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.to_dict()

    name = data.get('name', 'Your Name')
    about = data.get('about', '')
    contact_email = data.get('contact_email', '')
    contact_phone = data.get('contact_phone', '')
    template_choice = data.get('template', 'template5') 

    if template_choice not in TEMPLATES:
        return "Invalid template selected", 400

    education_entries = parse_dynamic_entries(data, 'edu', ['institution', 'degree', 'period', 'description'])
    experience_entries = parse_dynamic_entries(data, 'exp', ['company', 'role', 'period', 'description'])
    project_entries = parse_dynamic_entries(data, 'proj', ['title', 'description', 'link', 'technologies'])
    
    raw_skills = data.get('skills', '')
    skills = [s.strip() for s in raw_skills.split(',') if s.strip()] if raw_skills else []

    include_education = 'include_education' in data
    include_experience = 'include_experience' in data
    include_projects = 'include_projects' in data
    include_skills = 'include_skills' in data

    profile_pic_filename = None
    if 'profile_pic' in request.files:
        pic = request.files['profile_pic']
        if pic and pic.filename:
            profile_pic_filename = secure_filename(pic.filename)
            pic_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
            pic.save(pic_path)

    safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    user_folder = os.path.join(app.config['GENERATED_FOLDER'], safe_name)
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
    os.makedirs(user_folder)

    template_data = {
        'name': name,
        'about': about,
        'education_entries': education_entries,
        'skills': skills,
        'project_entries': project_entries,
        'experience_entries': experience_entries,
        'contact_email': contact_email,
        'contact_phone': contact_phone,
        'profile_pic': profile_pic_filename,
        'include_education': include_education,
        'include_experience': include_experience,
        'include_projects': include_projects,
        'include_skills': include_skills,
        'now': datetime.utcnow, 
    }

    html_content = render_template(f'{template_choice}.html', **template_data)
    with open(os.path.join(user_folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    if profile_pic_filename:
        shutil.copy(os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename),
                    os.path.join(user_folder, profile_pic_filename))

    zip_filename = f'{safe_name}_portfolio.zip'
    zip_path = os.path.join(app.config['GENERATED_FOLDER'], zip_filename)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files_in_dir in os.walk(user_folder):
            for file_item in files_in_dir:
                file_path = os.path.join(root, file_item)

                archive_name = os.path.relpath(file_path, user_folder)
                zipf.write(file_path, archive_name)
    
   

    return send_file(zip_path, as_attachment=True, download_name=zip_filename)


@app.route('/preview', methods=['POST'])
def preview():
    data = request.json

    name = data.get('name', 'Your Name')
    about = data.get('about', '')
    contact_email = data.get('contact_email', '')
    contact_phone = data.get('contact_phone', '')
    template_choice = data.get('template', 'template_modern')
    profile_pic_value = data.get('profile_pic', None) 

    if template_choice not in TEMPLATES:
        return jsonify({"error": "Invalid template"}), 400

    education_entries = data.get('education_entries', [])
    experience_entries = data.get('experience_entries', [])
    project_entries = data.get('project_entries', [])
    
    raw_skills = data.get('skills', '')
    skills = [s.strip() for s in raw_skills.split(',') if s.strip()] if raw_skills else []

    include_education = data.get('include_education', True)
    include_experience = data.get('include_experience', True)
    include_projects = data.get('include_projects', True)
    include_skills = data.get('include_skills', True)
    
    template_data = {
        'name': name,
        'about': about,
        'education_entries': education_entries,
        'skills': skills,
        'project_entries': project_entries,
        'experience_entries': experience_entries,
        'contact_email': contact_email,
        'contact_phone': contact_phone,
        'profile_pic': profile_pic_value,
        'include_education': include_education,
        'include_experience': include_experience,
        'include_projects': include_projects,
        'include_skills': include_skills,
        'now': datetime.utcnow,
    }
    
    html_content = render_template(f'{template_choice}.html', **template_data)
    return jsonify({"html": html_content})


if __name__ == '__main__':
    app.run(debug=True)