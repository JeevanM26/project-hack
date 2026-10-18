"""
J.A.R.V.I.S. v12.0 SOTA GODMODE — Master Pipeline: 3-Min Test Recording + Video Post-Production
1. Executes comprehensive automated test suite and records HD 720p 16:9 video (~3m 15s).
2. Performs post-production editing: Adds cinematic Intro & Outro cards, HUD overlays, and exports MP4.
"""

import sys
import time
from pathlib import Path
from run_3min_test_and_record import run_test_and_record
from edit_video import edit_video

if __name__ == "__main__":
    print("================================================================================")
    print("  J.A.R.V.I.S. v12.0 SOTA GODMODE — 3-MINUTE RECORD & EDIT PIPELINE")
    print("================================================================================")
    t0 = time.time()
    
    print("\n>>> STAGE 1: EXECUTING AUTOMATED TESTS & RECORDING HD SCREEN VIDEO...")
    record_ok = run_test_and_record()
    if not record_ok:
        print("❌ Recording failed!")
        sys.exit(1)
        
    t1 = time.time()
    print(f"✓ STAGE 1 COMPLETE: Recorded in {t1 - t0:.1f}s")
    
    print("\n>>> STAGE 2: VIDEO EDITING & POST-PRODUCTION (CINEMATIC CARDS & WATERMARK)...")
    edit_ok = edit_video()
    if not edit_ok:
        print("❌ Video editing failed!")
        sys.exit(1)
        
    t2 = time.time()
    print(f"✓ STAGE 2 COMPLETE: Edited in {t2 - t1:.1f}s")
    
    print("\n================================================================================")
    print("  ALL STAGES COMPLETE: 3-MINUTE VIDEO RECORDED & EDITED SUCCESSFULLY")
    print("  - Raw Video:    e:\\New folder\\jarvis_sota_godmode_3min_test_run.webm")
    print("  - Edited Video: e:\\New folder\\jarvis_sota_godmode_3min_edited.mp4")
    print(f"  - Total Elapsed Time: {t2 - t0:.1f}s")
    print("================================================================================")
