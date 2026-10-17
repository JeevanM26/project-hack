with open(r'C:\Users\Jeevan\Downloads\j_a_r_v_i_s_antigravity_ai_ide_real_gemma_4_multi_agent_swarm_live_code_stream_playwright_vision_backend.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Header Stop Button next to btnHeaderRunPipeline
header_run_needle = '<button id="btnHeaderRunPipeline" type="button" class="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1 transition shadow">\n        <span>&#9654;</span> Build &amp; Test\n      </button>'
header_stop_code = header_run_needle + '\n      <button id="btnHeaderStop" type="button" class="hidden px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold flex items-center gap-1 transition animate-pulse" title="Halt running pipeline">\n        <span>■</span> Stop Task\n      </button>'
if header_run_needle in html:
    html = html.replace(header_run_needle, header_stop_code)
else:
    print("Warning: header_run_needle not found!")

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
else:
    print("Warning: exec_btn_needle not found!")

# 3. Replace the 3 presets with 6 presets
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

new_presets_code = '''        <!-- Quick Prompt Shortcuts (Sends prompt to real LLM backend) -->
        <div class="grid grid-cols-2 gap-1 text-[10px] mono">
          <button type="button" data-cmd="Build a Real-Time DevOps & Cloud Incident Command Center web app with service health cards and live event log" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-sky-300 truncate text-left" title="DevOps App">
            &#9889; 1. DevOps Incident App
          </button>
          <button type="button" data-cmd="Build an AI Multilingual Rural Healthcare Triage & ICU Dispatch web app with patient vital cards" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-amber-500/40 text-amber-300 truncate text-left" title="Rural Triage App">
            &#128030; 2. Rural Triage App
          </button>
          <button type="button" data-cmd="Build a Real-Time FinTech UPI Fraud & Anomaly Detection Radar web app with live transactions" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-emerald-300 truncate text-left" title="FinTech Fraud Radar">
            &#128200; 3. FinTech Fraud Radar
          </button>
          <button type="button" data-cmd="Open calculator." class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-rose-300 truncate text-left" title="Fast-Path OS process launcher">
            &#128640; 4. &lt;50ms: Open Calc
          </button>
          <button type="button" data-cmd="Build a Classic Snake Arcade Game in HTML5 Canvas with score board and restart controls" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-emerald-500/40 text-emerald-300 truncate text-left" title="Snake Canvas Game">
            &#127918; 5. Snake Canvas Game
          </button>
          <button type="button" data-cmd="Build a Full-Featured Interactive Scientific Calculator web app with arithmetic and memory keys" class="quick-cmd px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] border border-purple-500/40 text-purple-300 truncate text-left" title="Scientific Calculator App">
            &#129518; 6. Calculator App (Full)
          </button>
        </div>'''

if old_presets_needle in html:
    html = html.replace(old_presets_needle, new_presets_code)
else:
    print("Warning: old_presets_needle not found!")

# 4. In state object, add isPipelineStopped and isPipelineRunning
state_needle = "backendOnline: false,"
state_add = "backendOnline: true,\n      isPipelineStopped: false,\n      isPipelineRunning: false,"
html = html.replace(state_needle, state_add, 1)

# 5. Add stopCurrentPipeline function and Escape key handler
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

# Insert stopCurrentPipeline right before runFullAutonomousPipeline
pipeline_needle = 'async function runFullAutonomousPipeline(userPrompt, visualImageB64 = \'\') {'
html = html.replace(pipeline_needle, stop_func_code + '\n    ' + pipeline_needle)

# 6. Inside runFullAutonomousPipeline, handle stop state
pipeline_start_needle = '''    async function runFullAutonomousPipeline(userPrompt, visualImageB64 = '') {
      const targetDir = document.getElementById('targetDirInput').value.trim() || './hackathon_app';'''
pipeline_start_repl = '''    async function runFullAutonomousPipeline(userPrompt, visualImageB64 = '') {
      state.isPipelineStopped = false;
      state.isPipelineRunning = true;
      const btnHdrStop = document.getElementById('btnHeaderStop');
      if (btnHdrStop) btnHdrStop.classList.remove('hidden');
      const targetDir = document.getElementById('targetDirInput').value.trim() || './hackathon_app';'''
html = html.replace(pipeline_start_needle, pipeline_start_repl)

# 7. At end of runFullAutonomousPipeline, hide stop button and reset state
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

# 9. Register event listeners for Stop buttons, Escape key, and Ctrl+S save
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

# 10. Write saveCurrentFileToDisk function if not present
save_file_func = '''
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
      document.getElementById('btnSaveDiskFile')?.addEventListener('click', saveCurrentFileToDisk);
'''
html = html.replace("document.getElementById('btnSaveDiskFile').addEventListener('click', async () => {", save_file_func + "\n      // replaced:\n      const _ignore = (async () => {")

with open('jarvis_command_center.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Successfully generated unified jarvis_command_center.html')
