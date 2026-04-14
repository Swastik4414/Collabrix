import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/collabrix')

def get_db_connection():
    """Create and return a database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initialize the database with all tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'medium',
            assignee TEXT,
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            sender_name TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert demo user if not exists
    cursor.execute("SELECT * FROM users WHERE email = 'demo@collabrix.com'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
        ''', ('Demo User', 'demo@collabrix.com', 'demo123'))
    
    # Insert sample project if no projects exist
    cursor.execute("SELECT * FROM projects")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO projects (name, description, start_date, end_date)
            VALUES (%s, %s, %s, %s)
        ''', ('Sample Project', 'This is a sample project to get started', '2026-04-01', '2026-05-01'))
        conn.commit()
        
        # Get the project id
        cursor.execute("SELECT id FROM projects ORDER BY id DESC LIMIT 1")
        project_id = cursor.fetchone()[0]
        
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
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', task)
        
        # Sample messages
        sample_messages = [
            (project_id, 'Demo User', 'Welcome to Collabrix! This is the team messaging area.'),
            (project_id, 'Demo User', 'You can send messages to your team members here.'),
        ]
        
        for msg in sample_messages:
            cursor.execute('''
                INSERT INTO messages (project_id, sender_name, message)
                VALUES (%s, %s, %s)
            ''', msg)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Update all other functions to use psycopg2 syntax
# (Replace ? with %s for PostgreSQL)

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

