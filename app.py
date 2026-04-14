from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import database as db
import os

app = Flask(__name__)
app.secret_key = 'collabrix-secret-key-change-in-production'

# Initialize database
db.init_db()

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.get_user_by_email(email)
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))

# ==================== MAIN PAGES ====================

@app.route('/dashboard')
def dashboard():
    """Dashboard home page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = db.get_task_stats()
    upcoming_tasks = db.get_upcoming_tasks(7)
    recent_projects = db.get_recent_projects(5)
    all_projects = db.get_all_projects()
    
    return render_template('dashboard.html', 
                         user_name=session['user_name'],
                         stats=stats,
                         upcoming_tasks=upcoming_tasks,
                         recent_projects=recent_projects,
                         projects=all_projects)

@app.route('/projects')
def projects():
    """Projects listing page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_projects = db.get_all_projects()
    return render_template('projects.html', 
                         user_name=session['user_name'],
                         projects=all_projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Single project page with Kanban board"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = db.get_project_by_id(project_id)
    if not project:
        return redirect(url_for('projects'))
    
    tasks = db.get_tasks_by_project(project_id)
    messages = db.get_messages_by_project(project_id)
    
    # Organize tasks by status
    tasks_by_status = {
        'todo': [],
        'inprogress': [],
        'review': [],
        'done': []
    }
    
    for task in tasks:
        status = task['status']
        if status in tasks_by_status:
            tasks_by_status[status].append(task)
    
    return render_template('project_detail.html',
                         user_name=session['user_name'],
                         project=project,
                         tasks_by_status=tasks_by_status,
                         messages=messages)

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('profile.html',
                         user_name=session['user_name'],
                         user_email=session['user_email'])

# ==================== PROJECT API ROUTES ====================

@app.route('/api/project/create', methods=['POST'])
def api_create_project():
    """Create a new project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.form
    project_id = db.create_project(
        data.get('name'),
        data.get('description'),
        data.get('start_date'),
        data.get('end_date')
    )
    return jsonify({'success': True, 'project_id': project_id})

@app.route('/api/project/<int:project_id>/update', methods=['POST'])
def api_update_project(project_id):
    """Update a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.form
    db.update_project(
        project_id,
        data.get('name'),
        data.get('description'),
        data.get('start_date'),
        data.get('end_date')
    )
    return jsonify({'success': True})

@app.route('/api/project/<int:project_id>/delete', methods=['POST'])
def api_delete_project(project_id):
    """Delete a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db.delete_project(project_id)
    return jsonify({'success': True})

# ==================== TASK API ROUTES ====================

@app.route('/api/task/create', methods=['POST'])
def api_create_task():
    """Create a new task"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.form
    task_id = db.create_task(
        int(data.get('project_id')),
        data.get('title'),
        data.get('description'),
        data.get('priority'),
        data.get('assignee'),
        data.get('due_date'),
        data.get('status', 'todo')
    )
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/api/task/<int:task_id>/status', methods=['POST'])
def api_update_task_status(task_id):
    """Update task status (for Kanban drag-drop)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json() or request.form
    status = data.get('status')
    db.update_task_status(task_id, status)
    return jsonify({'success': True})

@app.route('/api/task/<int:task_id>/update', methods=['POST'])
def api_update_task(task_id):
    """Update task details"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.form
    db.update_task(
        task_id,
        data.get('title'),
        data.get('description'),
        data.get('priority'),
        data.get('assignee'),
        data.get('due_date')
    )
    return jsonify({'success': True})

@app.route('/api/task/<int:task_id>/delete', methods=['POST'])
def api_delete_task(task_id):
    """Delete a task"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db.delete_task(task_id)
    return jsonify({'success': True})

# ==================== MESSAGE API ROUTES ====================

@app.route('/api/message/create', methods=['POST'])
def api_create_message():
    """Add a new message"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.form
    db.add_message(
        int(data.get('project_id')),
        session['user_name'],
        data.get('message')
    )
    return jsonify({'success': True})

@app.route('/api/messages/<int:project_id>')
def api_get_messages(project_id):
    """Get messages for a project (for AJAX refresh)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    messages = db.get_messages_by_project(project_id)
    return jsonify([dict(msg) for msg in messages])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))