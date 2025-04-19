# data_access_layer.py

import sqlite3
import yaml
import json
from typing import Dict, List, Any, Optional
import os

class DatabaseConnection:
    def __init__(self, db_path="resume_analyzer.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def __enter__(self):
        """Context manager entry point to establish the connection."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.connection.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point to close the connection."""
        if self.connection:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
            self.connection.close()


class ResumeRepository:
    """Data Access Layer for resume-related operations."""
    
    def __init__(self, db_path="resume_analyzer.db"):
        self.db_path = db_path
        self._create_tables_if_not_exist()
    
    def _create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist."""
        with DatabaseConnection(self.db_path) as db:
            # User profiles table
            db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                surname TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Resumes table
            db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parsed_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Skills table
            db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            ''')
            
            # Resume-Skills mapping table (many-to-many)
            db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_skills (
                resume_id INTEGER,
                skill_id INTEGER,
                PRIMARY KEY (resume_id, skill_id),
                FOREIGN KEY (resume_id) REFERENCES resumes(id),
                FOREIGN KEY (skill_id) REFERENCES skills(id)
            )
            ''')
            
            # Job applications table
            db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                job_title TEXT,
                job_url TEXT,
                status TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id)
            )
            ''')
    
    def save_user(self, user_data: Dict[str, Any]) -> int:
        """Save user information and return user ID."""
        with DatabaseConnection(self.db_path) as db:
            # Check if user exists
            db.cursor.execute(
                "SELECT id FROM users WHERE email = ?", 
                (user_data.get("email"),)
            )
            result = db.cursor.fetchone()
            
            if result:
                # Update existing user
                user_id = result["id"]
                db.cursor.execute(
                    """
                    UPDATE users SET 
                    name = ?, surname = ?, phone = ?
                    WHERE id = ?
                    """,
                    (
                        user_data.get("name", ""),
                        user_data.get("surname", ""),
                        user_data.get("phone", ""),
                        user_id
                    )
                )
                return user_id
            else:
                # Create new user
                db.cursor.execute(
                    """
                    INSERT INTO users (email, name, surname, phone)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user_data.get("email", ""),
                        user_data.get("name", ""),
                        user_data.get("surname", ""),
                        user_data.get("phone", "")
                    )
                )
                return db.cursor.lastrowid
    
    def save_resume(self, user_id: int, file_path: str, parsed_data: Dict[str, Any]) -> int:
        """Save resume information and return resume ID."""
        with DatabaseConnection(self.db_path) as db:
            # Convert parsed data to JSON string
            parsed_data_json = json.dumps(parsed_data)
            
            # Insert resume
            db.cursor.execute(
                """
                INSERT INTO resumes (user_id, file_path, parsed_data)
                VALUES (?, ?, ?)
                """,
                (user_id, file_path, parsed_data_json)
            )
            resume_id = db.cursor.lastrowid
            
            # Save skills
            self._save_resume_skills(db, resume_id, parsed_data.get("skills", []))
            
            return resume_id
    
    def _save_resume_skills(self, db, resume_id: int, skills: List[str]):
        """Save skills for a resume."""
        for skill in skills:
            # Add skill if not exists
            db.cursor.execute(
                "INSERT OR IGNORE INTO skills (name) VALUES (?)",
                (skill,)
            )
            
            # Get skill ID
            db.cursor.execute("SELECT id FROM skills WHERE name = ?", (skill,))
            skill_id = db.cursor.fetchone()["id"]
            
            # Map skill to resume
            db.cursor.execute(
                """
                INSERT OR IGNORE INTO resume_skills (resume_id, skill_id)
                VALUES (?, ?)
                """,
                (resume_id, skill_id)
            )
    
    def get_resume_by_id(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Get resume by ID."""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute(
                """
                SELECT r.*, u.email, u.name, u.surname, u.phone
                FROM resumes r
                JOIN users u ON r.user_id = u.id
                WHERE r.id = ?
                """,
                (resume_id,)
            )
            resume = db.cursor.fetchone()
            
            if not resume:
                return None
                
            # Convert row to dict
            resume_dict = dict(resume)
            
            # Parse JSON data
            if resume_dict.get("parsed_data"):
                resume_dict["parsed_data"] = json.loads(resume_dict["parsed_data"])
            
            # Get associated skills
            resume_dict["skills"] = self.get_skills_for_resume(resume_id)
            
            return resume_dict
    
    def get_skills_for_resume(self, resume_id: int) -> List[str]:
        """Get skills for a specific resume."""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute(
                """
                SELECT s.name 
                FROM skills s
                JOIN resume_skills rs ON s.id = rs.skill_id
                WHERE rs.resume_id = ?
                """,
                (resume_id,)
            )
            skills = [row["name"] for row in db.cursor.fetchall()]
            return skills
    
    def save_job_application(self, resume_id: int, job_data: Dict[str, Any]) -> int:
        """Save job application information and return application ID."""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute(
                """
                INSERT INTO job_applications (
                    resume_id, job_title, job_url, status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    resume_id,
                    job_data.get("job_title", ""),
                    job_data.get("job_url", ""),
                    job_data.get("status", "Applied")
                )
            )
            return db.cursor.lastrowid
    
    def get_job_applications(self, resume_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get job applications, optionally filtered by resume ID."""
        with DatabaseConnection(self.db_path) as db:
            query = """
                SELECT ja.*, r.file_path, u.email, u.name, u.surname
                FROM job_applications ja
                JOIN resumes r ON ja.resume_id = r.id
                JOIN users u ON r.user_id = u.id
            """
            params = ()
            
            if resume_id:
                query += " WHERE ja.resume_id = ?"
                params = (resume_id,)
            
            db.cursor.execute(query, params)
            applications = [dict(row) for row in db.cursor.fetchall()]
            return applications
    
    def update_job_application_status(self, application_id: int, status: str) -> bool:
        """Update job application status."""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute(
                "UPDATE job_applications SET status = ? WHERE id = ?",
                (status, application_id)
            )
            return db.cursor.rowcount > 0
    
    def load_resume_from_yaml(self, yaml_path: str) -> Dict[str, Any]:
        """Load resume data from a YAML file."""
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")
            
        with open(yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data
    
    def save_resume_as_yaml(self, resume_data: Dict[str, Any], yaml_path: str) -> None:
        """Save resume data to a YAML file."""
        with open(yaml_path, 'w', encoding='utf-8') as file:
            yaml.dump(resume_data, file, default_flow_style=False)


# Factory for creating the appropriate repository
class RepositoryFactory:
    @staticmethod
    def create_resume_repository(db_path="resume_analyzer.db"):
        return ResumeRepository(db_path)