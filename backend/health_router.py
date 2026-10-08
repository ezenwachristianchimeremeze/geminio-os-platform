"""
CHIXUS Node Health Monitoring & Heartbeat Service
FastAPI router for distributed edge node health tracking and status monitoring
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Node operational status"""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class HeartbeatStatus(str, Enum):
    """Heartbeat tracking status"""
    ACTIVE = "active"
    STALE = "stale"
    DEAD = "dead"


# ============================================================================
# Request/Response Models
# ============================================================================

class SystemMetadata(BaseModel):
    """System information metadata"""
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    disk_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    uptime_seconds: Optional[int] = Field(None, ge=0)
    network_latency_ms: Optional[float] = Field(None, ge=0)
    sync_queue_size: Optional[int] = Field(None, ge=0)
    custom_fields: Optional[Dict[str, Any]] = None


class HeartbeatRequest(BaseModel):
    """Request model for node heartbeat"""
    node_id: str = Field(..., description="Unique node identifier", min_length=1, max_length=100)
    status: str = Field(
        default="online",
        description="Node status",
        pattern="^(online|degraded)$"
    )
    pending_sync_count: int = Field(
        default=0,
        description="Number of pending sync operations",
        ge=0
    )
    metadata: Optional[SystemMetadata] = Field(
        None,
        description="System health metadata"
    )


class NodeHeartbeatRecord(BaseModel):
    """Response model for node heartbeat record"""
    node_id: str
    status: str
    heartbeat_status: str
    pending_sync_count: int
    last_seen: str
    seconds_since_heartbeat: int
    is_offline: bool
    metadata: Optional[Dict[str, Any]] = None


class HeartbeatResponse(BaseModel):
    """Response for heartbeat submission"""
    success: bool
    message: str
    node_id: str
    status: str
    last_seen: str
    next_heartbeat_in_seconds: int = 30


class NodeHealthSummary(BaseModel):
    """Summary of a node's health"""
    node_id: str
    status: str
    heartbeat_status: str
    is_online: bool
    is_degraded: bool
    is_offline: bool
    pending_sync_count: int
    last_seen: str
    seconds_since_heartbeat: int
    metadata: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Response for cluster health check"""
    timestamp: str
    total_nodes: int
    online_nodes: int
    degraded_nodes: int
    offline_nodes: int
    summary: List[NodeHealthSummary]


class HeartbeatStatsResponse(BaseModel):
    """Statistics on heartbeat activity"""
    total_heartbeats: int
    unique_nodes: int
    last_24h_heartbeats: int
    nodes_with_activity: List[str]


# ============================================================================
# Database Layer
# ============================================================================

class NodeHealthDatabase:
    """Handles all node health database operations"""

    def __init__(self, db_path: str = "verify_team.db"):
        self.db_path = db_path
        self.heartbeat_timeout_minutes = 5  # Nodes offline after 5 min inactivity
        self._initialize_tables()

    def _connect(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_tables(self) -> None:
        """Initialize node health tables"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Create node_heartbeats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS node_heartbeats (
                    node_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'online' 
                        CHECK(status IN ('online', 'degraded', 'offline', 'unknown')),
                    pending_sync_count INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    heartbeat_count INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Create heartbeat_history table for analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pending_sync_count INTEGER NOT NULL,
                    metadata TEXT,
                    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (node_id) REFERENCES node_heartbeats(node_id)
                )
            """)

            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_node_heartbeats_status
                ON node_heartbeats(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_node_heartbeats_last_seen
                ON node_heartbeats(last_seen DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_heartbeat_history_node_id
                ON heartbeat_history(node_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_heartbeat_history_recorded_at
                ON heartbeat_history(recorded_at DESC)
            """)

            conn.commit()
            conn.close()
            logger.info("Node health tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize health tables: {e}")
            raise

    def upsert_heartbeat(
        self,
        node_id: str,
        status: str = "online",
        pending_sync_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Upsert a node heartbeat (insert or update)
        
        Args:
            node_id: Unique node identifier
            status: Node status (online, degraded)
            pending_sync_count: Number of pending sync operations
            metadata: Optional system metadata
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()

            # Check if node exists
            cursor.execute("SELECT node_id FROM node_heartbeats WHERE node_id = ?", (node_id,))
            exists = cursor.fetchone() is not None

            metadata_json = json.dumps(metadata) if metadata else None

            if exists:
                # Update existing
                cursor.execute("""
                    UPDATE node_heartbeats
                    SET status = ?,
                        pending_sync_count = ?,
                        last_seen = ?,
                        last_heartbeat_at = ?,
                        metadata = ?,
                        heartbeat_count = heartbeat_count + 1
                    WHERE node_id = ?
                """, (status, pending_sync_count, now, now, metadata_json, node_id))
                
                message = "Heartbeat updated"
                logger.info(f"Updated heartbeat for node {node_id} (status: {status})")
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO node_heartbeats
                    (node_id, status, pending_sync_count, last_seen, last_heartbeat_at, metadata, created_at, heartbeat_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (node_id, status, pending_sync_count, now, now, metadata_json, now, 1))
                
                message = "Node registered"
                logger.info(f"Registered new node {node_id} (status: {status})")

            # Log to history
            cursor.execute("""
                INSERT INTO heartbeat_history
                (node_id, status, pending_sync_count, metadata, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            """, (node_id, status, pending_sync_count, metadata_json, now))

            conn.commit()
            conn.close()
            return True, message

        except Exception as e:
            logger.error(f"Failed to upsert heartbeat for {node_id}: {e}")
            return False, f"Error: {str(e)[:100]}"

    def get_node_status(self, node_id: str) -> Optional[Dict]:
        """
        Get current status of a specific node
        
        Args:
            node_id: Node identifier
            
        Returns:
            Node record dictionary or None
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT node_id, status, pending_sync_count, last_seen, 
                       last_heartbeat_at, metadata, heartbeat_count, created_at
                FROM node_heartbeats
                WHERE node_id = ?
            """, (node_id,))

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            return None

    def _calculate_heartbeat_status(self, last_seen_iso: str) -> str:
        """Calculate heartbeat status based on last_seen time"""
        try:
            last_seen = datetime.fromisoformat(last_seen_iso)
            now = datetime.utcnow()
            delta = now - last_seen
            
            if delta.total_seconds() > (self.heartbeat_timeout_minutes * 60):
                return HeartbeatStatus.DEAD.value
            elif delta.total_seconds() > 120:  # 2 minutes
                return HeartbeatStatus.STALE.value
            else:
                return HeartbeatStatus.ACTIVE.value
        except Exception:
            return HeartbeatStatus.UNKNOWN.value

    def get_all_nodes(self) -> List[Dict]:
        """
        Get all registered nodes with calculated status
        
        Returns:
            List of node records
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT node_id, status, pending_sync_count, last_seen, 
                       last_heartbeat_at, metadata, heartbeat_count, created_at
                FROM node_heartbeats
                ORDER BY last_seen DESC
            """)

            nodes = []
            now = datetime.utcnow()

            for row in cursor.fetchall():
                node_dict = dict(row)
                last_seen = datetime.fromisoformat(node_dict["last_seen"])
                seconds_delta = int((now - last_seen).total_seconds())
                
                # Determine if offline
                is_offline = seconds_delta > (self.heartbeat_timeout_minutes * 60)
                
                # Calculate heartbeat status
                heartbeat_status = self._calculate_heartbeat_status(node_dict["last_seen"])
                
                node_dict["seconds_since_heartbeat"] = seconds_delta
                node_dict["is_offline"] = is_offline
                node_dict["heartbeat_status"] = heartbeat_status
                
                # Parse metadata if present
                if node_dict.get("metadata"):
                    try:
                        node_dict["metadata"] = json.loads(node_dict["metadata"])
                    except json.JSONDecodeError:
                        node_dict["metadata"] = None
                
                nodes.append(node_dict)

            conn.close()
            return nodes

        except Exception as e:
            logger.error(f"Failed to get all nodes: {e}")
            return []

    def get_cluster_health_summary(self) -> Dict[str, Any]:
        """
        Get overall cluster health summary
        
        Returns:
            Cluster health statistics
        """
        try:
            nodes = self.get_all_nodes()
            now = datetime.utcnow()
            
            online_count = 0
            degraded_count = 0
            offline_count = 0
            
            for node in nodes:
                if node["is_offline"]:
                    offline_count += 1
                elif node["status"] == NodeStatus.DEGRADED.value:
                    degraded_count += 1
                else:
                    online_count += 1
            
            return {
                "total_nodes": len(nodes),
                "online_nodes": online_count,
                "degraded_nodes": degraded_count,
                "offline_nodes": offline_count,
                "timestamp": now.isoformat(),
                "nodes": nodes
            }

        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            return {
                "error": str(e),
                "total_nodes": 0,
                "online_nodes": 0,
                "degraded_nodes": 0,
                "offline_nodes": 0,
                "nodes": []
            }

    def get_heartbeat_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get heartbeat statistics for time period
        
        Args:
            hours: Look-back period in hours
            
        Returns:
            Heartbeat statistics
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            # Total heartbeats in period
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM heartbeat_history
                WHERE recorded_at > ?
            """, (cutoff_time,))
            total_heartbeats = cursor.fetchone()["total"]

            # Unique nodes
            cursor.execute("""
                SELECT COUNT(DISTINCT node_id) as count
                FROM heartbeat_history
                WHERE recorded_at > ?
            """, (cutoff_time,))
            unique_nodes = cursor.fetchone()["count"]

            # Nodes with recent activity
            cursor.execute("""
                SELECT DISTINCT node_id
                FROM heartbeat_history
                WHERE recorded_at > ?
                ORDER BY node_id
            """, (cutoff_time,))
            active_nodes = [row["node_id"] for row in cursor.fetchall()]

            conn.close()

            return {
                "period_hours": hours,
                "cutoff_time": cutoff_time,
                "total_heartbeats": total_heartbeats,
                "unique_nodes": unique_nodes,
                "active_nodes": active_nodes,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get heartbeat stats: {e}")
            return {"error": str(e)}


# ============================================================================
# Dependency Functions
# ============================================================================

from typing import Tuple

# Global health database instance
_health_db: Optional[NodeHealthDatabase] = None


def get_health_db(db_path: str = "verify_team.db") -> NodeHealthDatabase:
    """Get or create singleton health database instance"""
    global _health_db
    if _health_db is None:
        _health_db = NodeHealthDatabase(db_path)
    return _health_db


async def verify_admin_passkey_health(
    x_admin_passkey: Optional[str] = Header(None)
) -> bool:
    """
    Verify master admin passkey for health endpoints
    
    Args:
        x_admin_passkey: Admin passkey header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If invalid
    """
    expected_passkey = "CHIXUS-ADMIN-@)@^"
    
    if not x_admin_passkey:
        logger.warning("Health check: missing X-Admin-Passkey header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin passkey"
        )
    
    if x_admin_passkey != expected_passkey:
        logger.warning(f"Health check: invalid admin passkey attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin passkey"
        )
    
    return True


async def verify_access_token_heartbeat(
    x_access_token: Optional[str] = Header(None)
) -> str:
    """
    Verify access token for heartbeat submission
    
    Args:
        x_access_token: Access token from header
        
    Returns:
        The token if valid
        
    Raises:
        HTTPException: If invalid
    """
    if not x_access_token:
        logger.warning("Heartbeat: missing X-Access-Token header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Import here to avoid circular dependency
    try:
        from backend.auth_router import get_token_db
        token_db = get_token_db()
        
        # Check if revoked
        if token_db.is_token_revoked(x_access_token):
            logger.warning(f"Heartbeat: revoked token attempt")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has been revoked"
            )
        
        # Verify token exists
        token_record = token_db.get_token(x_access_token)
        if not token_record:
            logger.warning(f"Heartbeat: invalid token attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return x_access_token
    
    except ImportError:
        logger.warning("Auth router not available, allowing heartbeat")
        return x_access_token


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/api/node",
    tags=["CHIXUS Node Health Monitoring"],
    responses={
        401: {"description": "Unauthorized - missing or invalid credentials"},
        403: {"description": "Forbidden - insufficient permissions"}
    }
)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    summary="Submit Node Heartbeat",
    description="Authenticated endpoint for edge nodes to report their health status"
)
async def submit_heartbeat(
    request: HeartbeatRequest,
    token: str = Depends(verify_access_token_heartbeat),
    health_db: NodeHealthDatabase = Depends(get_health_db)
) -> HeartbeatResponse:
    """
    Submit a heartbeat for a node
    
    Requires X-Access-Token header with valid token.
    Performs UPSERT on node_heartbeats table.
    """
    success, message = health_db.upsert_heartbeat(
        node_id=request.node_id,
        status=request.status,
        pending_sync_count=request.pending_sync_count,
        metadata=request.metadata.dict() if request.metadata else None
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    node_record = health_db.get_node_status(request.node_id)

    return HeartbeatResponse(
        success=True,
        message=message,
        node_id=request.node_id,
        status=request.status,
        last_seen=node_record["last_seen"] if node_record else datetime.utcnow().isoformat(),
        next_heartbeat_in_seconds=30
    )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Get Cluster Health Status",
    description="Admin-protected endpoint returning all registered nodes and their health status"
)
async def get_cluster_health(
    admin_verified: bool = Depends(verify_admin_passkey_health),
    health_db: NodeHealthDatabase = Depends(get_health_db)
) -> HealthCheckResponse:
    """
    Get cluster health summary
    
    Requires X-Admin-Passkey header with master passkey value.
    Returns status of all nodes, calculating offline status based on last_seen > 5 minutes.
    """
    summary_data = health_db.get_cluster_health_summary()

    # Build detailed summary
    nodes_summary = []
    for node in summary_data["nodes"]:
        nodes_summary.append(NodeHealthSummary(
            node_id=node["node_id"],
            status=node["status"],
            heartbeat_status=node["heartbeat_status"],
            is_online=node["status"] == NodeStatus.ONLINE.value and not node["is_offline"],
            is_degraded=node["status"] == NodeStatus.DEGRADED.value and not node["is_offline"],
            is_offline=node["is_offline"],
            pending_sync_count=node["pending_sync_count"],
            last_seen=node["last_seen"],
            seconds_since_heartbeat=node["seconds_since_heartbeat"],
            metadata=node.get("metadata")
        ))

    return HealthCheckResponse(
        timestamp=summary_data["timestamp"],
        total_nodes=summary_data["total_nodes"],
        online_nodes=summary_data["online_nodes"],
        degraded_nodes=summary_data["degraded_nodes"],
        offline_nodes=summary_data["offline_nodes"],
        summary=nodes_summary
    )


@router.get(
    "/health/stats",
    response_model=HeartbeatStatsResponse,
    summary="Get Heartbeat Statistics",
    description="Admin-protected endpoint returning heartbeat statistics"
)
async def get_heartbeat_stats(
    hours: int = 24,
    admin_verified: bool = Depends(verify_admin_passkey_health),
    health_db: NodeHealthDatabase = Depends(get_health_db)
) -> HeartbeatStatsResponse:
    """
    Get heartbeat statistics for the specified period
    
    Requires X-Admin-Passkey header with master passkey value.
    """
    stats = health_db.get_heartbeat_statistics(hours=hours)

    return HeartbeatStatsResponse(
        total_heartbeats=stats.get("total_heartbeats", 0),
        unique_nodes=stats.get("unique_nodes", 0),
        last_24h_heartbeats=stats.get("total_heartbeats", 0),
        nodes_with_activity=stats.get("active_nodes", [])
    )


@router.get(
    "/health/{node_id}",
    summary="Get Specific Node Health",
    description="Get detailed health information for a specific node"
)
async def get_node_health(
    node_id: str,
    admin_verified: bool = Depends(verify_admin_passkey_health),
    health_db: NodeHealthDatabase = Depends(get_health_db)
) -> NodeHeartbeatRecord:
    """
    Get health status of a specific node
    
    Requires X-Admin-Passkey header with master passkey value.
    """
    node = health_db.get_node_status(node_id)

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found"
        )

    now = datetime.utcnow()
    last_seen = datetime.fromisoformat(node["last_seen"])
    seconds_delta = int((now - last_seen).total_seconds())
    is_offline = seconds_delta > (5 * 60)  # 5 minutes
    heartbeat_status = health_db._calculate_heartbeat_status(node["last_seen"])

    metadata = None
    if node.get("metadata"):
        try:
            metadata = json.loads(node["metadata"])
        except json.JSONDecodeError:
            metadata = None

    return NodeHeartbeatRecord(
        node_id=node["node_id"],
        status=node["status"],
        heartbeat_status=heartbeat_status,
        pending_sync_count=node["pending_sync_count"],
        last_seen=node["last_seen"],
        seconds_since_heartbeat=seconds_delta,
        is_offline=is_offline,
        metadata=metadata
    )


@router.get(
    "/ping",
    summary="Health Router Ping",
    description="Simple ping endpoint for health router availability"
)
async def health_ping() -> Dict[str, str]:
    """Simple health ping endpoint"""
    return {
        "status": "pong",
        "service": "CHIXUS Node Health Monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }


# Export for router registration
__all__ = [
    "router",
    "get_health_db",
    "verify_admin_passkey_health",
    "verify_access_token_heartbeat",
    "NodeHealthDatabase",
    "NodeStatus",
    "HeartbeatStatus"
]
