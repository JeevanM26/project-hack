"""
J.A.R.V.I.S. Mark VII - Active Task Manager & Protocol Zero Subsystem
Manages live background tasks, process termination, hardware muting, and HUD synchronization.
"""

import os
import time
import threading
from typing import Dict, Any, List, Optional
import psutil

try:
    from backend.computer_use import stop_all_media_playback
except ImportError:
    try:
        from computer_use import stop_all_media_playback
    except ImportError:
        stop_all_media_playback = None

try:
    from backend.jarvis_memory import BRAIN
except ImportError:
    try:
        from jarvis_memory import BRAIN
    except ImportError:
        BRAIN = None


class JarvisTaskManager:
    """Thread-safe registry for all ongoing tasks and child processes."""

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, Dict[str, Any]] = {}
        # Initialize default core tasks
        self._init_core_tasks()

    def _init_core_tasks(self):
        core_pid = os.getpid()
        self._tasks["task_core_observer"] = {
            "task_id": "task_core_observer",
            "name": "Gemma 4 Cognitive Engine & UIA Desktop Observer",
            "category": "neural",
            "status": "RUNNING",
            "started_at": time.strftime("%H:%M:%S"),
            "pid": core_pid,
            "can_terminate": False,
            "details": "Live multimodal perception & companion reasoning",
        }

    def register_task(
        self,
        name: str,
        category: str = "general",
        pid: Optional[int] = None,
        details: Optional[str] = None,
        can_terminate: bool = True
    ) -> str:
        """Register a new active task and return its unique ID."""
        task_id = f"task_{category}_{int(time.time() * 1000) % 1000000}"
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "name": name,
                "category": category,
                "status": "RUNNING",
                "started_at": time.strftime("%H:%M:%S"),
                "start_timestamp": time.time(),
                "pid": pid,
                "can_terminate": can_terminate,
                "details": details or "",
            }
        return task_id

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Return list of all currently running tasks, pruning dead PIDs."""
        now = time.time()
        active = []
        with self._lock:
            for task_id, task in list(self._tasks.items()):
                # Check if PID is still alive if specified
                pid = task.get("pid")
                if pid and task.get("can_terminate") and task.get("category") == "shell":
                    if not psutil.pid_exists(pid):
                        task["status"] = "COMPLETED"
                        continue

                if task.get("status") == "RUNNING":
                    # Calculate elapsed seconds
                    start_ts = task.get("start_timestamp", now)
                    task["elapsed_sec"] = int(now - start_ts)
                    active.append(dict(task))
        return active

    def terminate_task(self, task_id: str) -> Dict[str, Any]:
        """Terminate a specific task by its ID."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return {"ok": False, "error": f"Task '{task_id}' not found."}

            if not task.get("can_terminate", True):
                return {"ok": False, "error": f"Task '{task.get('name')}' is a protected core system component."}

            name = task.get("name", task_id)
            category = task.get("category", "")
            pid = task.get("pid")

        # 1. Kill process by PID if applicable
        killed_proc = False
        if pid and psutil.pid_exists(pid) and pid != os.getpid():
            try:
                proc = psutil.Process(pid)
                # Terminate children first
                for child in proc.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                proc.kill()
                killed_proc = True
            except Exception:
                pass

        # 2. Stop audio/media if category is media
        if category == "media" and stop_all_media_playback:
            try:
                stop_all_media_playback()
            except Exception:
                pass

        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "TERMINATED"
                self._tasks[task_id]["terminated_at"] = time.strftime("%H:%M:%S")

        # 3. Log to Cognitive Brain
        outcome = f"Terminated {name} (PID: {pid or 'N/A'}) on user instruction"
        if BRAIN:
            try:
                BRAIN.record_completed_task("task_termination", f"Terminate {name}", outcome)
                BRAIN.set_doing_now("Idle & Monitoring", f"Task {name} was successfully terminated.")
            except Exception:
                pass

        return {
            "ok": True,
            "task_id": task_id,
            "name": name,
            "category": category,
            "killed_process": killed_proc,
            "message": f"Terminated '{name}' successfully, sir.",
            "active_tasks": self.get_active_tasks(),
            "brain": BRAIN.snapshot() if BRAIN else {}
        }

    def terminate_all_tasks(self) -> Dict[str, Any]:
        """PROTOCOL ZERO: Terminate all non-core background tasks, mute all media, and kill child processes."""
        terminated_tasks = []
        with self._lock:
            to_kill = [t for t in self._tasks.values() if t.get("status") == "RUNNING" and t.get("can_terminate")]

        for t in to_kill:
            self.terminate_task(t["task_id"])
            terminated_tasks.append(t.get("name"))

        # Extra safety: Mute all background audio sessions
        if stop_all_media_playback:
            try:
                stop_all_media_playback()
            except Exception:
                pass

        if BRAIN:
            try:
                BRAIN.record_completed_task(
                    "protocol_zero",
                    "Engage Protocol Zero / Terminate All",
                    f"Emergency killswitch terminated {len(terminated_tasks)} tasks."
                )
                BRAIN.set_doing_now("Idle / All Tasks Cleared", "Protocol Zero completed successfully.")
            except Exception:
                pass

        return {
            "ok": True,
            "action": "protocol_zero",
            "terminated_count": len(terminated_tasks),
            "terminated_names": terminated_tasks,
            "message": f"Protocol Zero executed, sir. {len(terminated_tasks)} operations terminated.",
            "active_tasks": self.get_active_tasks(),
            "brain": BRAIN.snapshot() if BRAIN else {}
        }


# Global Singleton Instance
TASK_MANAGER = JarvisTaskManager()
