import sqlite3
from datetime import datetime

DB_NAME = 'collabrix.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with all tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'medium',
            assignee TEXT,
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            sender_name TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    # Insert demo user if not exists
    cursor.execute("SELECT * FROM users WHERE email = 'demo@collabrix.com'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        ''', ('Demo User', 'demo@collabrix.com', 'demo123'))
    
    # Insert sample project if no projects exist
    cursor.execute("SELECT * FROM projects")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO projects (name, description, start_date, end_date)
            VALUES (?, ?, ?, ?)
        ''', ('Sample Project', 'This is a sample project to get started', '2026-04-01', '2026-05-01'))
        project_id = cursor.lastrowid
        
        # Sample tasks
        sample_tasks = [
            (project_id, 'Design Database Schema', 'Create tables for users, projects, tasks', 'done', 'high', 'Demo User', '2026-04-05'),
            (project_id, 'Build Login System', 'Implement user authentication', 'inprogress', 'high', 'Demo User', '2026-04-10'),
            (project_id, 'Create Kanban Board', 'Build drag-drop task board', 'todo', 'medium', 'Demo User', '2026-04-15'),
            (project_id, 'Add Messaging Feature', 'Team chat functionality', 'todo', 'low', 'Demo User', '2026-04-20'),
        ]
        
        for task in sample_tasks:
            cursor.execute('''
                INSERT INTO tasks (project_id, title, description, status, priority, assignee, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', task)
        
        # Sample messages
        sample_messages = [
            (project_id, 'Demo User', 'Welcome to Collabrix! This is the team messaging area.'),
            (project_id, 'Demo User', 'You can send messages to your team members here.'),
        ]
        
        for msg in sample_messages:
            cursor.execute('''
                INSERT INTO messages (project_id, sender_name, message)
                VALUES (?, ?, ?)
            ''', msg)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_user_by_email(email):
    """Get user by email"""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def get_all_projects():
    """Get all projects"""
    conn = get_db_connection()
    projects = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return projects

def get_project_by_id(project_id):
    """Get a single project by ID"""
    conn = get_db_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return project

def create_project(name, description, start_date, end_date):
    """Create a new project"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (name, description, start_date, end_date)
        VALUES (?, ?, ?, ?)
    ''', (name, description, start_date, end_date))
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id

def update_project(project_id, name, description, start_date, end_date):
    """Update a project"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE projects SET name = ?, description = ?, start_date = ?, end_date = ?
        WHERE id = ?
    ''', (name, description, start_date, end_date, project_id))
    conn.commit()
    conn.close()

def delete_project(project_id):
    """Delete a project (tasks and messages cascade)"""
    conn = get_db_connection()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def get_tasks_by_project(project_id):
    """Get all tasks for a project"""
    conn = get_db_connection()
    tasks = conn.execute('''
        SELECT * FROM tasks WHERE project_id = ? ORDER BY 
        CASE priority 
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
        END, due_date ASC
    ''', (project_id,)).fetchall()
    conn.close()
    return tasks

def create_task(project_id, title, description, priority, assignee, due_date, status='todo'):
    """Create a new task"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (project_id, title, description, priority, assignee, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (project_id, title, description, priority, assignee, due_date, status))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def update_task_status(task_id, status):
    """Update task status"""
    conn = get_db_connection()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

def update_task(task_id, title, description, priority, assignee, due_date):
    """Update task details"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE tasks SET title = ?, description = ?, priority = ?, assignee = ?, due_date = ?
        WHERE id = ?
    ''', (title, description, priority, assignee, due_date, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    """Delete a task"""
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_messages_by_project(project_id):
    """Get all messages for a project"""
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT * FROM messages WHERE project_id = ? ORDER BY timestamp ASC
    ''', (project_id,)).fetchall()
    conn.close()
    return messages

def add_message(project_id, sender_name, message):
    """Add a new message"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (project_id, sender_name, message)
        VALUES (?, ?, ?)
    ''', (project_id, sender_name, message))
    conn.commit()
    conn.close()

def get_task_stats():
    """Get task statistics across all projects"""
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()['count']
    done = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'done'").fetchone()['count']
    inprogress = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'inprogress'").fetchone()['count']
    conn.close()
    return {
        'total': total,
        'done': done,
        'inprogress': inprogress,
        'pending': total - done
    }

def get_upcoming_tasks(days=7):
    """Get tasks due within next X days"""
    conn = get_db_connection()
    tasks = conn.execute('''
        SELECT t.*, p.name as project_name 
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.status != 'done' AND t.due_date IS NOT NULL
        AND date(t.due_date) <= date('now', ?)
        ORDER BY t.due_date ASC
        LIMIT 10
    ''', (f'+{days} days',)).fetchall()
    conn.close()
    return tasks

def get_recent_projects(limit=5):
    """Get most recent projects"""
    conn = get_db_connection()
    projects = conn.execute('''
        SELECT * FROM projects ORDER BY created_at DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return projects

if __name__ == '__main__':
    init_db()