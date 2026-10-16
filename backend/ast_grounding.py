"""
Deterministic AST & Repository Grounding Engine for J.A.R.V.I.S. (Gemma 4 Multi-Agent System).
Prevents hallucinations by indexing real files, classes, functions, imports, and line numbers,
and deterministically validating every agent patch before execution.
"""
import ast
import os
import subprocess
import tempfile
from typing import Dict, List, Any, Tuple


class RepoGroundingIndex:
    def __init__(self, repo_dir: str):
        self.repo_dir = os.path.abspath(repo_dir)
        self.index: Dict[str, Any] = {}

    def build_index(self) -> Dict[str, Any]:
        """Scans Python files in repo_dir and extracts exact AST symbols and line ranges."""
        self.index = {}
        for root, _, files in os.walk(self.repo_dir):
            if any(part.startswith(".") or part == "__pycache__" for part in root.split(os.sep)):
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.repo_dir)
                    self.index[rel_path] = self._parse_python_file(full_path)
        return self.index

    def _parse_python_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        lines = source.splitlines()
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            return {"error": f"SyntaxError at line {e.lineno}: {e.msg}", "line_count": len(lines)}

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                functions.append({
                    "name": node.name,
                    "args": args,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "docstring": ast.get_docstring(node) or ""
                })
            elif isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}")

        return {
            "line_count": len(lines),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "source": source,
        }

    def verify_claim_or_patch(
        self, target_file: str, proposed_code: str, referenced_symbols: List[str]
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Deterministic Critic Verification:
        1. Checks that target_file exists in the indexed repository.
        2. Checks that proposed_code parses into a valid Python AST without SyntaxError.
        3. Checks that all referenced_symbols exist either in the repo index or proposed AST.
        """
        issues: List[str] = []
        receipt: Dict[str, Any] = {
            "target_file_exists": False,
            "ast_syntax_valid": False,
            "verified_symbols": [],
            "missing_symbols": [],
        }

        if target_file not in self.index:
            issues.append(f"Hallucinated file path '{target_file}'. Valid files: {list(self.index.keys())}")
            return False, issues, receipt
        receipt["target_file_exists"] = True

        try:
            proposed_tree = ast.parse(proposed_code)
            receipt["ast_syntax_valid"] = True
        except SyntaxError as e:
            issues.append(f"Proposed code contains SyntaxError on line {e.lineno}: {e.msg}")
            return False, issues, receipt

        # Collect all known symbols in repo + proposed code
        known_symbols = set()
        for fdata in self.index.values():
            for fn in fdata.get("functions", []):
                known_symbols.add(fn["name"])
            for cls in fdata.get("classes", []):
                known_symbols.add(cls["name"])
                known_symbols.update(cls["methods"])

        for node in ast.walk(proposed_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                known_symbols.add(node.name)

        for sym in referenced_symbols:
            base_sym = sym.split(".")[-1].replace("()", "")
            if base_sym in known_symbols:
                receipt["verified_symbols"].append(sym)
            else:
                receipt["missing_symbols"].append(sym)
                issues.append(f"Unverified symbol reference '{sym}' not found in AST index.")

        return len(issues) == 0, issues, receipt
