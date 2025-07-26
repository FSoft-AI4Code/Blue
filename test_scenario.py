#!/usr/bin/env python3
"""
Test scenario script for Blue CLI
This script creates realistic code changes to test the monitoring system
"""

import os
import time
import shutil
from pathlib import Path

def create_test_project():
    """Create a test project directory with initial files"""
    test_dir = Path("test_codebase")
    
    # Clean up if exists
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    test_dir.mkdir()
    
    # Create initial Python file
    with open(test_dir / "main.py", "w") as f:
        f.write('''#!/usr/bin/env python3
"""
Main application entry point
"""

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')
    
    # Create initial JavaScript file
    with open(test_dir / "app.js", "w") as f:
        f.write('''// Simple web application
console.log("Starting application...");

const config = {
    port: 3000,
    host: 'localhost'
};
''')
    
    print(f"✅ Created test project in: {test_dir.absolute()}")
    return test_dir

def simulate_development_session(test_dir, delay=3):
    """Simulate a realistic development session with timed changes"""
    
    print(f"\n🚀 Starting development simulation (changes every {delay} seconds)")
    print("💡 You should run 'python blue.py --dir test_codebase' in another terminal")
    print("Press Ctrl+C to stop the simulation\n")
    
    try:
        # Change 1: Add a new function to main.py
        time.sleep(delay)
        print("📝 Adding user authentication function...")
        with open(test_dir / "main.py", "a") as f:
            f.write('''
def authenticate_user(username, password):
    """Authenticate user credentials"""
    if not username or not password:
        raise ValueError("Username and password required")
    
    # TODO: Add actual authentication logic
    return username == "admin" and password == "secret"
''')
        
        # Change 2: Modify JavaScript - add error handling
        time.sleep(delay)
        print("📝 Adding error handling to JavaScript...")
        with open(test_dir / "app.js", "a") as f:
            f.write('''
function handleError(error) {
    console.error('Application error:', error);
    // TODO: Send to logging service
}

try {
    console.log(`Server will run on ${config.host}:${config.port}`);
} catch (error) {
    handleError(error);
}
''')
        
        # Change 3: Create new database module
        time.sleep(delay)
        print("📝 Creating database module...")
        with open(test_dir / "database.py", "w") as f:
            f.write('''"""
Database connection and operations
"""

import sqlite3
from typing import Optional, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def create_user_table(self) -> None:
        """Create users table if not exists"""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
''')
        
        # Change 4: Update main.py to use database
        time.sleep(delay)
        print("📝 Integrating database into main application...")
        with open(test_dir / "main.py", "a") as f:
            f.write('''
from database import DatabaseManager

def setup_database():
    """Initialize database connection and tables"""
    db = DatabaseManager("app.db")
    db.connect()
    db.create_user_table()
    return db

def enhanced_authenticate_user(username, password, db_manager):
    """Enhanced authentication with database lookup"""
    # This would typically query the database
    # For now, fall back to simple auth
    return authenticate_user(username, password)
''')
        
        # Change 5: Add configuration file
        time.sleep(delay)
        print("📝 Adding configuration management...")
        with open(test_dir / "config.py", "w") as f:
            f.write('''"""
Application configuration management
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration class"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'app.db')
        self.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.port = int(os.getenv('PORT', '3000'))
        self.host = os.getenv('HOST', 'localhost')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'database_url': self.database_url,
            'secret_key': self.secret_key,
            'debug': self.debug,
            'port': self.port,
            'host': self.host
        }
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.secret_key or self.secret_key == 'dev-secret-key':
            print("Warning: Using default secret key in production!")
            return False
        return True

# Global configuration instance
config = Config()
''')
        
        # Change 6: Create API endpoints file
        time.sleep(delay)
        print("📝 Creating API endpoints...")
        with open(test_dir / "api.py", "w") as f:
            f.write('''"""
REST API endpoints
"""

from typing import Dict, Any
import json

class APIResponse:
    """Standard API response format"""
    
    def __init__(self, data: Any = None, error: str = None, status_code: int = 200):
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        response = {
            'success': self.error is None,
            'data': self.data,
            'error': self.error
        }
        return json.dumps(response)

def login_endpoint(username: str, password: str) -> APIResponse:
    """Handle user login requests"""
    try:
        # This would integrate with our auth system
        if not username or not password:
            return APIResponse(
                error="Username and password required",
                status_code=400
            )
        
        # Simulate authentication
        if username == "admin" and password == "secret":
            return APIResponse(data={"token": "fake-jwt-token"})
        else:
            return APIResponse(
                error="Invalid credentials",
                status_code=401
            )
    
    except Exception as e:
        return APIResponse(
            error=f"Internal server error: {str(e)}",
            status_code=500
        )

def health_check() -> APIResponse:
    """Health check endpoint"""
    return APIResponse(data={"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"})
''')
        
        # Change 7: Update main.py with final integration
        time.sleep(delay)
        print("📝 Final integration in main.py...")
        with open(test_dir / "main.py", "a") as f:
            f.write('''

def create_app():
    """Create and configure the application"""
    from config import config
    from api import health_check, login_endpoint
    
    if not config.validate():
        print("Configuration validation failed!")
        return None
    
    print("Application created successfully!")
    print(f"Configuration: {config.to_dict()}")
    return {"config": config, "endpoints": [health_check, login_endpoint]}

def run_server():
    """Start the application server"""
    app = create_app()
    if app:
        print(f"Server starting on {app['config'].host}:{app['config'].port}")
        # In a real app, this would start the actual server
        print("🚀 Server is running! (simulated)")

if __name__ == "__main__":
    print("=== Enhanced Application ===")
    db = setup_database()
    run_server()
''')
        
        # Change 8: Add some TypeScript for variety
        time.sleep(delay)
        print("📝 Adding TypeScript interface definitions...")
        with open(test_dir / "types.ts", "w") as f:
            f.write('''// TypeScript type definitions

export interface User {
    id: number;
    username: string;
    createdAt: Date;
}

export interface AuthRequest {
    username: string;
    password: string;
}

export interface APIResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
}

export class UserService {
    private baseUrl: string;
    
    constructor(baseUrl: string = 'http://localhost:3000') {
        this.baseUrl = baseUrl;
    }
    
    async login(credentials: AuthRequest): Promise<APIResponse<{token: string}>> {
        // Implementation would go here
        throw new Error('Not implemented');
    }
    
    async getCurrentUser(): Promise<APIResponse<User>> {
        // Implementation would go here
        throw new Error('Not implemented');
    }
}
''')
        
        print("\n✅ Development simulation completed!")
        print("📊 Summary of changes:")
        print("  - Added authentication functions")
        print("  - Created database module with class")
        print("  - Added configuration management")
        print("  - Built API endpoints")
        print("  - Added TypeScript definitions")
        print("  - Multiple function additions and modifications")
        
    except KeyboardInterrupt:
        print("\n⏹️  Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")

def cleanup_test_project():
    """Clean up the test project"""
    test_dir = Path("test_codebase")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"🧹 Cleaned up test project: {test_dir}")

def main():
    """Main test runner"""
    print("🧪 Blue CLI Test Scenario Generator")
    print("=" * 50)
    
    # Create test project
    test_dir = create_test_project()
    
    print("\n📋 Instructions:")
    print("1. Open a new terminal")
    print(f"2. Run: python blue.py --dir {test_dir}")
    print("3. Come back to this terminal and press Enter to start the simulation")
    print("4. Watch the Blue CLI detect and comment on changes!")
    
    input("\nPress Enter when you're ready to start the simulation...")
    
    # Run simulation
    simulate_development_session(test_dir)
    
    # Ask about cleanup
    cleanup_choice = input("\nDo you want to clean up the test project? (y/N): ")
    if cleanup_choice.lower() in ['y', 'yes']:
        cleanup_test_project()
    else:
        print(f"📁 Test project preserved at: {test_dir.absolute()}")

if __name__ == "__main__":
    main()