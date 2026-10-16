"""
Shared Global Project Blackboard for J.A.R.V.I.S. Swarm.
Thread-safe, observable, real-time shared state accessible by all autonomous agents
(Co-Leader, Deep Researcher, System Architect, Workspace Builder, QA Critic, and Sub-Agents).
"""
import copy
import datetime
import threading
from typing import Dict, Any, List, Optional, Callable


class SharedBlackboard:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(SharedBlackboard, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.lock = threading.RLock()
        self.listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.reset_state()
        self._initialized = True

    def reset_state(self, mission_id: str = "mission-init", user_objective: str = ""):
        with self.lock:
            self.mission_id = mission_id
            self.user_objective = user_objective
            self.status = "IDLE"  # IDLE, PLANNING, RESEARCHING, CODING, EXECUTING, TESTING, HEALING, COMPLETED, FAILED
            self.research_notes: List[Dict[str, Any]] = []
            self.architecture_blueprint: Dict[str, Any] = {
                "system_summary": "",
                "components": [],
                "files_to_create": [],
                "entrypoint": "",
                "run_command": "",
                "test_command": "",
            }
            self.active_agents: Dict[str, Dict[str, Any]] = {
                "Co-Leader": {"role": "Co-Leader & Chief Reviewer", "status": "STANDBY", "current_task": "Idle", "last_active": self._now()},
                "Researcher": {"role": "Autonomous Deep Researcher & Web Crawler", "status": "STANDBY", "current_task": "Idle", "last_active": self._now()},
                "Architect": {"role": "System Architect & AST Grounding Engineer", "status": "STANDBY", "current_task": "Idle", "last_active": self._now()},
                "Builder": {"role": "Full-Stack Workspace Builder & Terminal Operator", "status": "STANDBY", "current_task": "Idle", "last_active": self._now()},
                "Critic": {"role": "Zero-Hallucination QA & Self-Healing Critic", "status": "STANDBY", "current_task": "Idle", "last_active": self._now()},
            }
            self.workspace_path: str = ""
            self.workspace_files: Dict[str, Dict[str, Any]] = {}
            self.ast_symbol_registry: Dict[str, Dict[str, Any]] = {}
            self.browser_and_os_state: Dict[str, Any] = {
                "active_browser_url": "",
                "open_windows": [],
                "last_clicked_element": "",
                "mouse_position": [0, 0],
                "active_app": "desktop",
            }
            self.terminal_logs: List[Dict[str, Any]] = []
            self.team_chat_bus: List[Dict[str, Any]] = []
            self.last_update_ts = self._now()

    def _now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]):
        with self.lock:
            if callback not in self.listeners:
                self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]):
        with self.lock:
            if callback in self.listeners:
                self.listeners.remove(callback)

    def _notify(self, event_type: str, payload: Any = None):
        snapshot = self.get_snapshot()
        for listener in list(self.listeners):
            try:
                listener({"event": event_type, "payload": payload, "blackboard": snapshot})
            except Exception:
                pass

    def update_status(self, new_status: str, objective: Optional[str] = None):
        with self.lock:
            self.status = new_status
            if objective is not None:
                self.user_objective = objective
            self.last_update_ts = self._now()
        self._notify("status_updated", {"status": new_status, "objective": objective})

    def update_agent(self, agent_name: str, status: str, current_task: str):
        with self.lock:
            if agent_name not in self.active_agents:
                self.active_agents[agent_name] = {"role": "Child Sub-Agent", "status": status, "current_task": current_task, "last_active": self._now()}
            else:
                self.active_agents[agent_name]["status"] = status
                self.active_agents[agent_name]["current_task"] = current_task
                self.active_agents[agent_name]["last_active"] = self._now()
            self.last_update_ts = self._now()
        self._notify("agent_updated", {"agent": agent_name, "status": status, "current_task": current_task})

    def post_chat_message(self, from_agent: str, to_agent: str, message: str, kind: str = "chat"):
        msg = {
            "timestamp": self._now(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message,
            "kind": kind,
        }
        with self.lock:
            self.team_chat_bus.append(msg)
            # keep max 500 messages
            if len(self.team_chat_bus) > 500:
                self.team_chat_bus = self.team_chat_bus[-500:]
            self.last_update_ts = self._now()
        self._notify("chat_message", msg)

    def add_research_note(self, url: str, title: str, summary: str, key_takeaways: Optional[List[str]] = None):
        note = {
            "timestamp": self._now(),
            "url": url,
            "title": title,
            "summary": summary,
            "key_takeaways": key_takeaways or [],
        }
        with self.lock:
            self.research_notes.append(note)
            self.last_update_ts = self._now()
        self._notify("research_note_added", note)

    def set_architecture_blueprint(self, blueprint: Dict[str, Any]):
        with self.lock:
            self.architecture_blueprint.update(blueprint)
            self.last_update_ts = self._now()
        self._notify("blueprint_updated", blueprint)

    def register_workspace_file(self, rel_path: str, content: str, language: str = "python"):
        file_info = {
            "language": language,
            "content": content,
            "size": len(content.encode("utf-8")),
            "last_modified": self._now(),
        }
        with self.lock:
            self.workspace_files[rel_path] = file_info
            self.last_update_ts = self._now()
        self._notify("workspace_file_saved", {"path": rel_path, "size": file_info["size"]})

    def register_ast_symbols(self, rel_path: str, symbols: Dict[str, Any]):
        with self.lock:
            self.ast_symbol_registry[rel_path] = symbols
            self.last_update_ts = self._now()
        self._notify("ast_symbols_updated", {"path": rel_path, "symbols": symbols})

    def update_browser_and_os(self, **kwargs):
        with self.lock:
            self.browser_and_os_state.update(kwargs)
            self.last_update_ts = self._now()
        self._notify("browser_os_updated", kwargs)

    def update_mouse_position(self, x: int, y: int):
        with self.lock:
            self.browser_and_os_state["mouse_position"] = [x, y]
            self.last_update_ts = self._now()
        # High-frequency: notify lightly or throttle in telemetry loop

    def append_terminal_log(self, command: str, stdout: str, stderr: str, exit_code: int):
        entry = {
            "timestamp": self._now(),
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }
        with self.lock:
            self.terminal_logs.append(entry)
            if len(self.terminal_logs) > 300:
                self.terminal_logs = self.terminal_logs[-300:]
            self.last_update_ts = self._now()
        self._notify("terminal_log_appended", entry)

    def get_snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "mission_id": self.mission_id,
                "user_objective": self.user_objective,
                "status": self.status,
                "research_notes": list(self.research_notes),
                "architecture_blueprint": copy.deepcopy(self.architecture_blueprint),
                "active_agents": copy.deepcopy(self.active_agents),
                "workspace_path": self.workspace_path,
                "workspace_files": {k: {"language": v["language"], "size": v["size"], "last_modified": v["last_modified"], "content": v.get("content", "")} for k, v in self.workspace_files.items()},
                "ast_symbol_registry": copy.deepcopy(self.ast_symbol_registry),
                "browser_and_os_state": copy.deepcopy(self.browser_and_os_state),
                "terminal_logs": list(self.terminal_logs),
                "team_chat_bus": list(self.team_chat_bus[-50:]),
                "last_update_ts": self.last_update_ts,
            }


global_blackboard = SharedBlackboard()
