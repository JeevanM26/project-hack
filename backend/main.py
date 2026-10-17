import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from memory_graph import NeuralMemoryGraph
from llm_autonomous_brain import JarvisAutonomousBrain
from os_and_dir_tools import open_system_app_or_url, inspect_directory_and_find_mistakes, run_terminal_command

app = FastAPI(title="J.A.R.V.I.S. Crimson Red Autonomous OS")
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
        from computer_use_agent import attach_to_default_desktop
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
        from computer_use_agent import attach_to_default_desktop
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
        from computer_use_agent import attach_to_default_desktop
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


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"memory_graph": memory_graph.snapshot()})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
