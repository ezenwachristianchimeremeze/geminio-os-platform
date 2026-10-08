"""
CHIXUS Test Fixtures & Configuration
Provides isolated test database, FastAPI test client, and mock authentication headers
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import os
import tempfile
import sqlite3
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from verify_team.team_backend import create_app


class MockConfig:
    """Mock configuration for testing"""
    ADMIN_PASSKEY = "CHIXUS-ADMIN-@)@^"
    ACCESS_TOKEN = "CHI-9625-NG"
    INVALID_TOKEN = "INVALID-TOKEN-12345"


@pytest.fixture(scope="session")
def temp_db_dir():
    """Create a temporary directory for test databases"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def test_db_path(temp_db_dir):
    """Provide a unique test database path for each test"""
    db_file = Path(temp_db_dir) / f"test_{os.urandom(8).hex()}.db"
    yield str(db_file)
    
    # Cleanup
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(scope="function")
def app(test_db_path: str) -> FastAPI:
    """Create and configure a test FastAPI application with isolated database"""
    
    # Set environment variable for test database
    os.environ["VERIFY_TEAM_DB"] = test_db_path
    
    # Create the app with test configuration
    app_instance = create_app(db_path=test_db_path)
    
    # Initialize test database with schema
    _initialize_test_database(test_db_path)
    
    return app_instance


@pytest.fixture(scope="function")
def client(app: FastAPI) -> TestClient:
    """Provide FastAPI TestClient with the test app"""
    return TestClient(app)


@pytest.fixture(scope="function")
def authenticated_headers():
    """Provide mock authentication headers"""
    return {
        "x-admin-passkey": MockConfig.ADMIN_PASSKEY,
        "x-access-token": MockConfig.ACCESS_TOKEN,
    }


@pytest.fixture(scope="function")
def admin_headers():
    """Provide admin-only headers"""
    return {
        "x-admin-passkey": MockConfig.ADMIN_PASSKEY,
    }


@pytest.fixture(scope="function")
def access_token_headers():
    """Provide standard access token headers"""
    return {
        "x-access-token": MockConfig.ACCESS_TOKEN,
    }


@pytest.fixture(scope="function")
def invalid_headers():
    """Provide invalid/unauthorized headers"""
    return {
        "x-access-token": MockConfig.INVALID_TOKEN,
    }


@pytest.fixture(scope="function")
def no_headers():
    """Provide empty headers (no authentication)"""
    return {}


def _initialize_test_database(db_path: str) -> None:
    """
    Initialize test database with required schema
    
    Args:
        db_path: Path to the test database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create sync_queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create verification_ledger table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_hash TEXT UNIQUE NOT NULL,
                payload_hash TEXT NOT NULL,
                signature TEXT NOT NULL,
                timestamp REAL NOT NULL,
                verified BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create node_health table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS node_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL,
                status TEXT NOT NULL,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                uptime_seconds INTEGER,
                last_heartbeat REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_value TEXT UNIQUE NOT NULL,
                token_type TEXT DEFAULT 'access',
                is_valid BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test tokens
        cursor.execute(
            "INSERT OR IGNORE INTO tokens (token_value, token_type, is_valid) VALUES (?, ?, ?)",
            (MockConfig.ACCESS_TOKEN, "access", 1)
        )
        cursor.execute(
            "INSERT OR IGNORE INTO tokens (token_value, token_type, is_valid) VALUES (?, ?, ?)",
            (MockConfig.ADMIN_PASSKEY, "admin", 1)
        )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to initialize test database: {e}")
    
    finally:
        conn.close()


@pytest.fixture(scope="function")
def mock_sync_payload():
    """Provide mock sync payload for testing"""
    return {
        "action": "CREATE",
        "resource_id": "user_12345",
        "payload": {
            "name": "Test User",
            "email": "test@chixus.local",
            "timestamp": 1696866600.123,
        }
    }


@pytest.fixture(scope="function")
def mock_health_data():
    """Provide mock health telemetry data"""
    return {
        "node_id": "edge_node_001",
        "status": "healthy",
        "cpu_percent": 45.2,
        "memory_percent": 62.1,
        "disk_percent": 73.5,
        "uptime_seconds": 86400,
    }


@pytest.fixture(scope="function")
def mock_ledger_payload():
    """Provide mock payload for ledger verification"""
    return {
        "transaction_id": "txn_20261008_001",
        "action": "TRANSFER",
        "source": "account_A",
        "destination": "account_B",
        "amount": 100.50,
        "timestamp": 1696866600.123,
    }


__all__ = [
    "MockConfig",
    "app",
    "client",
    "authenticated_headers",
    "admin_headers",
    "access_token_headers",
    "invalid_headers",
    "no_headers",
    "mock_sync_payload",
    "mock_health_data",
    "mock_ledger_payload",
]
