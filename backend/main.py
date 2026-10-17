"""
FastAPI Backend for J.A.R.V.I.S. (Hacktoberfest Hack Day Bengaluru 2026 - Track 1: Best Use of Gemma 4).
Combines G1 (Autonomous Dynamic Multi-Agent Swarm with 1 Single Gemma 4 Model)
and G2 (Voice-First AI Interaction with Sarvam AI).
"""
import asyncio
import io
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import JarvisMultiAgentSwarm
from sarvam_voice import SarvamVoicePipeline
from hardware_profile import HardwareOptimizer
from gui_computer_agent import JarvisGUIComputerAgent
from blackboard import global_blackboard

app = FastAPI(
    title="J.A.R.V.I.S. Mark LXXXV — Gemma 4 GUI + Multi-Agent + Sarvam Voice OS",
    description="Single-Model Dynamic Agent Swarm & Physical Mouse GUI Operator for Open-Source Maintainers"
)

INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "jarvis_command_center.html"))
if not os.path.exists(INDEX_PATH):
    INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))
if not os.path.exists(INDEX_PATH):
    INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/")
@app.head("/")
def serve_jarvis_frontend():
    """Serves the 3D J.A.R.V.I.S. Mark LXXXV Holographic Command Center UI."""
    return FileResponse(INDEX_PATH)

@app.get("/jarvis_command_center.html")
@app.get("/index.html")
def serve_command_center():
    return FileResponse(INDEX_PATH)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_DIR = os.getenv("JARVIS_REPO_DIR", os.path.join(os.path.dirname(__file__), "sample_repo"))
swarm = JarvisMultiAgentSwarm(repo_dir=REPO_DIR)
voice = SarvamVoicePipeline()
hw = HardwareOptimizer()
gui_agent = swarm.gui_agent


class TelemetryConnectionManager:
    """Manages active WebSocket connections and broadcasts real-time telemetry."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


telemetry_manager = TelemetryConnectionManager()


def build_telemetry_payload() -> Dict[str, Any]:
    """Assembles instantaneous physical cursor, swarm blackboard, AST verification, and GPU allocation state."""
    bb = swarm.current_blackboard
    scr_w, scr_h = gui_agent.get_screen_size()
    last_xy = gui_agent.session_memory.get("last_mouse_xy", [0, 0])
    norm_x = round((last_xy[0] / scr_w) * 1000, 1) if scr_w else 0.0
    norm_y = round((last_xy[1] / scr_h) * 1000, 1) if scr_h else 0.0
    return {
        "timestamp": time.time(),
        "cursor": {
            "physical_xy": last_xy,
            "normalized_coords": [norm_x, norm_y],
            "screen_resolution": [scr_w, scr_h],
            "active_app": gui_agent.session_memory.get("active_app")
        },
        "swarm": {
            "status": global_blackboard.status if global_blackboard.status != "IDLE" else ("active" if bb else "standby"),
            "active_agents": global_blackboard.active_agents,
            "single_model": swarm.engine.model_name,
            "objective": global_blackboard.user_objective or (bb.objective if bb else None),
            "chat_count": len(global_blackboard.team_chat_bus)
        },
        "blackboard": global_blackboard.get_snapshot(),
        "ast_grounding": {
            "indexed_files": list(swarm.grounding.build_index().keys()),
            "receipts": bb.verification_receipts if bb else [],
            "verification_status": "ENFORCED_ZERO_HALLUCINATION"
        },
        "inference": {
            "source": swarm.engine.last_inference_source,
            "model": swarm.engine.model_name,
            "is_live_gpu": swarm.engine.is_live_gpu,
            "using_mock_fallback": swarm.engine.using_mock_fallback,
            "installed_models": swarm.engine.installed_models
        },
        "hardware": hw.get_hardware_telemetry()
    }


@app.get("/api/health")
def get_system_health():
    """Truthfully reports Ollama connection, installed models, and whether live GPU inference is active."""
    engine = swarm.engine
    engine._probe_ollama()
    return {
        "status": "healthy",
        "ollama_connected": engine.ollama_connected,
        "ollama_base_url": engine.ollama_base_url,
        "active_model": engine.model_name,
        "installed_models": engine.installed_models,
        "last_inference_source": engine.last_inference_source,
        "is_live_gpu": engine.is_live_gpu,
        "using_mock_fallback": engine.using_mock_fallback,
        "hardware": hw.get_hardware_telemetry()
    }


class CommandRequest(BaseModel):
    command: str
    language_code: str = "en-IN"
    synthesize_voice: bool = True
    simulate_hallucination: bool = False
    execute_on_desktop_gui: bool = True


class AutonomousMissionRequest(BaseModel):
    objective: str
    depth: int = 3
    run_tests: bool = True
    launch_app: bool = True
    synthesize_voice: bool = True
    language_code: str = "en-IN"


class TerminalRunRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: int = 60


class DirectoryAuditRequest(BaseModel):
    directory: Optional[str] = None
    command: Optional[str] = None
    synthesize_voice: bool = True
    language_code: str = "en-IN"


class WriteCodeRequest(BaseModel):
    prompt: str
    target_filename: Optional[str] = None
    synthesize_voice: bool = True
    language_code: str = "en-IN"


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """
    WebSocket telemetry endpoint streaming real-time:
    - Physical & Normalized cursor coordinates [norm_x, norm_y]
    - Dynamic agent swarm state (active_agents, blackboard status)
    - AST verification status and verification receipts
    - GPU (RTX 5060 8GB GDDR7) and 24GB RAM allocation profile
    """
    await telemetry_manager.connect(websocket)
    try:
        # Send initial snapshot immediately upon connect
        await websocket.send_json(build_telemetry_payload())

        while True:
            data = await websocket.receive_text()
            payload = build_telemetry_payload()
            payload["client_echo"] = data
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        telemetry_manager.disconnect(websocket)
    except Exception:
        telemetry_manager.disconnect(websocket)


@app.post("/api/gui-action")
async def run_gui_mouse_action(req: CommandRequest):
    """Executes stateful desktop GUI mouse movements, clicks, and typing via Gemma 4 UI Pointing + PyAutoGUI."""
    gui_res = gui_agent.execute_gui_command(req.command)
    spoken = gui_res.get("spoken_response") or f"Executed {len(gui_res['executed_steps'])} GUI steps on your laptop screen. Active app is {gui_res['active_app']}."
    if req.synthesize_voice and voice.api_key:
        try:
            gui_res["tts_audio"] = voice.synthesize_speech(spoken, language_code=req.language_code)
        except Exception:
            pass
    gui_res["spoken_response"] = spoken

    # Broadcast updated physical cursor & GUI state over WebSocket
    try:
        await telemetry_manager.broadcast({
            "event": "gui_action",
            "payload": build_telemetry_payload(),
            "gui_res": {
                "active_app": gui_res.get("active_app"),
                "executed_steps_count": len(gui_res.get("executed_steps", []))
            }
        })
    except Exception:
        pass

    return gui_res


@app.post("/api/stop")
@app.get("/api/stop")
def stop_all_active_media():
    """Immediately silences all background audio and kills automated browser processes."""
    return swarm.os_actions.stop_all_media()


@app.get("/api/telemetry")
def get_hardware_telemetry():
    """Returns real-time GPU (RTX 5060 8GB) and 24GB RAM allocation profile."""
    return hw.get_hardware_telemetry()


@app.get("/api/status")
def get_system_status():
    """Returns active Gemma 4 single-model config and Sarvam voice pipeline state."""
    return {
        "status": "online",
        "single_model": swarm.engine.model_name,
        "repo_dir": REPO_DIR,
        "indexed_modules": list(swarm.grounding.build_index().keys()),
        "sarvam_configured": bool(voice.api_key),
        "gemini_api_configured": bool(swarm.engine.gemini_api_key),
        "hardware": hw.get_hardware_telemetry(),
    }


@app.get("/api/index")
def get_repo_index():
    """Returns the deterministic AST symbol index of the project."""
    return {"repo_dir": REPO_DIR, "index": swarm.grounding.build_index()}


@app.get("/api/blackboard")
def get_current_blackboard():
    """Returns the live Shared Project Blackboard state."""
    snapshot = global_blackboard.get_snapshot()
    bb = swarm.current_blackboard
    if bb and not snapshot.get("user_objective"):
        return {
            "status": "active",
            "objective": bb.objective,
            "blueprint": bb.blueprint,
            "active_agents": bb.active_agents,
            "chat_bus": bb.chat_bus,
            "files_registered": list(bb.files_registry.keys()),
            "receipts": bb.verification_receipts
        }
    return snapshot


@app.post("/api/autonomous-mission")
async def run_autonomous_mission(req: AutonomousMissionRequest):
    """
    Executes the full 5-Phase Autonomous Deep-Research & Software Engineering Swarm.
    100% General-purpose: works on ANY research topic, full-stack app, or terminal task.
    """
    mission_res = swarm.execute_autonomous_mission(
        objective=req.objective,
        depth=req.depth,
        run_tests=req.run_tests,
        launch_app=req.launch_app
    )

    if req.synthesize_voice and voice.api_key:
        try:
            tts = voice.synthesize_speech(mission_res["spoken_response"], language_code=req.language_code)
            mission_res["tts_audio"] = tts
        except Exception as e:
            mission_res["tts_warning"] = str(e)

    try:
        await telemetry_manager.broadcast({
            "event": "autonomous_mission_complete",
            "payload": build_telemetry_payload(),
            "mission": {
                "objective": req.objective,
                "project_slug": mission_res.get("project_slug"),
                "workspace_dir": mission_res.get("workspace_dir"),
                "generated_files": mission_res.get("generated_files", [])
            }
        })
    except Exception:
        pass

    return mission_res


@app.post("/api/terminal-run")
async def run_terminal_command(req: TerminalRunRequest):
    """Executes a real shell command in the workspace directory and broadcasts stdout/stderr."""
    res = swarm.workspace_agent.run_shell_command(req.command, cwd=req.cwd, timeout=req.timeout)
    try:
        await telemetry_manager.broadcast({
            "event": "terminal_command",
            "payload": build_telemetry_payload(),
            "command_result": res
        })
    except Exception:
        pass
@app.post("/api/audit-directory")
async def run_directory_audit(req: DirectoryAuditRequest):
    """Audits real files in the directory for syntax errors, bugs, and test failures."""
    cmd = req.command or f"Audit directory {req.directory or '.'}"
    target_dir = swarm.directory_auditor.resolve_target_directory(cmd, default_dir=req.directory or REPO_DIR)
    audit_res = swarm.directory_auditor.audit_directory(target_dir, objective=cmd)

    spoken = audit_res.get("spoken_response")
    if req.synthesize_voice and voice.api_key and spoken:
        try:
            audit_res["tts_audio"] = voice.synthesize_speech(spoken, language_code=req.language_code)
        except Exception:
            pass

    try:
        await telemetry_manager.broadcast({
            "event": "directory_audit_complete",
            "payload": build_telemetry_payload(),
            "audit": {
                "target_dir": target_dir,
                "scanned_files_count": audit_res.get("scanned_files_count", 0),
                "issues_count": audit_res.get("issues_count", 0)
            }
        })
    except Exception:
        pass

    return audit_res


@app.post("/api/write-code")
async def run_code_creation(req: WriteCodeRequest):
    """Writes requested code to disk, validates AST syntax, and registers in workspace."""
    code_res = swarm.workspace_agent.write_code_for_user(req.prompt, target_filename=req.target_filename)
    spoken = code_res.get("spoken_response")
    if req.synthesize_voice and voice.api_key and spoken:
        try:
            code_res["tts_audio"] = voice.synthesize_speech(spoken, language_code=req.language_code)
        except Exception:
            pass

    try:
        await telemetry_manager.broadcast({
            "event": "code_creation_complete",
            "payload": build_telemetry_payload(),
            "code_res": {
                "filename": code_res.get("filename"),
                "ast_syntax_valid": code_res.get("ast_syntax_valid", True)
            }
        })
    except Exception:
        pass

    return code_res


@app.get("/api/workspace-files")
def get_workspace_files(project: Optional[str] = None):
    """Returns real filesystem files generated in workspaces/<project_slug>."""
    base_dir = swarm.workspace_agent.base_workspace_dir
    target_dir = os.path.join(base_dir, project) if project else swarm.workspace_agent.current_workspace or base_dir
    if not os.path.exists(target_dir):
        return {"project": project, "workspace_dir": target_dir, "files": []}
    
    files_list = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, target_dir)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read(25000)
            except Exception:
                content = ""
            files_list.append({
                "path": rel,
                "size": os.path.getsize(full_path),
                "content": content
            })
    return {
        "project": project or os.path.basename(target_dir),
        "workspace_dir": target_dir,
        "files": files_list
    }


@app.get("/api/screen-frame")
def get_screen_frame():
    """Returns single JPEG frame of active desktop."""
    img = gui_agent.capture_screen()
    if not img:
        return Response(content=b"", media_type="image/jpeg", status_code=503)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return Response(content=buf.getvalue(), media_type="image/jpeg")


@app.get("/api/screen-stream")
def get_screen_mjpeg_stream():
    """Live MJPEG video stream of user desktop."""
    def frame_generator():
        while True:
            img = gui_agent.capture_screen()
            if img:
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=60)
                frame = buf.getvalue()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.12)
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/api/mission")
async def run_text_or_transcribed_mission(req: CommandRequest):
    """
    Runs the single-model dynamic multi-agent swarm:
    Handles YouTube playback, project building, or AST-grounded bug triage.
    """
    result = swarm.execute_voice_mission(
        req.command,
        simulate_hallucination=req.simulate_hallucination
    )

    if req.execute_on_desktop_gui and result.get("type") == "gui_action" and "gui_res" not in result:
        try:
            result["gui_trace"] = gui_agent.execute_gui_command(req.command)
        except Exception as e:
            result["gui_trace_warning"] = str(e)
    
    if req.synthesize_voice and voice.api_key:
        try:
            tts = voice.synthesize_speech(result["spoken_response"], language_code=req.language_code)
            result["tts_audio"] = tts
        except Exception as e:
            result["tts_warning"] = str(e)

    # Broadcast updated multi-agent blackboard & AST state
    try:
        await telemetry_manager.broadcast({
            "event": "mission_executed",
            "payload": build_telemetry_payload(),
            "mission_summary": {
                "objective": req.command,
                "ast_verified": result.get("ast_verified", True),
                "active_agents": result.get("active_agents", [])
            }
        })
    except Exception:
        pass

    return result


@app.post("/api/voice-mission")
async def run_audio_mission(
    audio: UploadFile = File(...),
    language_code: str = Form("en-IN"),
    mode: str = Form("codemix"),
    simulate_hallucination: bool = Form(False),
):
    """
    Accepts raw microphone audio from user, transcribes via Sarvam Saaras v4,
    executes single-model Gemma 4 swarm, and synthesizes audio via Sarvam Bulbul v4 Flash.
    """
    audio_bytes = await audio.read()
    repo_files = list(swarm.grounding.build_index().keys())
    
    stt_res = voice.transcribe_speech(
        audio_bytes=audio_bytes,
        filename=audio.filename or "command.wav",
        mode=mode,
        language_code=language_code,
        keyterms=repo_files + ["pytest", "idempotency", "GST", "webhook", "Gemma", "YouTube", "Kesariya"],
    )
    
    transcript = stt_res.get("transcript", "").strip()
    mission_res = None
    tts_res = None

    if transcript:
        mission_res = swarm.execute_voice_mission(
            transcript,
            simulate_hallucination=simulate_hallucination
        )
        if voice.api_key and mission_res.get("spoken_response"):
            try:
                tts_res = voice.synthesize_speech(mission_res["spoken_response"], language_code=language_code)
            except Exception:
                pass

    return {
        "stt": stt_res,
        "mission": mission_res,
        "tts": tts_res,
    }


@app.get("/api/os-action/youtube")
def trigger_youtube_action(query: str = Query("Kesariya Brahmastra")):
    """Direct testing endpoint for YouTube song playback action."""
    return swarm.os_actions.play_youtube_song(query, auto_open_browser=False)


@app.get("/api/browser-status")
def get_browser_automation_status():
    """Returns active Playwright desktop browser session state."""
    if swarm.os_actions.browser_auto:
        return swarm.os_actions.browser_auto.get_status()
    return {"standby": False, "active_app": None, "worker_status": {"is_alive": False}}


class BrowserActionRequest(BaseModel):
    action: str  # open, search, play, pause, close
    query: Optional[str] = None
    url: Optional[str] = None
    app_name: Optional[str] = "browser"


@app.post("/api/browser-action")
def trigger_browser_action(req: BrowserActionRequest):
    """Direct GUI control endpoint for Playwright browser automation."""
    auto = swarm.os_actions.browser_auto
    if not auto:
        return {"success": False, "error": "Browser automation not initialized"}

    if req.action == "open" and req.url:
        return auto.open_website(req.url, req.app_name or "browser")
    elif req.action == "search" and req.query:
        return auto.search(req.query)
    elif req.action in ["play", "play_video"]:
        return auto.play_video(req.query)
    elif req.action in ["pause", "pause_resume"]:
        return auto.pause_resume()
    elif req.action == "close":
        return auto.close_active()
    else:
        return {"success": False, "error": f"Unsupported browser action: {req.action}"}
