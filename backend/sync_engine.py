"""
Local Edge Sync Engine for Geminio OS Platform
Handles offline queuing and synchronization with central backend
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import sqlite3
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Sync operation status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SyncPriority(str, Enum):
    """Queue priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class SyncQueueItem:
    """Represents a queued sync operation"""
    id: str
    operation_type: str
    payload: Dict[str, Any]
    status: SyncStatus
    priority: SyncPriority
    created_at: datetime
    updated_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = int(self.priority.value)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['payload'] = json.dumps(self.payload)
        data['metadata'] = json.dumps(self.metadata) if self.metadata else None
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncQueueItem':
        """Reconstruct from stored data"""
        data['status'] = SyncStatus(data['status'])
        data['priority'] = SyncPriority(int(data['priority']))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['payload'] = json.loads(data['payload'])
        data['metadata'] = json.loads(data['metadata']) if data['metadata'] else None
        return cls(**data)


class SyncEngine:
    """
    Local Edge Sync Engine for Geminio OS
    Manages offline queuing and batch synchronization
    """

    def __init__(self, db_path: str = "verify_team.db"):
        """
        Initialize the sync engine
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection_pool: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize SQLite database with offline_sync_queue table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create offline_sync_queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_sync_queue (
                    id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    error_message TEXT,
                    metadata TEXT,
                    synced_at TEXT,
                    response_data TEXT
                )
            """)

            # Create indices for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_status 
                ON offline_sync_queue(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_priority 
                ON offline_sync_queue(priority)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_created 
                ON offline_sync_queue(created_at DESC)
            """)

            # Create sync_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_queued INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    avg_sync_time_ms REAL DEFAULT 0,
                    device_id TEXT
                )
            """)

            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.connection_pool is None:
            self.connection_pool = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False
            )
            self.connection_pool.row_factory = sqlite3.Row
        return self.connection_pool

    def enqueue_sync(
        self,
        operation_type: str,
        payload: Dict[str, Any],
        priority: SyncPriority = SyncPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enqueue a sync operation
        
        Args:
            operation_type: Type of operation (e.g., 'create', 'update', 'delete')
            payload: Operation payload data
            priority: Priority level (default: NORMAL)
            metadata: Optional metadata dict
            
        Returns:
            Operation ID (UUID)
        """
        item_id = str(uuid.uuid4())
        now = datetime.utcnow()

        item = SyncQueueItem(
            id=item_id,
            operation_type=operation_type,
            payload=payload,
            status=SyncStatus.PENDING,
            priority=priority,
            created_at=now,
            updated_at=now,
            metadata=metadata
        )

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            data = item.to_dict()

            cursor.execute("""
                INSERT INTO offline_sync_queue 
                (id, operation_type, payload, status, priority, 
                 created_at, updated_at, retry_count, max_retries, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['operation_type'], data['payload'],
                data['status'], data['priority'], data['created_at'],
                data['updated_at'], data['retry_count'], data['max_retries'],
                data['metadata']
            ))

            conn.commit()
            logger.info(f"Enqueued sync operation: {item_id} ({operation_type})")
            return item_id

        except Exception as e:
            logger.error(f"Failed to enqueue sync operation: {e}")
            raise

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status
        
        Returns:
            Dictionary with queue statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Total items
            cursor.execute("SELECT COUNT(*) FROM offline_sync_queue")
            total = cursor.fetchone()[0]

            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM offline_sync_queue 
                GROUP BY status
            """)
            status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

            # By priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM offline_sync_queue 
                GROUP BY priority
            """)
            priority_breakdown = {str(SyncPriority(row[0]).name): row[1] 
                                for row in cursor.fetchall()}

            # Oldest pending
            cursor.execute("""
                SELECT created_at FROM offline_sync_queue 
                WHERE status = 'pending' 
                ORDER BY created_at ASC LIMIT 1
            """)
            oldest_pending = cursor.fetchone()

            return {
                "total_queued": total,
                "by_status": status_breakdown,
                "by_priority": priority_breakdown,
                "oldest_pending_at": oldest_pending[0] if oldest_pending else None,
                "database": self.db_path,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}

    def get_pending_items(self, limit: int = 10) -> List[SyncQueueItem]:
        """
        Get pending sync items ordered by priority
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of pending SyncQueueItem objects
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM offline_sync_queue 
                WHERE status = 'pending' 
                ORDER BY priority ASC, created_at ASC
                LIMIT ?
            """, (limit,))

            items = []
            for row in cursor.fetchall():
                item_dict = dict(row)
                items.append(SyncQueueItem.from_dict(item_dict))

            return items

        except Exception as e:
            logger.error(f"Failed to get pending items: {e}")
            return []

    def mark_processing(self, item_id: str) -> bool:
        """Mark an item as processing"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE offline_sync_queue 
                SET status = 'processing', updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), item_id))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to mark item as processing: {e}")
            return False

    def mark_completed(
        self,
        item_id: str,
        response_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark an item as completed"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE offline_sync_queue 
                SET status = 'completed', 
                    updated_at = ?, 
                    synced_at = ?,
                    response_data = ?
                WHERE id = ?
            """, (
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                json.dumps(response_data) if response_data else None,
                item_id
            ))

            conn.commit()
            logger.info(f"Marked {item_id} as completed")
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to mark item as completed: {e}")
            return False

    def mark_failed(self, item_id: str, error_message: str) -> bool:
        """Mark an item as failed and handle retry logic"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get current retry count
            cursor.execute(
                "SELECT retry_count, max_retries FROM offline_sync_queue WHERE id = ?",
                (item_id,)
            )
            row = cursor.fetchone()

            if not row:
                return False

            retry_count = row[0] + 1
            max_retries = row[1]

            # Determine if we should retry
            if retry_count < max_retries:
                new_status = SyncStatus.RETRYING.value
            else:
                new_status = SyncStatus.FAILED.value

            cursor.execute("""
                UPDATE offline_sync_queue 
                SET status = ?, 
                    updated_at = ?, 
                    retry_count = ?,
                    error_message = ?
                WHERE id = ?
            """, (
                new_status,
                datetime.utcnow().isoformat(),
                retry_count,
                error_message,
                item_id
            ))

            conn.commit()
            logger.warning(
                f"Marked {item_id} as {new_status} "
                f"(retry {retry_count}/{max_retries}): {error_message}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to mark item as failed: {e}")
            return False

    def cleanup_old_items(self, days: int = 30) -> int:
        """
        Delete completed/failed items older than specified days
        
        Args:
            days: Number of days to retain
            
        Returns:
            Number of items deleted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute("""
                DELETE FROM offline_sync_queue 
                WHERE status IN ('completed', 'failed') 
                AND updated_at < ?
            """, (cutoff_date,))

            conn.commit()
            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} old sync items")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old items: {e}")
            return 0

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get sync statistics for specified time period"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(
                        (julianday(updated_at) - julianday(created_at)) * 24 * 60 * 1000
                    ) as avg_duration_ms
                FROM offline_sync_queue 
                WHERE created_at > ?
                GROUP BY status
            """, (cutoff_time,))

            stats = {
                "period_hours": hours,
                "cutoff_time": cutoff_time,
                "by_status": {}
            }

            for row in cursor.fetchall():
                stats["by_status"][row[0]] = {
                    "count": row[1],
                    "avg_duration_ms": round(row[2], 2) if row[2] else 0
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self) -> None:
        """Close database connection"""
        if self.connection_pool:
            self.connection_pool.close()
            self.connection_pool = None
            logger.info("Database connection closed")


# Singleton instance
_sync_engine_instance: Optional[SyncEngine] = None


def get_sync_engine(db_path: str = "verify_team.db") -> SyncEngine:
    """Get or create singleton sync engine instance"""
    global _sync_engine_instance
    if _sync_engine_instance is None:
        _sync_engine_instance = SyncEngine(db_path)
    return _sync_engine_instance
