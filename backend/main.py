import asyncio
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from memory_graph import NeuralMemoryGraph
from llm_autonomous_brain import JarvisAutonomousBrain
from os_and_dir_tools import (
    open_system_app_or_url,
    inspect_directory_and_find_mistakes,
    run_terminal_command,
    write_file_to_disk,
    get_directory_tree,
)
from computer_use_agent import execute_computer_use, control_desktop_gui, attach_to_default_desktop

app = FastAPI(title="J.A.R.V.I.S. Crimson Red Autonomous OS & Antigravity IDE")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_graph = NeuralMemoryGraph()
brain = JarvisAutonomousBrain(memory_graph)


class CommandRequest(BaseModel):
    instruction: str
    target_directory: str = "."
    preferred_model: str = ""
    gemini_api_key: str = ""


class FileSaveRequest(BaseModel):
    path: str
    content: str
    base_dir: str = "."


class RunFileRequest(BaseModel):
    command: str
    cwd: str = "."


class DesktopGuiRequest(BaseModel):
    app: str = "desktop"
    goal: str = ""
    actions: List[Dict[str, Any]] = []


FRONTEND_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "jarvis_command_center.html"))
if not os.path.exists(FRONTEND_FILE):
    FRONTEND_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))
if not os.path.exists(FRONTEND_FILE):
    FRONTEND_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))


@app.get("/")
@app.get("/index.html")
@app.get("/jarvis_command_center.html")
def serve_index():
    return FileResponse(FRONTEND_FILE)


@app.get("/api/health")
def health():
    model_status = brain.detect_live_model()
    return {
        "ok": True,
        **model_status,
        "memory_graph": memory_graph.snapshot(),
    }


@app.post("/api/execute")
def execute_instruction(req: CommandRequest):
    try:
        attach_to_default_desktop()
    except Exception:
        pass
    if req.preferred_model:
        brain.preferred_model = req.preferred_model
    if req.gemini_api_key:
        brain.gemini_api_key = req.gemini_api_key
    return brain.execute_user_instruction(req.instruction, req.target_directory)


@app.post("/api/open-app")
def api_open_app(req: CommandRequest):
    try:
        attach_to_default_desktop()
    except Exception:
        pass
    return open_system_app_or_url(req.instruction)


@app.get("/api/screen-frame")
def api_screen_frame():
    try:
        import base64
        import io
        import PIL.ImageGrab
        attach_to_default_desktop()
        img = PIL.ImageGrab.grab()
        img.thumbnail((1280, 800))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {"ok": True, "image": f"data:image/jpeg;base64,{b64}", "width": img.width, "height": img.height}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/inspect-dir")
def api_inspect_dir(req: CommandRequest):
    return inspect_directory_and_find_mistakes(req.target_directory)


@app.get("/api/files")
def api_get_files(dir: str = ""):
    target_dir = dir.strip()
    if not target_dir or target_dir == ".":
        # Prefer the root workspace folder (parent of backend if in backend)
        if Path("..").resolve().exists() and (Path("..") / "jarvis_command_center.html").exists():
            target_dir = str(Path("..").resolve())
        else:
            target_dir = "."
    return get_directory_tree(target_dir)


@app.get("/api/file-content")
def api_get_file_content(path: str):
    try:
        p = Path(path)
        if not p.is_absolute():
            for cand in [Path(path).resolve(), (Path("..") / path).resolve(), (Path(os.getcwd()) / path).resolve()]:
                if cand.exists() and cand.is_file():
                    p = cand
                    break
        else:
            p = p.resolve()

        if not p.exists() or not p.is_file():
            return {"ok": False, "error": f"File '{path}' does not exist."}
        content = p.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "path": str(p),
            "name": p.name,
            "content": content,
            "lines": len(content.splitlines()),
            "size": len(content),
            "extension": p.suffix.lower(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/save-file")
def api_save_file(req: FileSaveRequest):
    p = Path(req.path)
    if p.is_absolute():
        base = str(p.parent)
        rel = p.name
    else:
        base = req.base_dir
        rel = req.path
    return write_file_to_disk(base, rel, req.content, force=True)


@app.post("/api/run-file")
def api_run_file(req: RunFileRequest):
    return run_terminal_command(req.command, cwd=req.cwd)


@app.post("/api/control-desktop")
def api_control_desktop(req: DesktopGuiRequest):
    try:
        attach_to_default_desktop()
    except Exception:
        pass
    return control_desktop_gui(req.app, req.goal, req.actions)


@app.post("/api/stop")
def api_stop():
    return brain.stop()


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"memory_graph": memory_graph.snapshot()})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
