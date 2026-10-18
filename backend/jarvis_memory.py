"""
J.A.R.V.I.S. Cognitive Memory & Companion Brain Engine
Persistent SQLite-backed open-source memory system.
Maintains:
- Episodic Memory: full log of instructions, agent thoughts, actions, and outcomes.
- Working Context: current task, active tools, and real-time state.
- Companion Knowledge: user identity (Jeevan / Sir), preferences, hardware profile.
- Task Agenda: active, pending, and completed multi-step goals.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jarvis.memory")
DB_PATH = Path(__file__).parent / "jarvis_brain.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db() -> None:
    """Initializes the persistent cognitive brain tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS episodic_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        epoch_time REAL,
        user_prompt TEXT NOT NULL,
        agent_thought TEXT,
        action_name TEXT,
        tool_used TEXT,
        outcome_summary TEXT,
        metadata_json TEXT
    );

    CREATE TABLE IF NOT EXISTS working_context (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at REAL
    );

    CREATE TABLE IF NOT EXISTS companion_knowledge (
        key TEXT PRIMARY KEY,
        value TEXT,
        category TEXT,
        updated_at REAL
    );

    CREATE TABLE IF NOT EXISTS task_agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_description TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, in_progress, completed
        created_at REAL,
        completed_at REAL
    );
    """)

    # Populate default companion identity if empty
    cursor.execute("SELECT COUNT(*) FROM companion_knowledge")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("user_name", "Jeevan", "identity"),
            ("user_title", "Sir", "identity"),
            ("ai_persona", "J.A.R.V.I.S. Mark VII (Just A Rather Very Intelligent System)", "identity"),
            ("preferred_ide", "Antigravity IDE", "tools"),
            ("primary_browser", "Google Chrome & Microsoft Edge", "tools"),
            ("3d_suite", "Blender 5.2.2", "tools"),
            ("hardware_profile", "NVIDIA GeForce RTX 5060 Ti • Windows 11 64-bit", "system"),
            ("neural_engine", "Local Gemma 4 (Ollama) & Moondream Vision", "ai"),
        ]
        cursor.executemany(
            "INSERT INTO companion_knowledge (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
            [(k, v, cat, time.time()) for k, v, cat in defaults],
        )

    # Initialize working context defaults
    cursor.execute("INSERT OR IGNORE INTO working_context (key, value, updated_at) VALUES ('current_task', 'Standing by on default desktop', ?)", (time.time(),))
    cursor.execute("INSERT OR IGNORE INTO working_context (key, value, updated_at) VALUES ('active_workspace', 'e:\\New folder', ?)", (time.time(),))
    cursor.execute("INSERT OR IGNORE INTO working_context (key, value, updated_at) VALUES ('vision_status', 'Optical and desktop vision armed', ?)", (time.time(),))

    conn.commit()
    conn.close()


def record_episodic_memory(
    user_prompt: str,
    agent_thought: str = "",
    action_name: str = "",
    tool_used: str = "",
    outcome_summary: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """Stores a cognitive memory entry in the episodic database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    cursor.execute(
        """
        INSERT INTO episodic_memory (epoch_time, user_prompt, agent_thought, action_name, tool_used, outcome_summary, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (now, user_prompt, agent_thought, action_name, tool_used, outcome_summary, json.dumps(metadata or {})),
    )
    mem_id = cursor.lastrowid or 0
    # Update current task
    cursor.execute("REPLACE INTO working_context (key, value, updated_at) VALUES ('current_task', ?, ?)", (f"Completed: {user_prompt[:80]}", now))
    conn.commit()
    conn.close()
    return mem_id


def set_working_context(key: str, value: str) -> None:
    """Updates a working memory variable."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO working_context (key, value, updated_at) VALUES (?, ?, ?)", (key, value, time.time()))
    conn.commit()
    conn.close()


def get_working_context() -> Dict[str, str]:
    """Retrieves all active working context variables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM working_context")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def get_recent_episodes(limit: int = 8) -> List[Dict[str, Any]]:
    """Retrieves recent memories of tasks completed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, timestamp, user_prompt, agent_thought, action_name, tool_used, outcome_summary
        FROM episodic_memory
        ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_companion_profile() -> Dict[str, str]:
    """Retrieves J.A.R.V.I.S. identity and knowledge about the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM companion_knowledge")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def query_memory(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Searches memory for past instructions and tasks matching keywords."""
    conn = get_db_connection()
    cursor = conn.cursor()
    wildcard = f"%{query_text.strip()}%"
    cursor.execute(
        """
        SELECT id, timestamp, user_prompt, outcome_summary, action_name, tool_used
        FROM episodic_memory
        WHERE user_prompt LIKE ? OR outcome_summary LIKE ? OR agent_thought LIKE ?
        ORDER BY id DESC LIMIT ?
        """,
        (wildcard, wildcard, wildcard, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cognitive_brain_summary() -> Dict[str, Any]:
    """Provides a complete snapshot of J.A.R.V.I.S.'s internal mind, memory, and awareness."""
    init_memory_db()
    return {
        "identity": get_companion_profile(),
        "working_context": get_working_context(),
        "recent_tasks": get_recent_episodes(6),
        "total_memories_stored": len(get_recent_episodes(100)),
        "status": "Cognitive Memory Core Online",
    }


# Auto-initialize DB on module import
init_memory_db()
