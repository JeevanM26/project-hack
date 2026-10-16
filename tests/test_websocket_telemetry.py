"""
Unit tests for backend/main.py WebSocket telemetry endpoint and connection manager.
"""
import os
import sys
import pytest
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from main import (
    TelemetryConnectionManager,
    build_telemetry_payload,
    app
)

def test_telemetry_payload_schema():
    payload = build_telemetry_payload()
    assert "timestamp" in payload
    assert "cursor" in payload
    assert "swarm" in payload
    assert "ast_grounding" in payload
    assert "hardware" in payload

    # Verify cursor structure
    cursor = payload["cursor"]
    assert "physical_xy" in cursor
    assert "normalized_coords" in cursor
    assert len(cursor["normalized_coords"]) == 2
    assert "screen_resolution" in cursor

    # Verify swarm structure
    swarm_info = payload["swarm"]
    assert "active_agents" in swarm_info
    assert len(swarm_info["active_agents"]) >= 1

    # Verify AST grounding enforcement
    ast_info = payload["ast_grounding"]
    assert ast_info["verification_status"] == "ENFORCED_ZERO_HALLUCINATION"
    assert "indexed_files" in ast_info
    assert len(ast_info["indexed_files"]) > 0

    # Verify Hardware allocation
    hw = payload["hardware"]
    assert "gpu" in hw
    assert "ram" in hw
    assert "RTX 5060" in hw["gpu"]["name"]


@pytest.mark.anyio
async def test_telemetry_connection_manager_lifecycle():
    manager = TelemetryConnectionManager()
    assert len(manager.active_connections) == 0

    class MockWebSocket:
        def __init__(self):
            self.accepted = False
            self.sent_messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, data):
            self.sent_messages.append(data)

    mock_ws = MockWebSocket()
    await manager.connect(mock_ws)
    assert mock_ws.accepted is True
    assert len(manager.active_connections) == 1

    # Test broadcast
    test_event = {"event": "cursor_move", "coords": [480, 105]}
    await manager.broadcast(test_event)
    assert len(mock_ws.sent_messages) == 1
    assert mock_ws.sent_messages[0] == test_event

    # Test disconnect
    manager.disconnect(mock_ws)
    assert len(manager.active_connections) == 0
