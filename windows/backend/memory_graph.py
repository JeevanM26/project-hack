import time
import uuid
from typing import Dict, List, Any, Optional


class NeuralMemoryGraph:
    """Tracks live Memory Nodes, Agent Nodes, and Active Task Synapses for the UI Memory Graph Tab."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.activity_log: List[Dict[str, Any]] = []
        self._init_core_topology()

    def _init_core_topology(self) -> None:
        core_agents = [
            ("agent_coleader", "Co-Leader & Planner", "agent", "Idle — awaiting user command"),
            ("agent_os_operator", "OS App & GUI Operator", "agent", "Idle — ready to launch apps & move mouse"),
            ("agent_dir_auditor", "Directory & AST Auditor", "agent", "Idle — ready to scan folders & find bugs"),
            ("agent_coder", "Autonomous Code Builder", "agent", "Idle — ready to write & test code"),
            ("agent_researcher", "Deep Web Researcher", "agent", "Idle — ready to search & scrape docs"),
        ]
        for nid, label, ntype, task in core_agents:
            self.nodes[nid] = {
                "id": nid,
                "label": label,
                "type": ntype,
                "status": "idle",
                "current_task": task,
                "updated_at": time.time(),
            }
            if nid != "agent_coleader":
                self.add_edge("agent_coleader", nid, "orchestrates")

        core_memories = [
            ("mem_episodic", "Episodic Session Memory", "memory", "Stores conversation & command history"),
            ("mem_workspace", "Directory & File AST Memory", "memory", "Stores scanned local files & syntax trees"),
            ("mem_research", "Web & Documentation Memory", "memory", "Stores scraped web pages & API schemas"),
            ("mem_system", "Windows OS & App State", "memory", "Stores running processes & active windows"),
        ]
        for mid, label, mtype, desc in core_memories:
            self.nodes[mid] = {
                "id": mid,
                "label": label,
                "type": mtype,
                "status": "ready",
                "current_task": desc,
                "data_preview": "",
                "updated_at": time.time(),
            }

        self.add_edge("agent_coleader", "mem_episodic", "reads/writes")
        self.add_edge("agent_dir_auditor", "mem_workspace", "indexes AST")
        self.add_edge("agent_coder", "mem_workspace", "reads/writes files")
        self.add_edge("agent_researcher", "mem_research", "stores findings")
        self.add_edge("agent_os_operator", "mem_system", "controls OS")

    def add_edge(self, source: str, target: str, relation: str, active: bool = False) -> None:
        for edge in self.edges:
            if edge["source"] == source and edge["target"] == target:
                edge["relation"] = relation
                edge["active"] = active
                edge["timestamp"] = time.time()
                return
        self.edges.append({
            "id": f"{source}->{target}",
            "source": source,
            "target": target,
            "relation": relation,
            "active": active,
            "timestamp": time.time(),
        })

    def set_agent_task(self, agent_id: str, status: str, task_description: str, target_memory_id: Optional[str] = None) -> None:
        if agent_id in self.nodes:
            self.nodes[agent_id]["status"] = status
            self.nodes[agent_id]["current_task"] = task_description
            self.nodes[agent_id]["updated_at"] = time.time()
        for e in self.edges:
            if e["source"] == agent_id or e["target"] == agent_id:
                e["active"] = (status == "working")
        if target_memory_id and target_memory_id in self.nodes:
            self.add_edge(agent_id, target_memory_id, status, active=(status == "working"))

    def spawn_sub_agent_node(self, parent_id: str, name: str, task: str, target_memory_id: str = "mem_workspace") -> str:
        sub_id = f"sub_{uuid.uuid4().hex[:6]}"
        self.nodes[sub_id] = {
            "id": sub_id,
            "label": name,
            "type": "sub_agent",
            "status": "working",
            "current_task": task,
            "updated_at": time.time(),
        }
        self.add_edge(parent_id, sub_id, "spawned", active=True)
        self.add_edge(sub_id, target_memory_id, "operates on", active=True)
        return sub_id

    def upsert_memory_fact(self, memory_id: str, title: str, preview: str, connected_agent: str) -> str:
        fact_id = f"fact_{uuid.uuid4().hex[:6]}"
        self.nodes[fact_id] = {
            "id": fact_id,
            "label": title[:38],
            "type": "memory_artifact",
            "status": "stored",
            "current_task": preview[:160],
            "updated_at": time.time(),
        }
        self.add_edge(memory_id, fact_id, "contains", active=True)
        self.add_edge(connected_agent, fact_id, "wrote", active=True)
        return fact_id

    def snapshot(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "timestamp": time.time(),
        }
