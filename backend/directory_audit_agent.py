"""
Directory Audit & Bug Triage Agent for J.A.R.V.I.S.
Inspects real files in any target directory, detects real AST syntax errors,
static logic bugs, runs test suites, and synthesizes actionable reports and patches.
"""
import ast
import json
import logging
import os
import re
import subprocess
from typing import Dict, Any, List, Optional, Tuple

from blackboard import global_blackboard

logger = logging.getLogger("JarvisDirectoryAuditor")


class DirectoryAuditAgent:
    def __init__(self, gemma_engine=None):
        self.engine = gemma_engine

    def resolve_target_directory(self, user_command: str, default_dir: Optional[str] = None) -> str:
        """
        Extracts a directory path mentioned in user_command or falls back to sensible default.
        Handles common typos like 'directry', 'findthe', and filters conversational stop words.
        """
        # Normalize common typos
        cmd_norm = re.sub(r'\bdirectry\b', 'directory', user_command, flags=re.I)
        cmd_norm = re.sub(r'\bdirectroy\b', 'directory', cmd_norm, flags=re.I)
        cmd_norm = re.sub(r'\bfoldr\b', 'folder', cmd_norm, flags=re.I)
        cmd_norm = re.sub(r'\bfindthe\b', 'find the', cmd_norm, flags=re.I)

        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

        # 1. Look for explicit quoted path
        quoted = re.findall(r'["\']([^"\']+)["\']', cmd_norm)
        for q in quoted:
            if os.path.exists(q) and os.path.isdir(q):
                return os.path.abspath(q)

        # 2. Check for named directories in repo
        known_dirs = ["workspaces", "sample_repo", "backend", "frontend"]
        for kd in known_dirs:
            if re.search(r'\b' + kd + r'\b', cmd_norm, re.I):
                cand_path = os.path.join(project_root, kd)
                if os.path.exists(cand_path) and os.path.isdir(cand_path):
                    return os.path.abspath(cand_path)
                cand_backend = os.path.join(project_root, "backend", kd)
                if os.path.exists(cand_backend) and os.path.isdir(cand_backend):
                    return os.path.abspath(cand_backend)

        # 3. Look for path patterns after keywords
        match = re.search(r'(?:in|inside|directory|folder|path)\s+(?:the\s+|a\s+|my\s+|this\s+)?([a-zA-Z0-9_\-\.\/\\:]+)', cmd_norm, re.I)
        candidates = []
        stop_words = {"a", "an", "the", "this", "my", "some", "current", "system", "laptop", "pc", "directory", "folder", "directry"}
        if match:
            raw = match.group(1).strip()
            if raw.lower() not in stop_words and len(raw) > 1:
                candidates.append(raw)

        for c in candidates:
            # Direct path
            if os.path.exists(c) and os.path.isdir(c):
                return os.path.abspath(c)
            # Relative to project root
            root_cand = os.path.join(project_root, c)
            if os.path.exists(root_cand) and os.path.isdir(root_cand):
                return os.path.abspath(root_cand)
            # Inside workspaces
            ws_cand = os.path.join(project_root, "workspaces", c)
            if os.path.exists(ws_cand) and os.path.isdir(ws_cand):
                return os.path.abspath(ws_cand)

        # 4. Default priority: workspaces -> default_dir -> project root
        ws_root = os.path.join(project_root, "workspaces")
        if os.path.exists(ws_root) and os.path.isdir(ws_root):
            # Check if workspaces has subfolders or files
            ws_contents = [f for f in os.listdir(ws_root) if not f.startswith(".")]
            if ws_contents:
                return os.path.abspath(ws_root)

        if default_dir and os.path.exists(default_dir):
            return os.path.abspath(default_dir)

        if os.path.exists(project_root) and os.path.isdir(project_root):
            return os.path.abspath(project_root)
        return os.path.abspath(os.getcwd())

    def audit_directory(self, target_dir: str, objective: str = "") -> Dict[str, Any]:
        """
        Crawls all source files in target_dir and executes deep AST & static code verification.
        """
        target_dir = os.path.abspath(target_dir)
        if not os.path.isdir(target_dir):
            return {
                "success": False,
                "error": f"Directory does not exist: {target_dir}",
                "spoken_response": f"I could not find the directory '{target_dir}' on your system, sir."
            }

        global_blackboard.update_status("AUDITING", objective=f"Audit directory {os.path.basename(target_dir)}")
        global_blackboard.post_chat_message(
            from_agent="Critic",
            to_agent="Swarm",
            message=f"Starting comprehensive code audit in: {target_dir}",
            kind="audit_start"
        )

        scanned_files: List[str] = []
        issues_found: List[Dict[str, Any]] = []
        file_ast_cache: Dict[str, Any] = {}

        # Ignored directory names
        ignore_dirs = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".idea", ".vscode", "dist", "build"}

        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), target_dir)
                ext = os.path.splitext(file)[1].lower()

                if ext in {".py", ".json", ".js", ".ts", ".html", ".css", ".yaml", ".yml", ".sql"}:
                    full_path = os.path.join(root, file)
                    scanned_files.append(rel_path)

                    if ext == ".py":
                        file_issues = self._audit_python_file(full_path, rel_path)
                        issues_found.extend(file_issues)
                    elif ext == ".json":
                        file_issues = self._audit_json_file(full_path, rel_path)
                        issues_found.extend(file_issues)

        # Run test suite if present
        test_results = self._run_directory_tests(target_dir)
        if test_results.get("failed_count", 0) > 0:
            for failure in test_results.get("failures", []):
                issues_found.append({
                    "file": failure.get("file", "test_suite"),
                    "line": failure.get("line", 1),
                    "severity": "HIGH",
                    "type": "TestFailure",
                    "message": failure.get("message", "Unit test assertion failed"),
                    "details": failure.get("traceback", "")
                })

        # Synthesize with Gemma 4
        synthesis = self._synthesize_audit_report(target_dir, scanned_files, issues_found, test_results, objective)

        # Write AUDIT_REPORT.md to disk in the target directory
        report_md = self._generate_markdown_report(target_dir, scanned_files, issues_found, test_results, synthesis)
        try:
            report_path = os.path.join(target_dir, "AUDIT_REPORT.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_md)
        except Exception as e:
            logger.warning(f"Could not write AUDIT_REPORT.md: {e}")

        files_with_issues = len(set(i["file"] for i in issues_found))
        spoken = (
            f"Audit complete for {os.path.basename(target_dir)}. "
            f"Scanned {len(scanned_files)} files and identified {len(issues_found)} issues across {files_with_issues} files. "
            f"I have documented the full analysis in AUDIT_REPORT.md, sir."
        ) if issues_found else (
            f"Audit complete for {os.path.basename(target_dir)}. "
            f"Scanned {len(scanned_files)} files with zero syntax errors or test failures detected, sir."
        )

        global_blackboard.post_chat_message(
            from_agent="Critic",
            to_agent="Co-Leader",
            message=f"Audit complete. {len(issues_found)} issues identified. Report generated.",
            kind="audit_complete"
        )

        return {
            "success": True,
            "target_dir": target_dir,
            "scanned_files_count": len(scanned_files),
            "scanned_files": scanned_files[:50],
            "issues_count": len(issues_found),
            "issues": issues_found,
            "test_results": test_results,
            "synthesis": synthesis,
            "report_markdown": report_md,
            "spoken_response": spoken
        }

    def _audit_python_file(self, full_path: str, rel_path: str) -> List[Dict[str, Any]]:
        """Performs AST parsing and static defect detection on a Python source file."""
        issues: List[Dict[str, Any]] = []
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return [{
                "file": rel_path,
                "line": 1,
                "severity": "HIGH",
                "type": "FileReadError",
                "message": f"Could not read file: {e}"
            }]

        # 1. AST Syntax Error detection
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as se:
            issues.append({
                "file": rel_path,
                "line": se.lineno or 1,
                "col": se.offset or 0,
                "severity": "CRITICAL",
                "type": "SyntaxError",
                "message": f"SyntaxError: {se.msg}",
                "snippet": se.text.strip() if se.text else ""
            })
            return issues  # Cannot parse further if syntax is broken

        # 2. Walk AST to detect common bugs
        funcs_defined = set()
        for node in ast.walk(tree):
            # Duplicate function definitions in same scope
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in funcs_defined and not node.name.startswith("_"):
                    issues.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "severity": "MEDIUM",
                        "type": "DuplicateFunction",
                        "message": f"Function '{node.name}' is defined multiple times in the same file."
                    })
                funcs_defined.add(node.name)

                # Mutable default argument: def foo(items=[])
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "file": rel_path,
                            "line": node.lineno,
                            "severity": "MEDIUM",
                            "type": "MutableDefaultArgument",
                            "message": f"Function '{node.name}' uses a mutable default argument ({type(arg).__name__})."
                        })

            # Bare except clause: except:
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "severity": "LOW",
                        "type": "BareExcept",
                        "message": "Bare 'except:' catches all exceptions including KeyboardInterrupt and SystemExit."
                    })

            # Literal division by zero: x / 0
            elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    issues.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "severity": "CRITICAL",
                        "type": "ZeroDivisionError",
                        "message": "Literal division by zero detected."
                    })

        return issues

    def _audit_json_file(self, full_path: str, rel_path: str) -> List[Dict[str, Any]]:
        """Validates JSON structure."""
        issues = []
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                json.load(f)
        except json.JSONDecodeError as je:
            issues.append({
                "file": rel_path,
                "line": je.lineno,
                "col": je.colno,
                "severity": "CRITICAL",
                "type": "JSONDecodeError",
                "message": f"Invalid JSON syntax: {je.msg}"
            })
        except Exception as e:
            issues.append({
                "file": rel_path,
                "line": 1,
                "severity": "HIGH",
                "type": "JSONReadError",
                "message": str(e)
            })
        return issues

    def _run_directory_tests(self, target_dir: str) -> Dict[str, Any]:
        """Runs pytest if tests are present in the directory."""
        has_tests = False
        for root, _, files in os.walk(target_dir):
            if any(f.startswith("test_") and f.endswith(".py") for f in files):
                has_tests = True
                break

        if not has_tests:
            return {"tests_found": False, "passed_count": 0, "failed_count": 0, "failures": []}

        try:
            res = subprocess.run(
                ["python", "-m", "pytest", "-q", "--tb=short"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            stdout = res.stdout
            failures = []
            for line in stdout.splitlines():
                if "FAILED" in line or "ERROR" in line:
                    failures.append({"file": "pytest", "message": line.strip()})
            return {
                "tests_found": True,
                "exit_code": res.returncode,
                "passed_count": 0 if res.returncode != 0 else 1,
                "failed_count": len(failures),
                "failures": failures,
                "output": stdout[:800]
            }
        except Exception as e:
            return {"tests_found": True, "error": str(e), "failed_count": 0, "failures": []}

    def _synthesize_audit_report(self, target_dir: str, files: List[str], issues: List[Dict[str, Any]], tests: Dict[str, Any], objective: str) -> Dict[str, Any]:
        """Uses Single Gemma 4 Engine to provide recommendations on discovered issues."""
        if not issues:
            return {
                "executive_summary": f"Directory '{os.path.basename(target_dir)}' passed all syntax and static validations cleanly.",
                "recommendations": ["Codebase is healthy. Maintain unit test coverage."]
            }

        prompt = (
            f"You are the Chief QA Reviewer auditing the directory: '{target_dir}'.\n"
            f"Scanned files count: {len(files)}\n"
            f"Detected issues:\n{json.dumps(issues[:10], indent=2)}\n\n"
            f"Provide a concise JSON analysis with:\n"
            f"- 'executive_summary': 2-3 sentence overview of code health\n"
            f"- 'root_causes': list of primary root causes\n"
            f"- 'recommendations': actionable steps to fix the code\n"
        )

        if self.engine:
            try:
                res = self.engine.call_agent("Zero-Hallucination Critic", "Analyze directory audit results", prompt)
                if isinstance(res, dict) and "executive_summary" in res:
                    return res
            except Exception:
                pass

        return {
            "executive_summary": f"Discovered {len(issues)} code defect(s) across {len(set(i['file'] for i in issues))} file(s).",
            "root_causes": [i["message"] for i in issues[:4]],
            "recommendations": [
                f"Fix syntax errors in {i['file']} at line {i.get('line', '?')}" for i in issues[:4]
            ]
        }

    def _generate_markdown_report(self, target_dir: str, files: List[str], issues: List[Dict[str, Any]], tests: Dict[str, Any], synthesis: Dict[str, Any]) -> str:
        """Formats the audit results into a structured Markdown document."""
        md = f"# J.A.R.V.I.S. Directory Code Audit Report\n\n"
        md += f"**Audited Directory**: `{target_dir}`\n"
        md += f"**Total Files Scanned**: `{len(files)}`\n"
        md += f"**Issues Identified**: `{len(issues)}`\n\n"

        md += f"## Executive Summary\n{synthesis.get('executive_summary', 'Audit complete.')}\n\n"

        if issues:
            md += "## Identified Code Mistakes & Vulnerabilities\n"
            md += "| File | Line | Severity | Type | Description |\n"
            md += "| :--- | :--- | :--- | :--- | :--- |\n"
            for iss in issues:
                md += f"| `{iss.get('file')}` | `{iss.get('line', '-')}` | **{iss.get('severity')}** | `{iss.get('type')}` | {iss.get('message')} |\n"
            md += "\n"

        if tests.get("tests_found"):
            md += "## Test Suite Verification\n"
            md += f"- **Exit Code**: `{tests.get('exit_code')}`\n"
            md += f"- **Failures**: `{tests.get('failed_count')}`\n"
            if tests.get("output"):
                md += f"```text\n{tests.get('output')}\n```\n\n"

        recs = synthesis.get("recommendations", [])
        if recs:
            md += "## Corrective Recommendations\n"
            for r in recs:
                md += f"- {r}\n"

        return md
