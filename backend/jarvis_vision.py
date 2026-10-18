"""
J.A.R.V.I.S. Optical Vision & Multimodal Desktop Eye
Provides:
1. Real-time Laptop Webcam Optical Sensor (OpenCV cv2.VideoCapture)
2. Real-time Desktop Screen Capture & Visual Inspection (mss on WinSta0\\default)
3. Local Multimodal Neural Vision Engine (Moondream on Ollama)
4. Visual verification loops for GUI actions
"""

from __future__ import annotations

import base64
import ctypes
import io
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from PIL import Image

logger = logging.getLogger("jarvis.vision")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
VISION_MODEL = os.getenv("JARVIS_VISION_MODEL", "moondream")


def switch_to_default_desktop():
    """Ensures thread interacts with the user's active screen."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("default", 0, False, 0x1FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def capture_camera_frame() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Captures a real frame from the laptop's built-in webcam.
    Returns (success, base64_jpeg, saved_file_path).
    """
    try:
        import cv2

        # Try DirectShow backend (Windows 11 reliable)
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            return False, None, None

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            # Retry once on device 1
            cap1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            if cap1.isOpened():
                ret, frame = cap1.read()
                cap1.release()

        if not ret or frame is None:
            return False, None, None

        # Save to disk for inspection
        out_dir = Path(__file__).parent / "workspace_app" / "camera_snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        img_path = out_dir / f"jarvis_optic_{int(time.time())}.jpg"
        cv2.imwrite(str(img_path), frame)

        # Encode to base64
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64_str = base64.b64encode(buffer).decode("utf-8")
        return True, b64_str, str(img_path)
    except Exception as exc:
        logger.warning(f"Camera capture error: {exc}")
        return False, None, None


def capture_desktop_screenshot() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Captures full desktop screenshot on active Windows desktop.
    Returns (success, base64_jpeg, saved_file_path).
    """
    switch_to_default_desktop()
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        # Resize slightly for optimal fast inference
        w, h = img.size
        img_resized = img.resize((1280, int(1280 * h / w)))

        out_dir = Path(__file__).parent / "workspace_app" / "screen_snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        img_path = out_dir / f"jarvis_screen_{int(time.time())}.jpg"
        img_resized.save(str(img_path), format="JPEG", quality=82)

        buf = io.BytesIO()
        img_resized.save(buf, format="JPEG", quality=82)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        return True, b64_str, str(img_path)
    except Exception as exc:
        logger.warning(f"Desktop screenshot error: {exc}")
        return False, None, None


def analyze_multimodal_vision(b64_image: str, prompt: str) -> str:
    """
    Sends base64 image and prompt to local vision model (Moondream) in Ollama.
    Returns the visual description.
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": VISION_MODEL,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
            },
            timeout=35,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as exc:
        logger.warning(f"Ollama vision inference error: {exc}")
    return ""


def scan_laptop_camera() -> Dict[str, Any]:
    """
    Executes a real optical scan using the laptop's webcam.
    Performs multimodal vision analysis to recognize the user and environment.
    """
    t0 = time.perf_counter()
    ok, b64_img, file_path = capture_camera_frame()
    if not ok or not b64_img:
        return {
            "ok": False,
            "error": "Could not access optical sensor array (webcam). Ensure camera is connected and permissions granted.",
            "speech": "Optical sensor array is currently unavailable, sir.",
        }

    prompt = (
        "You are J.A.R.V.I.S. Optical Sensor Engine. "
        "Describe what you see through this laptop camera in detail. "
        "Identify the person, their clothing, glasses or appearance, their position at the desk, "
        "and their environment."
    )
    analysis = analyze_multimodal_vision(b64_img, prompt)
    latency = round((time.perf_counter() - t0) * 1000, 1)

    # Formulate natural Jarvis speech
    speech = (
        f"Optical scan complete, sir. I observe: {analysis[:180]}..."
        if analysis
        else "Optical scan complete. Visual sensor is operational and monitoring your workstation."
    )

    return {
        "ok": True,
        "action": "optical_camera_scan",
        "analysis": analysis,
        "file_path": file_path,
        "image_base64": b64_img,
        "speech": speech,
        "latency_ms": latency,
        "target": "Laptop HD Webcam",
    }


def scan_desktop_screen(task_context: str = "") -> Dict[str, Any]:
    """
    Executes real multimodal inspection of the active desktop screen.
    Identifies open applications, controls, and visual state.
    """
    t0 = time.perf_counter()
    ok, b64_img, file_path = capture_desktop_screenshot()
    if not ok or not b64_img:
        return {
            "ok": False,
            "error": "Could not capture desktop visual state.",
            "speech": "Desktop visual capture encountered an issue, sir.",
        }

    prompt = (
        f"Analyze this live Windows desktop screenshot. Context: '{task_context}'. "
        "Identify the active windows, buttons, text fields, and visual layout. "
        "Provide a concise 2-sentence visual assessment of what is on screen."
    )
    analysis = analyze_multimodal_vision(b64_img, prompt)
    latency = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "action": "desktop_visual_scan",
        "analysis": analysis,
        "file_path": file_path,
        "image_base64": b64_img,
        "speech": f"Visual screen inspection complete: {analysis[:160]}...",
        "latency_ms": latency,
        "target": "Windows 11 Desktop Screen",
    }
