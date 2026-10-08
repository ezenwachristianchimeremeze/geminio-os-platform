"""
CHIXUS Edge Sync Engine with Batch Processing & Last-Write-Wins Conflict Resolution
Manages offline queuing, batch synchronization, and conflict resolution
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import sqlite3
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

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
    CONFLICT_RESOLVED_DISCARDED = "conflict_resolved_discarded"


class SyncPriority(str, Enum):
    """Queue priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class ConflictResolutionStrategy(str, Enum):
    """Conflict resolution strategies"""
    LAST_WRITE_WINS = "lww"
    FIRST_WRITE_WINS = "fww"
    MANUAL = "manual"


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


# ============================================================================
# Request/Response Models
# ============================================================================

class BatchSyncPayload(BaseModel):
    """Individual payload in batch sync"""
    operation_type: str = Field(..., description="Type of operation")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    data: Dict[str, Any] = Field(..., description="Operation data")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    signature: Optional[str] = Field(None, description="Optional HMAC signature")


class BatchSyncRequest(BaseModel):
    """Request model for batch sync"""
    node_id: str = Field(..., description="Source node identifier")
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique batch identifier")
    payloads: List[BatchSyncPayload] = Field(..., description="List of sync payloads")
    conflict_strategy: str = Field(default="lww", description="Conflict resolution strategy")


class BatchSyncResult(BaseModel):
    """Result of processing a single payload"""
    operation_type: str
    resource_id: Optional[str]
    status: str
    conflict_detected: bool
    conflict_reason: Optional[str] = None
    local_timestamp: Optional[str] = None
    incoming_timestamp: str


class BatchSyncResponse(BaseModel):
    """Response for batch sync"""
    success: bool
    batch_id: str
    node_id: str
    total_payloads: int
    processed_payloads: int
    successful: int
    conflicts: int
    failed: int
    results: List[BatchSyncResult]
    timestamp: str


# ============================================================================
# Database Layer
# ============================================================================

class SyncEngine:
    """
    CHIXUS Edge Sync Engine
    Manages offline queuing, batch synchronization, and LWW conflict resolution
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
        """Initialize SQLite database with sync tables"""
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
                    response_data TEXT,
                    conflict_resolution_status TEXT DEFAULT NULL
                )
            """)

            # Create sync_batch_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_batch_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL UNIQUE,
                    node_id TEXT NOT NULL,
                    total_payloads INTEGER NOT NULL,
                    successful_payloads INTEGER NOT NULL,
                    conflict_payloads INTEGER NOT NULL,
                    failed_payloads INTEGER NOT NULL,
                    conflict_strategy TEXT NOT NULL,
                    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create sync_conflict_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_conflict_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    resource_id TEXT,
                    operation_type TEXT NOT NULL,
                    incoming_timestamp TEXT NOT NULL,
                    local_timestamp TEXT NOT NULL,
                    resolution_strategy TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_batch_history_node_id
                ON sync_batch_history(node_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_conflict_log_batch_id
                ON sync_conflict_log(batch_id)
            """)

            # Create sync_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_queued INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    conflicts_resolved INTEGER DEFAULT 0,
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

    def _extract_timestamp_from_payload(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract updated_at timestamp from payload
        Searches for common timestamp field names
        
        Args:
            payload: The payload dictionary
            
        Returns:
            ISO timestamp string or None
        """
        timestamp_keys = ['updated_at', 'timestamp', 'updated', 'modified_at', 'last_modified']
        
        for key in timestamp_keys:
            if key in payload and payload[key]:
                return str(payload[key])
        
        return None

    def _compare_timestamps(self, ts1: str, ts2: str) -> int:
        """
        Compare two ISO timestamps
        
        Args:
            ts1: First timestamp
            ts2: Second timestamp
            
        Returns:
            1 if ts1 > ts2, -1 if ts1 < ts2, 0 if equal
        """
        try:
            dt1 = datetime.fromisoformat(ts1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(ts2.replace('Z', '+00:00'))
            
            if dt1 > dt2:
                return 1
            elif dt1 < dt2:
                return -1
            else:
                return 0
        except Exception as e:
            logger.warning(f"Failed to compare timestamps: {e}")
            return 0

    def _resolve_lww_conflict(
        self,
        incoming_timestamp: str,
        local_timestamp: str,
        batch_id: str,
        resource_id: Optional[str],
        operation_type: str
    ) -> Tuple[bool, str]:
        """
        Resolve conflict using Last-Write-Wins strategy
        
        Args:
            incoming_timestamp: Timestamp of incoming payload
            local_timestamp: Timestamp of local record
            batch_id: Batch ID for logging
            resource_id: Resource identifier
            operation_type: Operation type
            
        Returns:
            Tuple of (should_apply: bool, reason: str)
        """
        cmp = self._compare_timestamps(incoming_timestamp, local_timestamp)
        
        if cmp > 0:
            # Incoming is newer, apply it
            action = "applied"
            should_apply = True
        elif cmp < 0:
            # Local is newer, discard incoming
            action = "discarded"
            should_apply = False
        else:
            # Timestamps are equal, apply for idempotency
            action = "applied_equal_timestamp"
            should_apply = True

        # Log conflict
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_conflict_log
                (batch_id, resource_id, operation_type, incoming_timestamp, local_timestamp, resolution_strategy, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (batch_id, resource_id, operation_type, incoming_timestamp, local_timestamp, "lww", action))
            conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log conflict: {e}")

        return should_apply, f"LWW: {action} (incoming: {incoming_timestamp}, local: {local_timestamp})"

    def process_batch_sync(
        self,
        batch_request: 'BatchSyncRequest',
        verify_signature_func=None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a batch sync request with conflict resolution
        
        Args:
            batch_request: Batch sync request
            verify_signature_func: Optional function to verify signatures
            
        Returns:
            Tuple of (success: bool, response_dict: Dict)
        """
        batch_id = batch_request.batch_id
        node_id = batch_request.node_id
        payloads = batch_request.payloads
        conflict_strategy = batch_request.conflict_strategy

        results = []
        successful_count = 0
        conflict_count = 0
        failed_count = 0

        try:
            conn = self._get_connection()
            
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()

            for payload_item in payloads:
                result = {
                    "operation_type": payload_item.operation_type,
                    "resource_id": payload_item.resource_id,
                    "status": "unknown",
                    "conflict_detected": False,
                    "conflict_reason": None,
                    "local_timestamp": None,
                    "incoming_timestamp": payload_item.updated_at
                }

                try:
                    # Verify signature if provided and function available
                    if payload_item.signature and verify_signature_func:
                        try:
                            is_valid = verify_signature_func(
                                payload_item.data,
                                payload_item.signature
                            )
                            if not is_valid:
                                result["status"] = "failed"
                                result["conflict_reason"] = "Signature verification failed"
                                failed_count += 1
                                results.append(result)
                                continue
                        except Exception as sig_err:
                            logger.warning(f"Signature verification error: {sig_err}")

                    # Check for existing record by resource_id
                    existing_local_timestamp = None
                    if payload_item.resource_id:
                        # Query for existing record (example: assumes a generic data table)
                        # In a real implementation, this would query the actual resource table
                        # For now, we'll use a simplified approach
                        cursor.execute("""
                            SELECT payload FROM offline_sync_queue 
                            WHERE payload LIKE ? AND status = 'completed'
                            ORDER BY updated_at DESC LIMIT 1
                        """, (f'%"{payload_item.resource_id}"%',))
                        
                        existing_row = cursor.fetchone()
                        if existing_row:
                            try:
                                existing_payload = json.loads(existing_row[0])
                                existing_local_timestamp = self._extract_timestamp_from_payload(existing_payload)
                                result["local_timestamp"] = existing_local_timestamp
                            except json.JSONDecodeError:
                                pass

                    # Resolve conflicts if LWW strategy
                    should_apply = True
                    if existing_local_timestamp and conflict_strategy == "lww":
                        result["conflict_detected"] = True
                        should_apply, reason = self._resolve_lww_conflict(
                            payload_item.updated_at,
                            existing_local_timestamp,
                            batch_id,
                            payload_item.resource_id,
                            payload_item.operation_type
                        )
                        result["conflict_reason"] = reason
                        conflict_count += 1

                    # Record in queue if should apply
                    if should_apply:
                        queue_id = str(uuid.uuid4())
                        now = datetime.utcnow().isoformat()
                        
                        cursor.execute("""
                            INSERT INTO offline_sync_queue
                            (id, operation_type, payload, status, priority, created_at, updated_at, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            queue_id,
                            payload_item.operation_type,
                            json.dumps(payload_item.data),
                            "pending",
                            2,  # HIGH priority for batch items
                            now,
                            now,
                            json.dumps({"batch_id": batch_id, "node_id": node_id})
                        ))
                        result["status"] = "enqueued"
                        successful_count += 1
                    else:
                        # Mark as conflict resolved discarded
                        queue_id = str(uuid.uuid4())
                        now = datetime.utcnow().isoformat()
                        
                        cursor.execute("""
                            INSERT INTO offline_sync_queue
                            (id, operation_type, payload, status, priority, created_at, updated_at, 
                             conflict_resolution_status, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            queue_id,
                            payload_item.operation_type,
                            json.dumps(payload_item.data),
                            "conflict_resolved_discarded",
                            2,
                            now,
                            now,
                            "lww_discarded",
                            json.dumps({"batch_id": batch_id, "node_id": node_id})
                        ))
                        result["status"] = "conflict_discarded"

                except Exception as item_err:
                    logger.error(f"Error processing payload: {item_err}")
                    result["status"] = "failed"
                    result["conflict_reason"] = str(item_err)[:100]
                    failed_count += 1

                results.append(result)

            # Record batch history
            cursor.execute("""
                INSERT INTO sync_batch_history
                (batch_id, node_id, total_payloads, successful_payloads, 
                 conflict_payloads, failed_payloads, conflict_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (batch_id, node_id, len(payloads), successful_count, conflict_count, failed_count, conflict_strategy))

            # Commit transaction
            conn.commit()

            logger.info(
                f"Batch {batch_id} processed: {successful_count} successful, "
                f"{conflict_count} conflicts, {failed_count} failed"
            )

            return True, {
                "batch_id": batch_id,
                "node_id": node_id,
                "total_payloads": len(payloads),
                "successful": successful_count,
                "conflicts": conflict_count,
                "failed": failed_count,
                "results": results
            }

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            return False, {"error": str(e)[:200]}

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
                WHERE status IN ('completed', 'failed', 'conflict_resolved_discarded') 
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


# ============================================================================
# FastAPI Router for Batch Sync
# ============================================================================

router = APIRouter(
    prefix="/api/sync",
    tags=["CHIXUS Batch Sync"],
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Bad request"}
    }
)


async def verify_access_token_sync(x_access_token: Optional[str] = Header(None)) -> str:
    """Verify access token for sync endpoints"""
    if not x_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )
    return x_access_token


@router.post(
    "/batch",
    response_model=BatchSyncResponse,
    summary="Batch Sync with Conflict Resolution",
    description="Submit batch of sync payloads with Last-Write-Wins conflict resolution"
)
async def batch_sync(
    request: BatchSyncRequest,
    token: str = Depends(verify_access_token_sync),
    sync_engine: SyncEngine = Depends(get_sync_engine)
) -> BatchSyncResponse:
    """
    Process batch sync with LWW conflict resolution
    
    Requires X-Access-Token header.
    """
    success, result = sync_engine.process_batch_sync(request)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Batch processing failed")
        )

    return BatchSyncResponse(
        success=True,
        batch_id=result["batch_id"],
        node_id=result["node_id"],
        total_payloads=result["total_payloads"],
        processed_payloads=result["successful"] + result["conflicts"] + result["failed"],
        successful=result["successful"],
        conflicts=result["conflicts"],
        failed=result["failed"],
        results=[
            BatchSyncResult(
                operation_type=r["operation_type"],
                resource_id=r["resource_id"],
                status=r["status"],
                conflict_detected=r["conflict_detected"],
                conflict_reason=r["conflict_reason"],
                local_timestamp=r["local_timestamp"],
                incoming_timestamp=r["incoming_timestamp"]
            )
            for r in result["results"]
        ],
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/status")
async def get_sync_status(
    sync_engine: SyncEngine = Depends(get_sync_engine)
) -> Dict[str, Any]:
    """Get current sync queue status"""
    return sync_engine.get_queue_status()


__all__ = [
    "SyncEngine",
    "SyncStatus",
    "SyncPriority",
    "ConflictResolutionStrategy",
    "get_sync_engine",
    "router"
]
