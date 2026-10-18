"""
J.A.R.V.I.S. 4-Tier Cognitive Memory Brain (SQLite Engine)
Persistent Open-Source Memory System:
1. What I Am (Identity & Core Engines)
2. Doing Right Now (Working Memory & Thought Trace)
3. Tasks I Did (Episodic Memory of Completed Actions)
4. What I Have To Do (Prospective Goal Queue & User Added Goals)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jarvis.memory")
DB_PATH = Path(__file__).parent / "jarvis_brain.db"


class JarvisCognitiveBrain:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.current_activity: Dict[str, Any] = {
            "status": "IDLE_MONITORING",
            "task": "Monitoring voice, laptop camera, Windows UIA desktop tree & companion memory",
            "started_at": time.strftime("%H:%M:%S"),
            "last_thought": "All 4 cognitive memory tiers online and synchronized.",
        }
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS self_identity (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS todo_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    priority TEXT DEFAULT 'HIGH',
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    thought TEXT DEFAULT '',
                    timestamp TEXT NOT NULL
                );
                -- Backward compatibility tables
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
                """
            )
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            defaults = {
                "name": "J.A.R.V.I.S. (Just A Rather Very Intelligent System) Mark VII",
                "nature": "Autonomous Multimodal AI Companion & Local OS Executive Brain",
                "core_engines": "Gemma 4 27B Vision (Ollama) + AirLLM + Windows UI Automation (UIA) + Win32 Media Controller + Antigravity IDE Bridge + SQLite Memory",
                "mission": "Think alongside the user as a real companion, remember every completed task and future goal, perceive screen and camera visually, and control all OS apps and media playback.",
            }
            for k, v in defaults.items():
                conn.execute("INSERT OR IGNORE INTO self_identity VALUES (?, ?, ?)", (k, v, now))

            if conn.execute("SELECT COUNT(*) FROM todo_goals").fetchone()[0] == 0:
                default_goals = [
                    "Monitor open desktop windows via Windows UIA to prevent duplicate app instances",
                    "Dispatch full-stack coding tasks directly into Antigravity IDE Composer (Ctrl+I)",
                    "Maintain zero-latency hardware and software media playback control",
                    "Ensure dynamic autonomous resource downloads without hardcoded routing"
                ]
                for g in default_goals:
                    conn.execute("INSERT INTO todo_goals (goal, priority, status, created_at) VALUES (?, 'HIGH', 'PENDING', ?)", (g, now))

            conn.commit()

    def set_doing_now(self, task: str, status: str = "EXECUTING", thought: str = "") -> None:
        self.current_activity = {
            "status": status,
            "task": task,
            "started_at": time.strftime("%H:%M:%S"),
            "last_thought": thought or self.current_activity.get("last_thought", ""),
        }

    def record_completed_task(self, category: str, instruction: str, outcome: str) -> None:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO completed_tasks (category, instruction, outcome, timestamp) VALUES (?, ?, ?, ?)",
                (category, instruction[:300], outcome[:500], now),
            )
            # Auto-complete pending matching goals
            inst_words = set(re.findall(r"[a-z0-9]{3,}", instruction.lower()))
            for row in conn.execute("SELECT id, goal FROM todo_goals WHERE status = 'PENDING'").fetchall():
                goal_words = set(re.findall(r"[a-z0-9]{3,}", row["goal"].lower()))
                if goal_words and len(inst_words & goal_words) >= max(2, min(3, len(goal_words))):
                    conn.execute("UPDATE todo_goals SET status = 'DONE', completed_at = ? WHERE id = ?", (now, row["id"]))
            conn.commit()
        self.set_doing_now(f"Completed: {outcome[:90]}", "IDLE_MONITORING", f"Logged '{instruction[:60]}' in episodic memory.")

    def add_todo_goal(self, goal: str, priority: str = "HIGH") -> Dict[str, Any]:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO todo_goals (goal, priority, status, created_at) VALUES (?, ?, 'PENDING', ?)", (goal.strip(), priority.upper(), now))
            conn.commit()
            return {"id": cur.lastrowid, "goal": goal.strip(), "priority": priority.upper(), "status": "PENDING"}

    def update_todo_status(self, goal_id: int, status: str = "DONE") -> None:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute("UPDATE todo_goals SET status = ?, completed_at = ? WHERE id = ?", (status.upper(), now if status.upper() == "DONE" else "", goal_id))
            conn.commit()

    def update_identity_fact(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO self_identity VALUES (?, ?, ?)", (key.strip(), value.strip(), time.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def record_turn(self, role: str, content: str, thought: str = "") -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO conversation_memory (role, content, thought, timestamp) VALUES (?, ?, ?, ?)", (role, content[:1000], thought[:600], time.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def snapshot(self, uia_windows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        with self._connect() as conn:
            what_it_is = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM self_identity").fetchall()}
            what_it_did = [dict(r) for r in conn.execute("SELECT id, category, instruction, outcome, timestamp FROM completed_tasks ORDER BY id DESC LIMIT 15").fetchall()]
            what_it_has_to_do = [dict(r) for r in conn.execute("SELECT id, goal, priority, status, created_at, completed_at FROM todo_goals ORDER BY CASE status WHEN 'PENDING' THEN 0 ELSE 1 END, id DESC LIMIT 15").fetchall()]
            recent_dialogue = list(reversed([dict(r) for r in conn.execute("SELECT role, content, thought, timestamp FROM conversation_memory ORDER BY id DESC LIMIT 8").fetchall()]))

        return {
            "what_it_is": what_it_is,
            "what_it_did": what_it_did,
            "what_it_is_doing": {
                **self.current_activity,
                "live_uia_windows": [w.get("title", "") for w in (uia_windows or []) if w.get("title")][:12],
            },
            "what_it_has_to_do": what_it_has_to_do,
            "recent_dialogue": recent_dialogue,
        }


BRAIN = JarvisCognitiveBrain()


# -------------------------------------------------------------
# Backward Compatibility Wrappers
# -------------------------------------------------------------
def record_episodic_memory(
    user_prompt: str,
    agent_thought: str = "",
    action_name: str = "",
    tool_used: str = "",
    outcome_summary: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    category = tool_used or action_name or "general_task"
    BRAIN.record_completed_task(category, user_prompt, outcome_summary or action_name)
    BRAIN.record_turn("user", user_prompt)
    if outcome_summary or agent_thought:
        BRAIN.record_turn("assistant", outcome_summary, agent_thought)
    return 1


def get_cognitive_brain_summary() -> Dict[str, Any]:
    snap = BRAIN.snapshot()
    return {
        "user_profile": {"name": "Jeevan", "title": "Sir"},
        "companion_status": snap["what_it_is"],
        "working_context": {"current_task": snap["what_it_is_doing"]["task"], "last_thought": snap["what_it_is_doing"].get("last_thought", "")},
        "recent_tasks": [
            {
                "tool_used": d["category"],
                "action_name": d["category"],
                "user_prompt": d["instruction"],
                "outcome_summary": d["outcome"],
                "timestamp": d["timestamp"]
            }
            for d in snap["what_it_did"]
        ],
        "task_agenda": snap["what_it_has_to_do"],
        "full_snapshot": snap
    }


def query_memory(search_term: str, limit: int = 5) -> List[Dict[str, Any]]:
    with BRAIN._connect() as conn:
        q = f"%{search_term.lower()}%"
        rows = conn.execute(
            """
            SELECT id, category, instruction, outcome, timestamp
            FROM completed_tasks
            WHERE LOWER(instruction) LIKE ? OR LOWER(outcome) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY id DESC LIMIT ?
            """,
            (q, q, q, limit),
        ).fetchall()
        return [dict(r) for r in rows]
