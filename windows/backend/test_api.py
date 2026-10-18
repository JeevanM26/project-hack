import requests, json, time
time.sleep(4)

print("=== END-TO-END TEST: open calculator and execute 5*3583 ===")
r = requests.post("http://127.0.0.1:8000/api/execute", json={
    "instruction": "open calculator and execute 5*3583",
    "target_directory": "."
}, timeout=120)
d = r.json()
print("spoken_response:", d.get("spoken_response", "")[:300])
print()
print("tool_traces:")
for t in d.get("tool_traces", []):
    tn = t.get("tool")
    res = t.get("result", {})
    if tn == "calculate":
        print("  CALCULATE: expr =", res.get("expression"))
        print("  result =", res.get("result"))
        print("  gui_ok =", res.get("gui_ok"))
        print("  method =", res.get("gui_method"))
        print("  steps =", res.get("calculator_gui_steps"))
    elif tn == "open_system_app_or_url":
        print("  OPEN APP: target =", res.get("target"), "ok =", res.get("ok"))
