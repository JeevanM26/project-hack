import os
from pathlib import Path

source_path = r'C:\Users\Jeevan\Downloads\j_a_r_v_i_s_antigravity_ai_ide_real_gemma_4_multi_agent_swarm_live_code_stream_playwright_vision_backend.html'
with open(source_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Header Stop Button next to btnHeaderRunPipeline
header_run_needle = '<button id="btnHeaderRunPipeline" type="button" class="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1 transition shadow">\n        <span>&#9654;</span> Build &amp; Test\n      </button>'
header_stop_code = header_run_needle + '\n      <button id="btnHeaderStop" type="button" class="hidden px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold flex items-center gap-1 transition animate-pulse" title="Halt running pipeline">\n        <span>■</span> Stop Task\n      </button>'
if header_run_needle in html:
    html = html.replace(header_run_needle, header_stop_code)

# 2. Add Stop button in composer next to btnExecuteCommand
exec_btn_needle = '''<button id="btnExecuteCommand" type="button" class="px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs mono shrink-0 transition">
            Run &rarr;
          </button>'''
composer_stop_code = exec_btn_needle + '''
          <button id="btnStopPipeline" type="button" class="px-3 py-2 rounded-lg bg-rose-950 hover:bg-rose-900 border border-rose-500/60 text-rose-200 font-bold text-xs mono shrink-0 transition flex items-center gap-1 shadow" title="Halt current pipeline immediately (Esc key)">
            <span>■</span> Stop
          </button>'''
if exec_btn_needle in html:
    html = html.replace(exec_btn_needle, composer_stop_code)

# 3. Add Export PDF button next to btnSaveDiskFile
save_btn_needle = '<button id="btnSaveDiskFile" type="button" class="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1 shadow">\n          <span>&#128190;</span> Save to Disk\n        </button>'
export_pdf_btn = save_btn_needle + '\n        <button id="btnExportPdf" type="button" class="px-2.5 py-1 rounded bg-rose-950 hover:bg-rose-900 border border-rose-500/50 text-rose-200 text-xs font-semibold flex items-center gap-1 shadow" title="Export current file or document to PDF">\n          <span>&#128196;</span> Export PDF\n        </button>'
if save_btn_needle in html:
    html = html.replace(save_btn_needle, export_pdf_btn)

# 4. Replace presets with all 12 rich presets (WebOS, Startup SaaS, YouTube, Netflix, Gmail, Bookings, Blender 3D, State-Aware Calc)
old_presets_needle = '''        <!-- Quick Prompt Shortcuts (Sends prompt to real LLM backend) -->
        <div class="grid grid-cols-3 gap-1 text-[10px] mono">
          <button type="button" data-cmd="Build a Real-Time DevOps & Cloud Incident Command Center web app with service health cards and live event log" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-sky-300 truncate text-left">
            &#9889; DevOps App Prompt
          </button>
          <button type="button" data-cmd="Build an Interactive Kanban Project Board web app with To-Do, In-Progress, and Done columns and task creation" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-purple-500/40 text-purple-300 truncate text-left">
            &#128203; Kanban App Prompt
          </button>
          <button type="button" data-cmd="Open calculator." class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-rose-300 truncate text-left">
            &#128640; Open Calc (&lt;50ms)
          </button>
        </div>'''

new_presets_code = '''        <!-- Quick Prompt Shortcuts (Real Computer-Use & Multi-Agent Swarm) -->
        <div class="grid grid-cols-2 gap-1 text-[10px] mono">
          <button type="button" data-cmd="Build a Real-Time DevOps & Cloud Incident Command Center web app with service health cards and live event log" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-sky-300 truncate text-left" title="DevOps Incident App">
            &#9889; 1. DevOps Incident App
          </button>
          <button type="button" data-cmd="Build an AI Multilingual Rural Healthcare Triage & ICU Dispatch web app with patient vital cards" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-amber-500/40 text-amber-300 truncate text-left" title="Rural Healthcare Triage App">
            &#128030; 2. Rural Triage App
          </button>
          <button type="button" data-cmd="Build a Real-Time FinTech UPI Fraud & Anomaly Detection Radar web app with live transactions" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-emerald-300 truncate text-left" title="FinTech Fraud Radar">
            &#128200; 3. FinTech Fraud Radar
          </button>
          <button type="button" data-cmd="open calculator and perform 10+20" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-rose-500/40 text-rose-300 truncate text-left" title="State-Aware Calculator (No duplicate spawn, performs 10+20)">
            &#129518; 4. Calc: 10+20 (State-Aware)
          </button>
          <button type="button" data-cmd="Build a Classic Snake Arcade Game in HTML5 Canvas with score board and restart controls" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-emerald-500/40 text-emerald-300 truncate text-left" title="Snake Canvas Game">
            &#127918; 5. Snake Canvas Game
          </button>
          <button type="button" data-cmd="Build a simple OS" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-indigo-500/40 text-indigo-300 truncate text-left" title="Complete Desktop WebOS with Terminal, Calc & Taskbar">
            &#129680; 6. Simple WebOS Desktop
          </button>
          <button type="button" data-cmd="Build an app for startup" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-cyan-500/40 text-cyan-300 truncate text-left" title="Modern SaaS Startup Platform with Hero, Demo & Pricing">
            &#128640; 7. Startup SaaS Platform
          </button>
          <button type="button" data-cmd="Model a 3D metallic torus in Blender" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-sky-500/40 text-sky-200 truncate text-left" title="Blender 5.2.2 3D Modeling Pipeline">
            &#127912; 8. Blender 3D: Torus
          </button>
          <button type="button" data-cmd="open gmail and draft email to investors" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-teal-500/40 text-teal-300 truncate text-left" title="Drafts email in Gmail and requests user review">
            &#128231; 9. Gmail: Investor Update
          </button>
          <button type="button" data-cmd="open youtube and play lofi hip hop" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-red-500/40 text-red-300 truncate text-left" title="Deep-link YouTube video stream">
            &#127916; 10. YouTube: Play Lo-Fi
          </button>
          <button type="button" data-cmd="open netflix and play movies" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-rose-600/40 text-rose-300 truncate text-left" title="Netflix Streaming Search">
            &#127871; 11. Netflix: Stream Movies
          </button>
          <button type="button" data-cmd="book a table at restaurant in Bengaluru" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-amber-500/40 text-amber-300 truncate text-left" title="Restaurant & Dining Reservation Radar">
            &#127869; 12. Book Restaurant Radar
          </button>
        </div>'''

if old_presets_needle in html:
    html = html.replace(old_presets_needle, new_presets_code)

# 5. In state object, add pipeline controls
state_needle = "backendOnline: false,"
state_add = "backendOnline: true,\n      isPipelineStopped: false,\n      isPipelineRunning: false,"
html = html.replace(state_needle, state_add, 1)

# 6. Add stopCurrentPipeline function
stop_func_code = '''
    function stopCurrentPipeline() {
      state.isPipelineStopped = true;
      state.isPipelineRunning = false;
      const btnHeader = document.getElementById('btnHeaderStop');
      if (btnHeader) btnHeader.classList.add('hidden');
      const termEl = document.getElementById('sideTerminalOutput');
      if (termEl) termEl.textContent += '\\n\\n[STOPPED] Execution halted by user via STOP option (Esc).';
      pushA2AMessage('Gemma-4 Coordinator', 'All Agents', 'HALT: Emergency STOP trigger received.', 'text-rose-400');
      state.memoryGraph.nodes.forEach(n => { n.status = 'idle'; });
      renderCompactSwarm();
      state.orbPulse = 1.0;
      if (state.backendOnline) {
        fetch(`${state.backendUrl}/api/stop`, { method: 'POST' }).catch(() => {});
      }
    }
'''
pipeline_needle = 'async function runFullAutonomousPipeline(userPrompt, visualImageB64 = \'\') {'
html = html.replace(pipeline_needle, stop_func_code + '\n    ' + pipeline_needle)

# 7. Inside runFullAutonomousPipeline, handle stop state
pipeline_start_needle = '''    async function runFullAutonomousPipeline(userPrompt, visualImageB64 = '') {
      const targetDir = document.getElementById('targetDirInput').value.trim() || './hackathon_app';'''
pipeline_start_repl = '''    async function runFullAutonomousPipeline(userPrompt, visualImageB64 = '') {
      state.isPipelineStopped = false;
      state.isPipelineRunning = true;
      const btnHdrStop = document.getElementById('btnHeaderStop');
      if (btnHdrStop) btnHdrStop.classList.remove('hidden');
      const targetDir = document.getElementById('targetDirInput').value.trim() || './hackathon_app';'''
html = html.replace(pipeline_start_needle, pipeline_start_repl)

pipeline_end_needle = '''      document.getElementById('latencyPill').textContent = `${totalMs}ms Total`;
      speakText(`Completed ${projectTitle} in ${totalMs} milliseconds.`);
      state.orbPulse = 1.0;
    }'''
pipeline_end_repl = '''      document.getElementById('latencyPill').textContent = `${totalMs}ms Total`;
      speakText(`Completed ${projectTitle} in ${totalMs} milliseconds.`);
      state.orbPulse = 1.0;
      state.isPipelineRunning = false;
      const btnHdrStopEnd = document.getElementById('btnHeaderStop');
      if (btnHdrStopEnd) btnHdrStopEnd.classList.add('hidden');
    }'''
html = html.replace(pipeline_end_needle, pipeline_end_repl)

# 8. Check isPipelineStopped inside streamCodeToEditor
stream_loop_needle = '''      for (let i = 0; i < total; i += step) {
        const chunk = lines.slice(i, i + step);'''
stream_loop_repl = '''      for (let i = 0; i < total; i += step) {
        if (state.isPipelineStopped) return;
        const chunk = lines.slice(i, i + step);'''
html = html.replace(stream_loop_needle, stream_loop_repl)

# 9. Neural TTS & Voice output in speakText
old_speak_needle = '''    async function speakText(text) {
      document.getElementById('liveJarvisTranscript').textContent = text;
      if (state.sarvamKey) {'''
new_speak_repl = '''    async function speakText(text) {
      document.getElementById('liveJarvisTranscript').textContent = text;
      // 1. Try Neural Edge-TTS via Backend (ultra-realistic J.A.R.V.I.S. speech, no API key needed)
      if (state.backendOnline) {
        try {
          const r = await fetch(`${state.backendUrl}/api/convert/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text.slice(0, 480), voice: 'en-GB-RyanNeural' })
          });
          if (r.ok) {
            const d = await r.json();
            if (d.audio_base64) {
              const audio = new Audio(`data:audio/mp3;base64,${d.audio_base64}`);
              await audio.play();
              return;
            }
          }
        } catch (_) {}
      }
      if (state.sarvamKey) {'''
if old_speak_needle in html:
    html = html.replace(old_speak_needle, new_speak_repl)

# 10. ExecuteCommand: Full Autonomous Computer-Use Dispatcher (State-aware tools, YouTube, Netflix, Gmail, Bookings)
old_exec_cmd_needle = r'''    async function executeCommand(rawCmd) {
      const cmd = (rawCmd || document.getElementById('mainCommandInput').value).trim();
      if (!cmd) return;

      const lower = cmd.toLowerCase().replace(/[.,!?;:]+$/g, '');
      const simpleOpen = lower.match(/^(?:hey\s+|hi\s+)?(?:jarvis[,\s]*)?(?:please\s+|can you\s+)?(?:open|launch|start)\s+(.+)$/);
      const isComplex = / and |write|code|create|build|fix|mistake|bug|install|app|test|screenshot|triage|radar|dashboard|kanban|physics|sim/.test(lower);'''

new_exec_cmd_repl = r'''    async function executeCommand(rawCmd) {
      const cmd = (rawCmd || document.getElementById('mainCommandInput').value).trim();
      if (!cmd) return;

      const lower = cmd.toLowerCase().replace(/[.,!?;:]+$/g, '');

      // 1. Autonomous Computer-Use Dispatcher (State-aware Windows tools, YouTube, Netflix, Gmail, Bookings)
      const isComputerUse = /calc|calculator|youtube|netflix|gmail|restaurant|dining|movie\s*ticket|bookmyshow|notepad|blender/.test(lower) &&
                            !/build|create\s+(?:an?\s+)?(?:web\s*)?app|code|repo/.test(lower);
      const isQuickOpen = /^(?:hey\s+|hi\s+)?(?:jarvis[,\s]*)?(?:please\s+|can you\s+)?(?:open|launch|start|play|book|perform|calculate)\s+/.test(lower);

      if (isComputerUse || isQuickOpen) {
        const t0 = performance.now();
        try {
          const r = await fetch(`${state.backendUrl}/api/open-app`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction: cmd })
          });
          const d = await r.json();
          if (d.ok && (d.speech || d.action)) {
            const ms = Math.round(performance.now() - t0);
            document.getElementById('latencyPill').textContent = `${ms}ms OS Fast-Path`;
            pushA2AMessage('Gemma-4 Coordinator', 'Antigravity Runner', `<50ms OS Action: ${d.message || d.action} (${ms}ms)`, 'text-emerald-300');
            const termEl = document.getElementById('sideTerminalOutput');
            if (termEl) termEl.textContent += `\n[COMPUTER USE AGENT] ${d.message || d.action}\n`;
            speakText(d.speech || `Executed ${cmd} in ${ms} milliseconds.`);
            return;
          }
        } catch (err) {
          console.warn('Computer-use API error:', err);
        }
      }

      // 2. Full Autonomous Swarm Synthesis (WebOS, Startup SaaS, Web Apps, Swarms)
      const simpleOpen = lower.match(/^(?:hey\s+|hi\s+)?(?:jarvis[,\s]*)?(?:please\s+|can you\s+)?(?:open|launch|start)\s+(.+)$/);
      const isComplex = / and |write|code|create|build|fix|mistake|bug|install|app|test|screenshot|triage|radar|dashboard|kanban|physics|sim/.test(lower);'''

if old_exec_cmd_needle in html:
    html = html.replace(old_exec_cmd_needle, new_exec_cmd_repl)

# 11. Save to Disk & Export PDF functionality
save_and_pdf_func = '''
      const saveCurrentFileToDisk = async () => {
        if (!state.selectedFile || !state.mountedFiles[state.selectedFile]) return;
        const updated = document.getElementById('studioCodeEditor').value;
        state.mountedFiles[state.selectedFile].content = updated;
        state.mountedFiles[state.selectedFile].lines = updated.split('\\n').length;
        selectIdeFile(state.selectedFile);
        if (state.mountedDirHandle) {
          await writeFilesToMountedBrowserDirectory([{ relative_path: state.selectedFile, content: updated }]);
        }
        if (state.backendOnline) {
          const files = Object.keys(state.mountedFiles).map(k => ({ relative_path: k, content: state.mountedFiles[k].content }));
          fetch(`${state.backendUrl}/api/build-and-test-app`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction: 'Save file edit', target_directory: document.getElementById('targetDirInput').value.trim() || './hackathon_app', files })
          }).catch(() => {});
        }
        speakText(`Saved ${state.selectedFile} to workspace.`);
      };

      const exportCurrentDocToPdf = async () => {
        const text = document.getElementById('studioCodeEditor').value || 'J.A.R.V.I.S. Project Spec';
        const title = state.selectedFile || 'Project Spec';
        try {
          const r = await fetch(`${state.backendUrl}/api/convert/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content: text, target_path: './hackathon_app/document.pdf' })
          });
          const d = await r.json();
          if (d.ok && d.base64_pdf) {
            const link = document.createElement('a');
            link.href = `data:application/pdf;base64,${d.base64_pdf}`;
            link.download = `${title.replace(/[^a-zA-Z0-9_-]/g, '_')}.pdf`;
            link.click();
            speakText(`Exported publication PDF in ${d.latency_ms} milliseconds.`);
          }
        } catch (err) {
          alert('PDF conversion requires backend running on port 8000: ' + err);
        }
      };

      document.getElementById('btnSaveDiskFile')?.addEventListener('click', saveCurrentFileToDisk);
      document.getElementById('btnExportPdf')?.addEventListener('click', exportCurrentDocToPdf);
'''
html = html.replace("document.getElementById('btnSaveDiskFile').addEventListener('click', async () => {", save_and_pdf_func + "\n      // replaced:\n      const _ignore = (async () => {")

# 12. Register event listeners for Stop buttons, Escape key, and Ctrl+S save
listener_needle = "document.getElementById('btnExecuteCommand').addEventListener('click', () => executeCommand());"
listener_repl = """document.getElementById('btnExecuteCommand').addEventListener('click', () => executeCommand());
      document.getElementById('btnStopPipeline')?.addEventListener('click', stopCurrentPipeline);
      document.getElementById('btnHeaderStop')?.addEventListener('click', stopCurrentPipeline);
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') stopCurrentPipeline();
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
          e.preventDefault();
          saveCurrentFileToDisk();
        }
      });"""
html = html.replace(listener_needle, listener_repl)

# 13. Write to all standard targets
targets = [
    Path('jarvis_command_center.html'),
    Path('backend/jarvis_command_center.html'),
    Path('index.html'),
    Path('backend/index.html'),
    Path('frontend/index.html'),
]

for target in targets:
    if target.parent.exists():
        target.write_text(html, encoding='utf-8')
        print(f"Successfully updated: {target}")

print("All unified HTML files generated and synchronized successfully!")
