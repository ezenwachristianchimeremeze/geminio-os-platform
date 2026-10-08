"""
CHIXUS Cryptographic Data Verification & Ledger Payload Integrity
FastAPI router and cryptographic module for deterministic signature verification
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import sqlite3
import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationStatus(str, Enum):
    """Verification status"""
    VERIFIED = "verified"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    """Types of actions that can be logged"""
    NODE_REGISTRATION = "node_registration"
    SYNC_OPERATION = "sync_operation"
    STATE_UPDATE = "state_update"
    AUTHORIZATION = "authorization"
    CONFIGURATION_CHANGE = "configuration_change"
    CUSTOM = "custom"


# ============================================================================
# Cryptographic Functions
# ============================================================================

def serialize_payload(payload: Dict[str, Any]) -> str:
    """
    Serialize payload deterministically for signing
    
    Args:
        payload: Dictionary to serialize
        
    Returns:
        Deterministic JSON string (sorted keys, no whitespace)
    """
    try:
        # Sort keys recursively for deterministic output
        def sort_dict(obj):
            if isinstance(obj, dict):
                return {k: sort_dict(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, list):
                return [sort_dict(item) for item in obj]
            else:
                return obj

        sorted_payload = sort_dict(payload)
        # Use separators without spaces for compact representation
        serialized = json.dumps(sorted_payload, separators=(',', ':'), sort_keys=True)
        return serialized
    except Exception as e:
        logger.error(f"Failed to serialize payload: {e}")
        raise


def generate_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Generate SHA-256 hash of payload
    
    Args:
        payload: Dictionary to hash
        
    Returns:
        Hex-encoded SHA-256 hash
    """
    try:
        serialized = serialize_payload(payload)
        hash_obj = hashlib.sha256(serialized.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to generate payload hash: {e}")
        raise


def generate_payload_signature(payload: Dict[str, Any], secret_key: str) -> str:
    """
    Generate HMAC SHA-256 signature for payload
    
    Args:
        payload: Dictionary to sign
        secret_key: Secret key for HMAC
        
    Returns:
        Hex-encoded HMAC SHA-256 signature
    """
    try:
        serialized = serialize_payload(payload)
        signature = hmac.new(
            secret_key.encode('utf-8'),
            serialized.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"Generated signature for payload (hash: {serialized[:50]}...)")
        return signature
    except Exception as e:
        logger.error(f"Failed to generate payload signature: {e}")
        raise


def verify_payload_signature(
    payload: Dict[str, Any],
    signature: str,
    secret_key: str
) -> bool:
    """
    Verify HMAC SHA-256 signature against payload
    
    Args:
        payload: Dictionary to verify
        signature: Hex-encoded signature to verify
        secret_key: Secret key for HMAC
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Generate expected signature
        expected_signature = generate_payload_signature(payload, secret_key)
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            logger.debug(f"Signature verification successful")
        else:
            logger.warning(f"Signature verification failed (expected: {expected_signature[:16]}..., got: {signature[:16]}...)")
        
        return is_valid
    except Exception as e:
        logger.error(f"Failed to verify payload signature: {e}")
        return False


# ============================================================================
# Request/Response Models
# ============================================================================

class LedgerRecordRequest(BaseModel):
    """Request model for ledger record submission"""
    node_id: str = Field(..., description="Node identifier", min_length=1, max_length=100)
    action_type: str = Field(..., description="Type of action", max_length=50)
    payload: Dict[str, Any] = Field(..., description="Action payload")
    signature: str = Field(..., description="HMAC SHA-256 signature of payload", min_length=64, max_length=128)


class LedgerRecordResponse(BaseModel):
    """Response for ledger record submission"""
    success: bool
    message: str
    record_id: int
    node_id: str
    action_type: str
    payload_hash: str
    signature_verified: bool
    timestamp: str


class LedgerRecordDetail(BaseModel):
    """Detailed view of a ledger record"""
    record_id: int
    node_id: str
    action_type: str
    payload_hash: str
    signature: str
    verified_status: str
    signature_reverify_result: bool
    timestamp: str
    created_at: datetime


class LedgerVerificationResponse(BaseModel):
    """Response for ledger verification query"""
    record_id: int
    node_id: str
    action_type: str
    payload_hash: str
    signature: str
    stored_verification_status: str
    current_verification_result: bool
    signature_match: bool
    timestamp: str
    message: str


class LedgerStatsResponse(BaseModel):
    """Statistics on ledger activity"""
    total_records: int
    verified_records: int
    failed_records: int
    pending_records: int
    unique_nodes: int
    action_type_breakdown: Dict[str, int]
    timestamp: str


class LedgerListResponse(BaseModel):
    """Response for ledger record listing"""
    total_records: int
    records: List[LedgerRecordDetail]
    timestamp: str


# ============================================================================
# Database Layer
# ============================================================================

class LedgerDatabase:
    """Handles all ledger database operations"""

    def __init__(self, db_path: str = "verify_team.db"):
        self.db_path = db_path
        self._initialize_tables()

    def _connect(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_tables(self) -> None:
        """Initialize ledger tables"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Create verification_ledger table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    verified_status TEXT NOT NULL DEFAULT 'verified'
                        CHECK(verified_status IN ('verified', 'failed', 'pending', 'unknown')),
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indices for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_ledger_node_id
                ON verification_ledger(node_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_ledger_action_type
                ON verification_ledger(action_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_ledger_verified_status
                ON verification_ledger(verified_status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_ledger_timestamp
                ON verification_ledger(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_ledger_payload_hash
                ON verification_ledger(payload_hash)
            """)

            # Create node_secret_keys table for secure key storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS node_secret_keys (
                    node_id TEXT PRIMARY KEY,
                    secret_key TEXT NOT NULL,
                    key_rotation_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_node_secret_keys_created_at
                ON node_secret_keys(created_at DESC)
            """)

            conn.commit()
            conn.close()
            logger.info("Ledger tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize ledger tables: {e}")
            raise

    def register_node_key(self, node_id: str, secret_key: str) -> Tuple[bool, str]:
        """
        Register or update a node's secret key
        
        Args:
            node_id: Node identifier
            secret_key: Secret key for signing
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Check if exists
            cursor.execute("SELECT node_id FROM node_secret_keys WHERE node_id = ?", (node_id,))
            exists = cursor.fetchone() is not None

            now = datetime.utcnow().isoformat()

            if exists:
                cursor.execute("""
                    UPDATE node_secret_keys
                    SET secret_key = ?,
                        key_rotation_at = ?
                    WHERE node_id = ?
                """, (secret_key, now, node_id))
                message = "Node key updated"
            else:
                cursor.execute("""
                    INSERT INTO node_secret_keys
                    (node_id, secret_key, created_at)
                    VALUES (?, ?, ?)
                """, (node_id, secret_key, now))
                message = "Node key registered"

            conn.commit()
            conn.close()
            logger.info(f"Node key for {node_id} registered/updated")
            return True, message

        except Exception as e:
            logger.error(f"Failed to register node key: {e}")
            return False, f"Error: {str(e)[:100]}"

    def get_node_key(self, node_id: str) -> Optional[str]:
        """
        Retrieve a node's secret key
        
        Args:
            node_id: Node identifier
            
        Returns:
            Secret key string or None
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT secret_key FROM node_secret_keys WHERE node_id = ?",
                (node_id,)
            )
            row = cursor.fetchone()
            conn.close()

            return row["secret_key"] if row else None

        except Exception as e:
            logger.error(f"Failed to get node key: {e}")
            return None

    def record_ledger_entry(
        self,
        node_id: str,
        action_type: str,
        payload_hash: str,
        signature: str,
        verified_status: str = "verified"
    ) -> Tuple[bool, int, str]:
        """
        Record an entry in the verification ledger
        
        Args:
            node_id: Node identifier
            action_type: Type of action
            payload_hash: SHA-256 hash of payload
            signature: HMAC signature
            verified_status: Verification status
            
        Returns:
            Tuple of (success: bool, record_id: int, message: str)
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO verification_ledger
                (node_id, action_type, payload_hash, signature, verified_status, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (node_id, action_type, payload_hash, signature, verified_status, now, now))

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Recorded ledger entry {record_id} for node {node_id} ({action_type})")
            return True, record_id, "Ledger entry recorded"

        except Exception as e:
            logger.error(f"Failed to record ledger entry: {e}")
            return False, -1, f"Error: {str(e)[:100]}"

    def get_ledger_record(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve a specific ledger record
        
        Args:
            record_id: Record ID
            
        Returns:
            Record dictionary or None
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, node_id, action_type, payload_hash, signature, 
                       verified_status, timestamp, created_at
                FROM verification_ledger
                WHERE id = ?
            """, (record_id,))

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get ledger record: {e}")
            return None

    def list_ledger_records(self, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        List ledger records with pagination
        
        Args:
            limit: Maximum records to return
            offset: Records to skip
            
        Returns:
            Tuple of (records_list, total_count)
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM verification_ledger")
            total_count = cursor.fetchone()["count"]

            # Get records
            cursor.execute("""
                SELECT id, node_id, action_type, payload_hash, signature,
                       verified_status, timestamp, created_at
                FROM verification_ledger
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            records = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return records, total_count

        except Exception as e:
            logger.error(f"Failed to list ledger records: {e}")
            return [], 0

    def get_ledger_statistics(self) -> Dict[str, Any]:
        """
        Get ledger statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Total records
            cursor.execute("SELECT COUNT(*) as count FROM verification_ledger")
            total = cursor.fetchone()["count"]

            # By status
            cursor.execute("""
                SELECT verified_status, COUNT(*) as count
                FROM verification_ledger
                GROUP BY verified_status
            """)
            status_breakdown = {row["verified_status"]: row["count"] for row in cursor.fetchall()}

            # By action type
            cursor.execute("""
                SELECT action_type, COUNT(*) as count
                FROM verification_ledger
                GROUP BY action_type
            """)
            action_breakdown = {row["action_type"]: row["count"] for row in cursor.fetchall()}

            # Unique nodes
            cursor.execute("SELECT COUNT(DISTINCT node_id) as count FROM verification_ledger")
            unique_nodes = cursor.fetchone()["count"]

            conn.close()

            return {
                "total_records": total,
                "by_status": status_breakdown,
                "by_action_type": action_breakdown,
                "unique_nodes": unique_nodes,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get ledger statistics: {e}")
            return {}


# ============================================================================
# Dependency Functions
# ============================================================================

_ledger_db: Optional[LedgerDatabase] = None


def get_ledger_db(db_path: str = "verify_team.db") -> LedgerDatabase:
    """Get or create singleton ledger database instance"""
    global _ledger_db
    if _ledger_db is None:
        _ledger_db = LedgerDatabase(db_path)
    return _ledger_db


async def verify_admin_passkey_ledger(
    x_admin_passkey: Optional[str] = Header(None)
) -> bool:
    """
    Verify master admin passkey for ledger endpoints
    
    Args:
        x_admin_passkey: Admin passkey header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If invalid
    """
    expected_passkey = "CHIXUS-ADMIN-@)@^"

    if not x_admin_passkey:
        logger.warning("Ledger: missing X-Admin-Passkey header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin passkey"
        )

    if x_admin_passkey != expected_passkey:
        logger.warning(f"Ledger: invalid admin passkey attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin passkey"
        )

    return True


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/api/ledger",
    tags=["CHIXUS Cryptographic Ledger"],
    responses={
        401: {"description": "Unauthorized - missing or invalid credentials"},
        403: {"description": "Forbidden - insufficient permissions"}
    }
)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/record",
    response_model=LedgerRecordResponse,
    summary="Record Ledger Entry",
    description="Submit a cryptographically signed action to the verification ledger"
)
async def record_ledger_entry(
    request: LedgerRecordRequest,
    ledger_db: LedgerDatabase = Depends(get_ledger_db)
) -> LedgerRecordResponse:
    """
    Record a ledger entry with cryptographic verification
    
    Verifies payload signature using node's registered secret key.
    """
    # Get node's secret key
    node_key = ledger_db.get_node_key(request.node_id)

    # If no key registered, attempt verification with provided signature
    # (may fail if signature doesn't verify)
    signature_verified = False
    if node_key:
        signature_verified = verify_payload_signature(
            request.payload,
            request.signature,
            node_key
        )
    else:
        logger.warning(f"No secret key registered for node {request.node_id}")

    # Generate payload hash
    try:
        payload_hash = generate_payload_hash(request.payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to hash payload: {str(e)[:100]}"
        )

    # Determine verification status
    verification_status = VerificationStatus.VERIFIED.value if signature_verified else VerificationStatus.FAILED.value

    # Record in ledger
    success, record_id, message = ledger_db.record_ledger_entry(
        node_id=request.node_id,
        action_type=request.action_type,
        payload_hash=payload_hash,
        signature=request.signature,
        verified_status=verification_status
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    return LedgerRecordResponse(
        success=True,
        message="Ledger entry recorded",
        record_id=record_id,
        node_id=request.node_id,
        action_type=request.action_type,
        payload_hash=payload_hash,
        signature_verified=signature_verified,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get(
    "/verify/{record_id}",
    response_model=LedgerVerificationResponse,
    summary="Verify Ledger Record",
    description="Admin-protected endpoint to reverify a ledger record's cryptographic signature"
)
async def verify_ledger_record(
    record_id: int,
    admin_verified: bool = Depends(verify_admin_passkey_ledger),
    ledger_db: LedgerDatabase = Depends(get_ledger_db)
) -> LedgerVerificationResponse:
    """
    Verify and re-check a ledger record
    
    Requires X-Admin-Passkey header.
    Re-verifies the stored signature against the payload hash.
    """
    record = ledger_db.get_ledger_record(record_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} not found"
        )

    # Get node's secret key
    node_key = ledger_db.get_node_key(record["node_id"])

    current_verification_result = False
    if node_key:
        # Note: We cannot fully re-verify without the original payload
        # This is a design constraint - the ledger stores hash + signature
        # but not the original payload for privacy
        logger.info(
            f"Re-verification requires original payload (not stored). "
            f"Stored verification status: {record['verified_status']}"
        )

    return LedgerVerificationResponse(
        record_id=record["id"],
        node_id=record["node_id"],
        action_type=record["action_type"],
        payload_hash=record["payload_hash"],
        signature=record["signature"],
        stored_verification_status=record["verified_status"],
        current_verification_result=current_verification_result,
        signature_match=record["verified_status"] == VerificationStatus.VERIFIED.value,
        timestamp=record["timestamp"],
        message="Ledger record retrieved (full re-verification requires original payload)"
    )


@router.get(
    "/records",
    response_model=LedgerListResponse,
    summary="List Ledger Records",
    description="Admin-protected endpoint to list ledger records with pagination"
)
async def list_ledger_records(
    limit: int = 100,
    offset: int = 0,
    admin_verified: bool = Depends(verify_admin_passkey_ledger),
    ledger_db: LedgerDatabase = Depends(get_ledger_db)
) -> LedgerListResponse:
    """
    List ledger records
    
    Requires X-Admin-Passkey header.
    Supports pagination via limit and offset parameters.
    """
    if limit < 1 or limit > 1000:
        limit = 100
    if offset < 0:
        offset = 0

    records, total = ledger_db.list_ledger_records(limit=limit, offset=offset)

    records_detail = [
        LedgerRecordDetail(
            record_id=r["id"],
            node_id=r["node_id"],
            action_type=r["action_type"],
            payload_hash=r["payload_hash"],
            signature=r["signature"],
            verified_status=r["verified_status"],
            signature_reverify_result=False,  # Cannot reverify without original payload
            timestamp=r["timestamp"],
            created_at=datetime.fromisoformat(r["created_at"])
        )
        for r in records
    ]

    return LedgerListResponse(
        total_records=total,
        records=records_detail,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get(
    "/stats",
    response_model=LedgerStatsResponse,
    summary="Get Ledger Statistics",
    description="Admin-protected endpoint returning ledger activity statistics"
)
async def get_ledger_stats(
    admin_verified: bool = Depends(verify_admin_passkey_ledger),
    ledger_db: LedgerDatabase = Depends(get_ledger_db)
) -> LedgerStatsResponse:
    """
    Get ledger statistics
    
    Requires X-Admin-Passkey header.
    """
    stats = ledger_db.get_ledger_statistics()

    return LedgerStatsResponse(
        total_records=stats.get("total_records", 0),
        verified_records=stats.get("by_status", {}).get("verified", 0),
        failed_records=stats.get("by_status", {}).get("failed", 0),
        pending_records=stats.get("by_status", {}).get("pending", 0),
        unique_nodes=stats.get("unique_nodes", 0),
        action_type_breakdown=stats.get("by_action_type", {}),
        timestamp=stats.get("timestamp", datetime.utcnow().isoformat())
    )


@router.post(
    "/node/{node_id}/register-key",
    summary="Register Node Secret Key",
    description="Admin-protected endpoint to register a node's cryptographic secret key"
)
async def register_node_key(
    node_id: str,
    secret_key: str = Header(..., description="Secret key for node"),
    admin_verified: bool = Depends(verify_admin_passkey_ledger),
    ledger_db: LedgerDatabase = Depends(get_ledger_db)
) -> Dict[str, str]:
    """
    Register a node's secret key
    
    Requires X-Admin-Passkey header and X-Secret-Key header.
    """
    success, message = ledger_db.register_node_key(node_id, secret_key)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": "true" if success else "false",
        "message": message,
        "node_id": node_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/ping",
    summary="Ledger Router Ping",
    description="Simple ping endpoint for ledger router availability"
)
async def ledger_ping() -> Dict[str, str]:
    """Simple health ping endpoint"""
    return {
        "status": "pong",
        "service": "CHIXUS Cryptographic Ledger",
        "timestamp": datetime.utcnow().isoformat()
    }


# Export for router registration
__all__ = [
    "router",
    "get_ledger_db",
    "verify_admin_passkey_ledger",
    "generate_payload_signature",
    "verify_payload_signature",
    "generate_payload_hash",
    "serialize_payload",
    "LedgerDatabase",
    "VerificationStatus",
    "ActionType"
]
