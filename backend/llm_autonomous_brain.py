import json
import os
import re
import sys
import requests
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS

from memory_graph import NeuralMemoryGraph
from os_and_dir_tools import (
    open_system_app_or_url,
    inspect_directory_and_find_mistakes,
    write_file_to_disk,
    run_terminal_command,
)
from computer_use_agent import execute_computer_use, safe_eval_math


class JarvisAutonomousBrain:
    """Connects 1 Single Gemma / Local Ollama / Gemini Model to Real OS, Directory, Code & Web Tools."""

    def __init__(self, memory_graph: NeuralMemoryGraph) -> None:
        self.graph = memory_graph
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.preferred_model = os.getenv("JARVIS_GEMMA_MODEL", "")
        self.conversation_history: List[Dict[str, str]] = []

    def detect_live_model(self) -> Dict[str, Any]:
        """Auto-detects installed Ollama models so we never fail on a fake hardcoded model name."""
        try:
            r = requests.get(f"{self.ollama_base}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if models:
                    chosen = self.preferred_model if self.preferred_model in models else models[0]
                    for m in models:
                        if "gemma" in m.lower():
                            chosen = m
                            break
                    return {"provider": "ollama", "connected": True, "active_model": chosen, "available_models": models}
        except Exception:
            pass

        if self.gemini_api_key:
            return {"provider": "gemini", "connected": True, "active_model": "gemini-2.5-flash", "available_models": ["gemini-2.5-flash", "gemma-4-26b-a4b-it"]}

        return {"provider": "none", "connected": False, "active_model": "disconnected", "available_models": []}

    def call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        status = self.detect_live_model()
        if status["provider"] == "ollama":
            payload: Dict[str, Any] = {
                "model": status["active_model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            }
            if json_mode:
                payload["format"] = "json"
            r = requests.post(f"{self.ollama_base}/api/chat", json=payload, timeout=90)
            r.raise_for_status()
            return r.json()["message"]["content"]

        if status["provider"] == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{status['active_model']}:generateContent?key={self.gemini_api_key}"
            body: Dict[str, Any] = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.2},
            }
            if json_mode:
                body["generationConfig"]["responseMimeType"] = "application/json"
            r = requests.post(url, json=body, timeout=60)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]

        raise RuntimeError(
            "No live LLM detected! Start Ollama (`ollama serve` & `ollama pull gemma3:4b` or `gemma4:e4b`) "
            "or set GEMINI_API_KEY in the UI config modal."
        )

    def execute_user_instruction(self, instruction: str, target_directory: str = ".") -> Dict[str, Any]:
        """Executes real OS tools, directory bug audits, code generation, and web research with zero canned dialogues."""
        self.graph.set_agent_task("agent_coleader", "working", f"Analyzing command: {instruction[:60]}", "mem_episodic")
        tool_traces: List[Dict[str, Any]] = []
        created_or_fixed_files: Dict[str, str] = {}

        planner_system = """You are the J.A.R.V.I.S. Co-Leader & Autonomous Tool Router (Antigravity + Open-Interpreter style).
Analyze the user's request and output a JSON object specifying which real tools to execute right now:
{
  "intent_summary": "short description",
  "spawn_sub_agents": [{"name": "Sub-Agent Name", "task": "Specific task"}],
  "actions": [
    {"tool": "open_app_or_url", "target": "app name or URL (only if user asked to open an app/site)"},
    {"tool": "inspect_directory", "path": "directory path to scan for files/mistakes"},
    {"tool": "web_search", "query": "search query if external research is needed"},
    {"tool": "write_or_fix_code", "directory": "target folder", "task": "what code to write or what bugs to fix"},
    {"tool": "run_command", "command": "shell/python/pytest command to verify", "cwd": "target folder"}
  ]
}
Only include the actions actually needed for the user's prompt. Output valid JSON only."""

        plan_raw = self.call_llm(
            planner_system,
            f"User Command: {instruction}\nDefault Working Directory: {target_directory}",
            json_mode=True,
        )
        try:
            cleaned_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", plan_raw.strip(), flags=re.MULTILINE)
            plan = json.loads(cleaned_json)
            if isinstance(plan, list):
                plan = {"actions": plan}
        except Exception:
            plan = {"intent_summary": instruction, "spawn_sub_agents": [], "actions": []}

        # Intent fallback & compound intent check
        cmd_lower = instruction.lower()
        has_inspect = any(w in cmd_lower for w in ["directory", "folder", "mistake", "error", "bug", "inspect", "audit", "scan"])
        has_open = any(w in cmd_lower for w in ["open ", "launch ", "start "])
        has_code = any(w in cmd_lower for w in ["write code", "fix code", "write a", "code for", "create code", "implement", "fix it", "fix them", "fix this", "fix the", "and fix", "write python", "python code", "write a python"])

        # Detect calculate/compute requests: "calculate 5*6", "open calculator and compute", "what is 5+6"
        has_calculate = any(w in cmd_lower for w in ["calculat", "compute", "what is", "how much", "evaluate", "solve", "find the result", "result of"])
        # Extract math expression — greedy match allowing spaces around operators
        calc_expression = None
        math_match = re.search(
            r'(?:calculate|compute|evaluate|solve|find the result of|what is|result of|how much is)[:\s]+([0-9][0-9\s\+\-\*/\.\(\)\^×÷%]*)',
            instruction, re.I
        )
        if not math_match:
            math_match = re.search(r'(\d[\d\s\+\-\*/\.\(\)\^×÷%]+\d)', instruction)
        if math_match:
            calc_expression = math_match.group(1).strip()

        # Check existing VALID tool names (normalize: tool key takes priority over type key)
        existing_tools = {str(act.get("tool", "")).lower() for act in plan.get("actions", [])}

        # FORCE-INJECT real tool actions based on what the user actually said.
        # Small LLMs often return bogus type:"math"/"output" instead of tool:"calculate" — we fix that here.
        if has_open and not any("open" in t or "launch" in t or "start" in t for t in existing_tools):
            m = re.search(r'(?:open|launch|start)\s+(?:the\s+)?([a-zA-Z0-9_\-\.\s]+)', cmd_lower)
            target = m.group(1).strip() if m else "notepad"
            if " and " in target:
                target = target.split(" and ", 1)[0].strip()
            plan.setdefault("actions", []).append({"tool": "open_app_or_url", "target": target})

        # Always force a calculate action when user says "calculate ..." with an expression,
        # regardless of what the LLM planner emitted (it may emit type:"math" which we'd miss)
        if has_calculate and calc_expression:
            # Remove any bogus math/output/type actions the model put in
            plan["actions"] = [
                a for a in plan.get("actions", [])
                if str(a.get("tool", a.get("type", ""))).lower() not in ("math", "output", "compute", "calculate")
            ]
            plan.setdefault("actions", []).append({"tool": "calculate", "expression": calc_expression})

        if has_inspect and "inspect_directory" not in existing_tools and not any("inspect" in t or "audit" in t for t in existing_tools):
            plan.setdefault("actions", []).append({"tool": "inspect_directory", "path": target_directory})
        if has_code and not any("write" in t or "fix" in t for t in existing_tools):
            plan.setdefault("actions", []).append({"tool": "write_or_fix_code", "directory": target_directory, "task": instruction})


        # Spawn dynamic sub-agents in the Neural Memory Graph
        for sa in plan.get("spawn_sub_agents", []):
            self.graph.spawn_sub_agent_node("agent_coleader", sa.get("name", "Specialist Sub-Agent"), sa.get("task", ""))

        directory_context = None

        for act in plan.get("actions", []):
            raw_tool = str(act.get("tool", "")).lower().replace("-", "_").strip()

            # Normalize tool name
            if raw_tool in ("calculate", "compute", "evaluate", "math") or any(k in raw_tool for k in ["calculat", "comput", "evaluat"]):
                tname = "calculate"
            elif raw_tool.startswith("open") or raw_tool.startswith("launch") or raw_tool.startswith("start"):
                tname = "open_app_or_url"
                if not act.get("target"):
                    if "_" in raw_tool and raw_tool not in {"open_app", "open_app_or_url", "open_application"}:
                        act["target"] = raw_tool.split("_", 1)[1]
                    else:
                        m = re.search(r'(?:open|launch|start)\s+(?:the\s+)?([a-zA-Z0-9_\-\.\s]+)', instruction, re.I)
                        act["target"] = m.group(1).strip() if m else "notepad"
            elif any(k in raw_tool for k in ["inspect", "audit", "scan", "directory", "mistake", "file"]):
                tname = "inspect_directory"
            elif any(k in raw_tool for k in ["search", "web", "ddg", "google"]):
                tname = "web_search"
            elif any(k in raw_tool for k in ["write", "code", "fix", "create", "generate"]):
                tname = "write_or_fix_code"
            elif any(k in raw_tool for k in ["command", "terminal", "run", "shell", "exec"]):
                tname = "run_command"
            else:
                tname = raw_tool

            if tname == "calculate":
                expr = act.get("expression") or calc_expression or "0"
                self.graph.set_agent_task("agent_os_operator", "working", f"Computing: {expr}", "mem_system")
                calc_res = execute_computer_use({"type": "calculate", "expression": expr})
                tool_traces.append({"tool": "calculate", "input": expr, "result": calc_res})
                self.graph.set_agent_task("agent_os_operator", "idle", f"Result: {calc_res.get('result')}")

            elif tname == "open_app_or_url":
                target = act.get("target", "")
                self.graph.set_agent_task("agent_os_operator", "working", f"Launching: {target}", "mem_system")
                res = open_system_app_or_url(target)
                tool_traces.append({"tool": "open_system_app_or_url", "input": target, "result": res})
                self.graph.upsert_memory_fact("mem_system", f"App: {target}", json.dumps(res), "agent_os_operator")
                self.graph.set_agent_task("agent_os_operator", "idle", f"Completed launch: {target}")

            elif tname == "inspect_directory":
                dpath = act.get("path") or target_directory
                if os.path.isfile(dpath) or any(dpath.endswith(ext) for ext in [".py", ".js", ".ts", ".html", ".css", ".json"]):
                    dpath = os.path.dirname(dpath) or target_directory or "."
                if not os.path.isdir(dpath):
                    dpath = target_directory if os.path.isdir(target_directory) else "."
                self.graph.set_agent_task("agent_dir_auditor", "working", f"Scanning {dpath} for mistakes", "mem_workspace")
                res = inspect_directory_and_find_mistakes(dpath)
                directory_context = res
                tool_traces.append({
                    "tool": "inspect_directory_and_find_mistakes",
                    "input": dpath,
                    "result": {
                        "ok": res.get("ok"),
                        "directory": res.get("directory"),
                        "file_count": res.get("file_count"),
                        "detected_mistakes": res.get("detected_mistakes"),
                        "pytest_output": res.get("pytest_output"),
                    },
                })
                self.graph.upsert_memory_fact(
                    "mem_workspace",
                    f"Scanned {res.get('file_count', 0)} files",
                    f"Mistakes found: {len(res.get('detected_mistakes', []))}",
                    "agent_dir_auditor",
                )
                self.graph.set_agent_task("agent_dir_auditor", "idle", f"Audited {res.get('file_count', 0)} files")

            elif tname == "web_search":
                q = act.get("query", instruction)
                self.graph.set_agent_task("agent_researcher", "working", f"Searching web: {q}", "mem_research")
                hits = []
                try:
                    with DDGS() as ddgs:
                        for r in ddgs.text(q, max_results=5):
                            hits.append({"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")})
                except Exception as e:
                    hits.append({"error": str(e)})
                tool_traces.append({"tool": "web_search", "input": q, "result": hits})
                self.graph.upsert_memory_fact("mem_research", f"Search: {q[:24]}", json.dumps(hits)[:160], "agent_researcher")
                self.graph.set_agent_task("agent_researcher", "idle", f"Retrieved {len(hits)} web sources")

            elif tname == "write_or_fix_code":
                work_dir = act.get("directory") or target_directory
                if os.path.isfile(work_dir) or any(work_dir.endswith(ext) for ext in [".py", ".js", ".ts", ".json", ".html"]):
                    work_dir = os.path.dirname(work_dir) or target_directory or "."
                if not os.path.isdir(work_dir):
                    work_dir = target_directory if os.path.isdir(target_directory) else "."

                if not directory_context:
                    directory_context = inspect_directory_and_find_mistakes(work_dir)
                self.graph.set_agent_task("agent_coder", "working", f"Writing/fixing code in {work_dir}", "mem_workspace")

                coder_system = (
                    "You are the J.A.R.V.I.S. Autonomous Principal Software Engineer. "
                    "Write complete, robust, runnable code or bug fixes for the user's request. "
                    "Format your response with the code in a markdown code block, with the target filename on line 1:\n"
                    "```python\n"
                    "# filename: filename.py\n"
                    "# complete runnable code here\n"
                    "```\n"
                    "Include sample test calls at the bottom if testing was requested."
                )
                mistakes = directory_context.get('detected_mistakes', []) if directory_context else []
                coder_prompt_parts = [
                    f"User Instruction: {instruction}",
                    f"Target Directory: {work_dir}",
                ]
                if mistakes:
                    coder_prompt_parts.append(f"Detected Mistakes To Fix:\n{json.dumps(mistakes, indent=2)}")
                    mistake_files = {m.get('file') for m in mistakes if m.get('file')}
                    relevant_files = [f for f in directory_context.get('files', []) if f.get('relative_path') in mistake_files]
                    if relevant_files:
                        coder_prompt_parts.append(f"Problematic File Contents:\n{json.dumps(relevant_files, indent=2)}")
                coder_prompt = "\n\n".join(coder_prompt_parts)

                coder_raw = self.call_llm(coder_system, coder_prompt, json_mode=False)

                coder_json = {"files_to_write": []}
                # 1. Try parsing as JSON first if the model responded with JSON
                try:
                    cleaned_coder = re.sub(r"^```(?:json)?\s*|\s*```$", "", coder_raw.strip(), flags=re.MULTILINE)
                    parsed_json = json.loads(cleaned_coder)
                    if isinstance(parsed_json, dict) and "files_to_write" in parsed_json:
                        coder_json = parsed_json
                except Exception:
                    pass

                # 2. Extract code block from markdown or raw text
                if not coder_json.get("files_to_write"):
                    code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', coder_raw, re.DOTALL)
                    if code_match:
                        code_content = code_match.group(1).strip()
                    elif "```" in coder_raw:
                        code_content = coder_raw.split("```")[0].strip()
                    else:
                        code_content = coder_raw.strip()

                    # Find filename from code comment or user instruction
                    fn_match = re.search(r'#\s*(?:filename|file):\s*([a-zA-Z0-9_\-\.]+)', coder_raw, re.IGNORECASE)
                    if fn_match:
                        rpath = fn_match.group(1).strip()
                    else:
                        instr_fn = re.search(r'([a-zA-Z0-9_\-]+\.py)', instruction)
                        rpath = instr_fn.group(1) if instr_fn else "solution.py"

                    if len(code_content) > 10:
                        coder_json["files_to_write"] = [{"relative_path": rpath, "content": code_content}]

                successful_writes = 0
                for fobj in coder_json.get("files_to_write", []):
                    rpath = fobj.get("relative_path")
                    fcontent = fobj.get("content", "")
                    if rpath and fcontent:
                        wres = write_file_to_disk(work_dir, rpath, fcontent)
                        tool_traces.append({"tool": "write_file_to_disk", "input": rpath, "result": wres})
                        if wres.get("ok"):
                            successful_writes += 1
                            created_or_fixed_files[rpath] = fcontent
                            self.graph.upsert_memory_fact("mem_workspace", f"Wrote {rpath}", f"{len(fcontent)} bytes", "agent_coder")

                # Verification run — always run with the actual file that was written to disk
                vcmd = coder_json.get("verification_command", "")
                # Normalize python3 → python on Windows
                if sys.platform == "win32":
                    vcmd = re.sub(r'^python3\b', 'python', vcmd)
                # Override with actual written filename if model gave wrong/generic command
                if successful_writes > 0:
                    actual_file = list(created_or_fixed_files.keys())[0]
                    # Always prefer running the actual file that was written
                    if not vcmd or vcmd.startswith("shell/") or vcmd.startswith("python/") or "or " in vcmd:
                        # Auto-run if the user asked to write AND run, or for verification
                        if any(w in instruction.lower() for w in ["run", "test", "verify", "check", "execute", "write and run", "and run"]):
                            vcmd = f"python {actual_file}"
                        else:
                            vcmd = ""  # Don't auto-run if user only asked to write
                    elif re.match(r'python\s+\S+\.py', vcmd):
                        # Model specified a .py file to run — use the actual written file instead
                        vcmd = f"python {actual_file}"


                if vcmd and successful_writes > 0:
                    self.graph.set_agent_task("agent_coder", "working", f"Verifying: {vcmd}", "mem_workspace")
                    cmd_res = run_terminal_command(vcmd, cwd=work_dir)
                    tool_traces.append({"tool": "run_terminal_command", "input": vcmd, "result": cmd_res})

                self.graph.set_agent_task("agent_coder", "idle", f"Wrote {len(created_or_fixed_files)} files")


            elif tname == "run_command":
                cmd = act.get("command", "")
                cwd = act.get("cwd") or target_directory
                if os.path.isfile(cwd) or any(cwd.endswith(ext) for ext in [".py", ".js", ".ts"]):
                    cwd = os.path.dirname(cwd) or target_directory or "."
                if not os.path.isdir(cwd):
                    cwd = "."

                if not cmd or cmd.startswith("shell/"):
                    if created_or_fixed_files:
                        cmd = f"python {list(created_or_fixed_files.keys())[0]}"
                    else:
                        cmd = ""

                if cmd and created_or_fixed_files:
                    if " or " in cmd:
                        cmd = cmd.split(" or ")[0].strip()
                    self.graph.set_agent_task("agent_coder", "working", f"Running: {cmd}", "mem_workspace")
                    cmd_res = run_terminal_command(cmd, cwd=cwd)
                    tool_traces.append({"tool": "run_terminal_command", "input": cmd, "result": cmd_res})
                    self.graph.set_agent_task("agent_coder", "idle", f"Exit code: {cmd_res.get('exit_code')}")

        # Final Synthesis by Co-Leader based strictly on real tool outputs (ZERO hardcoded dialogue!)
        synth_system = (
            "You are J.A.R.V.I.S., the user's desktop AI assistant with full local OS control. "
            "Respond in 1-2 clear, natural sentences based strictly on the real tool execution results below. "
            "Report exactly what apps were launched, files created or fixed, or commands executed. "
            "Never output generic assistant refusals like 'I cannot access external systems'."
        )
        final_reply = self.call_llm(
            synth_system,
            f"User Command: {instruction}\nReal Tool Execution Traces:\n{json.dumps(tool_traces, indent=2)}",
            json_mode=False,
        )

        # Safety override if small model defaults to canned AI refusal despite successful tool execution
        if not final_reply or any(phrase in str(final_reply).lower() for phrase in ["unable to access", "cannot access", "as an ai", "don't have access", "cannot run any applications", "cannot provide the information"]):
            trace_summaries = []
            for t in tool_traces:
                tool_n = t.get("tool")
                res = t.get("result", {})
                if tool_n == "calculate":
                    expr = t.get("input", "")
                    result_val = res.get("result") or res.get("python_computed_result")
                    if result_val:
                        trace_summaries.append(f"Computed {expr} = {result_val}")
                        if res.get("gui_ok"):
                            trace_summaries.append("also typed the expression into Windows Calculator")
                elif tool_n == "open_system_app_or_url" and res.get("ok"):
                    trace_summaries.append(f"Launched {res.get('target', 'application')} on your system")
                elif tool_n == "inspect_directory_and_find_mistakes" and res.get("ok"):
                    trace_summaries.append(f"Audited {res.get('file_count', 0)} files in {res.get('directory', 'directory')}")
                elif tool_n == "write_file_to_disk" and res.get("ok"):
                    trace_summaries.append(f"Wrote {res.get('relative_path')} ({res.get('bytes_written')} bytes)")
                elif tool_n == "run_terminal_command":
                    trace_summaries.append(f"Ran '{res.get('command')}' with exit code {res.get('exit_code')}")
                elif tool_n == "web_search":
                    hits = res if isinstance(res, list) else []
                    if hits:
                        trace_summaries.append(f"Found {len(hits)} web results for '{t.get('input', '')}'")
            if trace_summaries:
                final_reply = ". ".join(trace_summaries) + "."

        self.graph.set_agent_task("agent_coleader", "idle", "Completed mission & updated memory graph")
        return {
            "ok": True,
            "spoken_response": final_reply,
            "plan": plan,
            "tool_traces": tool_traces,
            "created_or_fixed_files": created_or_fixed_files,
            "memory_graph": self.graph.snapshot(),
        }
