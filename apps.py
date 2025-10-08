from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import threading
import time
import uuid
import socket
import requests
import ssl
import json
from datetime import datetime
import concurrent.futures
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)
CORS(app)

# Your HTML content as a string variable
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hydra - Multi-Protocol Network Scanner</title>
    <style>
        /* Your complete CSS here */
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Courier New', monospace; }
        body { background: linear-gradient(135deg, #0c0e2a 0%, #1a1f4b 100%); color: #e0e0ff; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { width: 100%; max-width: 900px; background: rgba(10, 12, 35, 0.9); border: 1px solid #4a4de6; border-radius: 10px; box-shadow: 0 0 25px rgba(74, 77, 230, 0.4); padding: 30px; position: relative; overflow: hidden; }
        .container::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #4a4de6, #8a2be2, #4a4de6); }
        .logo { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #2a2d80; }
        .logo-pre { color: #4a4de6; font-size: 12px; line-height: 1.3; margin-bottom: 15px; text-align: center; overflow-x: auto; white-space: nowrap; padding: 10px; }
        .logo h1 { color: #8a2be2; font-size: 32px; margin-bottom: 10px; text-shadow: 0 0 10px rgba(138, 43, 226, 0.5); letter-spacing: 2px; }
        .logo p { color: #a9a9e6; font-size: 18px; margin-bottom: 5px; }
        .version { color: #4a4de6 !important; font-size: 14px !important; margin-top: 10px; }
        .upload-section { margin: 25px 0; padding: 20px; background: rgba(15, 18, 45, 0.6); border-radius: 8px; border: 1px dashed #4a4de6; }
        .upload-section h2 { font-size: 20px; margin-bottom: 15px; color: #a9a9e6; text-align: center; }
        .file-upload { display: flex; flex-direction: column; align-items: center; gap: 15px; }
        .file-input { display: none; }
        .file-label { background: linear-gradient(90deg, #4a4de6, #8a2be2); color: white; padding: 12px 25px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s ease; display: inline-block; }
        .file-label:hover { background: linear-gradient(90deg, #5b5eeb, #9b3bf2); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(74, 77, 230, 0.4); }
        .file-name { margin-top: 10px; font-size: 14px; color: #a9a9e6; }
        .mode-selector { margin: 30px 0; text-align: center; }
        .mode-selector h2 { font-size: 20px; margin-bottom: 20px; color: #a9a9e6; }
        .modes { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .mode-btn { background: rgba(74, 77, 230, 0.2); border: 1px solid #4a4de6; color: #e0e0ff; padding: 12px 25px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s ease; width: 120px; }
        .mode-btn:hover { background: rgba(74, 77, 230, 0.4); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(74, 77, 230, 0.2); }
        .mode-btn.selected { background: rgba(74, 77, 230, 0.6); box-shadow: 0 0 15px rgba(74, 77, 230, 0.5); }
        .action-buttons { display: flex; justify-content: center; gap: 15px; margin-top: 40px; }
        .action-btn { padding: 12px 30px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; }
        .scan-btn { background: linear-gradient(90deg, #4a4de6, #8a2be2); color: white; }
        .scan-btn:hover:not(:disabled) { background: linear-gradient(90deg, #5b5eeb, #9b3bf2); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(74, 77, 230, 0.4); }
        .scan-btn:disabled { background: #555; cursor: not-allowed; opacity: 0.7; }
        .config-btn { background: transparent; border: 1px solid #4a4de6; color: #e0e0ff; }
        .config-btn:hover { background: rgba(74, 77, 230, 0.1); }
        .output { margin-top: 30px; background: rgba(5, 6, 20, 0.7); border: 1px solid #2a2d80; border-radius: 6px; padding: 15px; height: 250px; overflow-y: auto; font-family: monospace; font-size: 14px; }
        .output pre { color: #a9e6a9; white-space: pre-wrap; word-break: break-all; }
        .scanning { color: #4a4de6; animation: pulse 1.5s infinite; }
        .success { color: #4ae64a; }
        .error { color: #e64a4a; }
        .warning { color: #e6e64a; }
        .info { color: #4a9ee6; }
        .stats { display: flex; justify-content: space-around; margin-top: 20px; padding: 15px; background: rgba(15, 18, 45, 0.6); border-radius: 8px; font-size: 14px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #4a4de6; }
        .results-section { margin-top: 20px; display: none; }
        .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .results-content { background: rgba(5, 6, 20, 0.7); border: 1px solid #2a2d80; border-radius: 6px; padding: 15px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 14px; color: #a9e6a9; }
        .copy-btn { background: rgba(74, 77, 230, 0.2); border: 1px solid #4a4de6; color: #e0e0ff; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-size: 14px; transition: all 0.3s ease; }
        .copy-btn:hover { background: rgba(74, 77, 230, 0.4); }
        .server-status { margin-top: 15px; padding: 8px; border-radius: 4px; text-align: center; font-size: 14px; }
        .server-connected { background: rgba(0, 255, 0, 0.1); color: #4ae64a; border: 1px solid #4ae64a; }
        .server-disconnected { background: rgba(255, 0, 0, 0.1); color: #e64a4a; border: 1px solid #e64a4a; }
        .server-connecting { background: rgba(255, 165, 0, 0.1); color: #e6e64a; border: 1px solid #e6e64a; }
        .retry-btn { background: rgba(74, 77, 230, 0.3); border: 1px solid #4a4de6; color: #e0e0ff; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 10px; }
        .retry-btn:hover { background: rgba(74, 77, 230, 0.5); }
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
        .footer { text-align: center; margin-top: 30px; color: #5a5da0; font-size: 12px; }
        @media (max-width: 600px) { .logo-pre { font-size: 8px; } .logo h1 { font-size: 24px; } .modes { flex-direction: column; align-items: center; } .mode-btn { width: 100%; max-width: 200px; } .action-buttons { flex-direction: column; } .stats { flex-direction: column; gap: 15px; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <pre class="logo-pre">
██╗  ██╗██╗   ██╗██████╗ ██████╗  █████╗
██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔══██╗
███████║ ╚████╔╝ ██║  ██║██████╔╝███████║
██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══██║
██║  ██║   ██║   ██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
            </pre>
            <h1>HYDRA</h1>
            <p>Multi-Protocol Network Scanner</p>
            <p class="version">v2.0</p>
        </div>
        
        <div class="upload-section">
            <h2>Upload Hosts File</h2>
            <div class="file-upload">
                <input type="file" id="fileInput" class="file-input" accept=".txt">
                <label for="fileInput" class="file-label">Choose File</label>
                <div id="fileName" class="file-name">No file selected</div>
                <div id="fileError" class="error" style="display: none; margin-top: 10px;"></div>
            </div>
        </div>
        
        <div class="mode-selector">
            <h2>Select scanning mode:</h2>
            <div class="modes">
                <button class="mode-btn" data-mode="http">HTTP</button>
                <button class="mode-btn" data-mode="tls">TLS</button>
                <button class="mode-btn" data-mode="vless">VLESS</button>
            </div>
            <div id="modeError" class="error" style="display: none; margin-top: 10px;"></div>
        </div>
        
        <div class="action-buttons">
            <button id="scanBtn" class="action-btn scan-btn" disabled>Start Scan</button>
            <button id="configBtn" class="action-btn config-btn">Configuration</button>
            <button id="cancelBtn" class="action-btn config-btn" style="display: none;">Cancel Scan</button>
        </div>
        
        <div id="serverStatus" class="server-status server-disconnected">
            Backend server: Disconnected
            <button id="retryConnection" class="retry-btn">Retry</button>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="totalHosts">0</div>
                <div>Total Hosts</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="successHosts">0</div>
                <div>Successful</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="failedHosts">0</div>
                <div>Failed</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="progress">0%</div>
                <div>Progress</div>
            </div>
        </div>
        
        <div class="output">
            <pre id="outputText">> System initialized successfully.
> Upload a hosts file and select a mode to begin scanning.</pre>
        </div>
        
        <div class="results-section" id="resultsSection">
            <div class="results-header">
                <h3>Successful Connections:</h3>
                <button class="copy-btn" id="copyResults">Copy Results</button>
            </div>
            <div class="results-content" id="resultsContent">
                <!-- Successful connections will be listed here -->
            </div>
        </div>
        
        <div class="footer">
            <p>© 2023 HYDRA Security Scanner | For authorized use only</p>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('fileInput');
            const fileName = document.getElementById('fileName');
            const fileError = document.getElementById('fileError');
            const modeButtons = document.querySelectorAll('.mode-btn');
            const modeError = document.getElementById('modeError');
            const scanButton = document.getElementById('scanBtn');
            const configBtn = document.getElementById('configBtn');
            const cancelBtn = document.getElementById('cancelBtn');
            const output = document.getElementById('outputText');
            const totalHostsEl = document.getElementById('totalHosts');
            const successHostsEl = document.getElementById('successHosts');
            const failedHostsEl = document.getElementById('failedHosts');
            const progressEl = document.getElementById('progress');
            const resultsSection = document.getElementById('resultsSection');
            const resultsContent = document.getElementById('resultsContent');
            const copyResultsBtn = document.getElementById('copyResults');
            const serverStatus = document.getElementById('serverStatus');
            const retryBtn = document.getElementById('retryConnection');
            
            let selectedMode = null;
            let hosts = [];
            let successfulHosts = [];
            let currentScanId = null;
            let isScanning = false;
            
            // Server configuration - Auto-detect current server
            const SERVER_URL = window.location.origin;
            let isServerConnected = false;
            
            // Initialize the application
            initializeApp();
            
            function initializeApp() {
                setupEventListeners();
                checkServerConnection();
                setInterval(checkServerConnection, 30000);
            }
            
            function setupEventListeners() {
                fileInput.addEventListener('change', handleFileUpload);
                modeButtons.forEach(button => {
                    button.addEventListener('click', handleModeSelection);
                });
                scanButton.addEventListener('click', startScan);
                configBtn.addEventListener('click', showConfig);
                cancelBtn.addEventListener('click', cancelScan);
                copyResultsBtn.addEventListener('click', copyResults);
                retryBtn.addEventListener('click', checkServerConnection);
            }
            
            function handleScanCompletion(data) {
                successfulHosts = data.results || [];
                const successful101Hosts = data.results_101 || [];
                
                output.innerHTML += `\\n<span class="success">> Scan completed. ${successfulHosts.length} successful, ${data.failed || 0} failed.</span>`;
                output.innerHTML += `\\n<span class="success">> ${successful101Hosts.length} hosts with 101 Switching Protocols detected.</span>`;
                output.innerHTML += `\\n<span class="info">> 📧 Report has been sent to your email automatically.</span>`;
                
                if (successful101Hosts.length > 0) {
                    resultsContent.textContent = successful101Hosts.join('\\n');
                    resultsSection.style.display = 'block';
                    output.innerHTML += `\\n<span class="success">> 101 Switching Protocols results available below.</span>`;
                    copyResultsToClipboard(successful101Hosts);
                } else if (successfulHosts.length > 0) {
                    resultsContent.textContent = successfulHosts.join('\\n');
                    resultsSection.style.display = 'block';
                    output.innerHTML += `\\n<span class="warning">> Results available below (no 101 Switching Protocols detected).</span>`;
                }
                
                isScanning = false;
                updateUIForScanning(false);
            }

            function updateScanProgress(data) {
                if (data.processed !== undefined && data.total > 0) {
                    const progress = Math.round((data.processed / data.total) * 100);
                    progressEl.textContent = `${progress}%`;
                    successHostsEl.textContent = data.successful || 0;
                    failedHostsEl.textContent = data.failed || 0;
                    
                    if (data.successful_101 > 0) {
                        output.innerHTML += `\\n<span class="success">> 101 Switching Protocols: ${data.successful_101} hosts</span>`;
                    }
                    
                    if (data.processed % 10 === 0) {
                        output.innerHTML += `\\n<span class="info">> Progress: ${data.processed}/${data.total} hosts (${progress}%)</span>`;
                        output.scrollTop = output.scrollHeight;
                    }
                }
            }

            async function copyResultsToClipboard(hosts) {
                try {
                    await navigator.clipboard.writeText(hosts.join('\\n'));
                    output.innerHTML += `\\n<span class="success">> 101 Switching Protocols results copied to clipboard automatically.</span>`;
                } catch (err) {
                    output.innerHTML += `\\n<span class="warning">> Failed to auto-copy results: ${err}</span>`;
                }
            }

            function handleFileUpload(e) {
                fileError.style.display = 'none';
                const file = e.target.files[0];
                if (!file) {
                    fileName.textContent = 'No file selected';
                    hosts = [];
                    updateScanButtonState();
                    return;
                }
                if (!file.name.endsWith('.txt')) {
                    showError(fileError, 'Please select a .txt file');
                    return;
                }
                fileName.textContent = file.name;
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const content = e.target.result;
                        parseHostsFile(content);
                    } catch (error) {
                        showError(fileError, `Error reading file: ${error.message}`);
                    }
                };
                reader.onerror = function() { showError(fileError, 'Error reading file'); };
                reader.readAsText(file);
            }
            
            function handleModeSelection(e) {
                modeError.style.display = 'none';
                modeButtons.forEach(btn => btn.classList.remove('selected'));
                this.classList.add('selected');
                selectedMode = this.getAttribute('data-mode');
                output.innerHTML += `\\n<span class="info">> ${selectedMode.toUpperCase()} mode selected.</span>`;
                updateScanButtonState();
            }
            
            function showError(element, message) {
                element.textContent = message;
                element.style.display = 'block';
                output.innerHTML += `\\n<span class="error">> ${message}</span>`;
            }
            
            async function checkServerConnection() {
                if (isScanning) return;
                serverStatus.textContent = 'Backend server: Checking...';
                serverStatus.className = 'server-status server-connecting';
                try {
                    const response = await fetch(`${SERVER_URL}/status`, {
                        method: 'GET',
                        headers: { 'Accept': 'application/json' },
                        signal: AbortSignal.timeout(5000)
                    });
                    if (response.ok) {
                        isServerConnected = true;
                        serverStatus.textContent = 'Backend server: Connected';
                        serverStatus.className = 'server-status server-connected';
                        output.innerHTML += `\\n<span class="success">> Backend server connection established.</span>`;
                    } else {
                        throw new Error(`Server responded with status ${response.status}`);
                    }
                } catch (error) {
                    isServerConnected = false;
                    serverStatus.textContent = 'Backend server: Disconnected';
                    serverStatus.className = 'server-status server-disconnected';
                    output.innerHTML += `\\n<span class="error">> Cannot connect to backend server.</span>`;
                }
                updateScanButtonState();
            }
            
            async function startScan() {
                if (!validateScanParameters()) return;
                try {
                    resetScanUI();
                    output.innerHTML += `\\n<span class="scanning">> Starting ${selectedMode.toUpperCase()} scan on ${hosts.length} hosts...</span>`;
                    const response = await fetchWithTimeout(`${SERVER_URL}/scan`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ hosts, protocol: selectedMode })
                    }, 10000);
                    if (!response.ok) throw new Error(`Server error: ${response.status}`);
                    const data = await response.json();
                    if (!data.scan_id) throw new Error('Invalid response from server');
                    currentScanId = data.scan_id;
                    isScanning = true;
                    updateUIForScanning(true);
                    pollScanResults(currentScanId);
                } catch (error) {
                    handleScanError(error);
                }
            }
            
            async function pollScanResults(scanId) {
                if (!isScanning || scanId !== currentScanId) return;
                try {
                    const response = await fetch(`${SERVER_URL}/scan/${scanId}`);
                    const data = await response.json();
                    if (data.error) throw new Error(data.error);
                    updateScanProgress(data);
                    switch (data.status) {
                        case 'completed': handleScanCompletion(data); break;
                        case 'running': setTimeout(() => pollScanResults(scanId), 1000); break;
                        case 'error': throw new Error(data.error || 'Scan failed');
                        case 'cancelled': output.innerHTML += `\\n<span class="warning">> Scan cancelled by user.</span>`; resetScanUI(); break;
                    }
                } catch (error) {
                    handleScanError(error);
                }
            }
            
            async function cancelScan() {
                if (!currentScanId || !isScanning) return;
                try {
                    const response = await fetch(`${SERVER_URL}/scan/${currentScanId}`, { method: 'DELETE' });
                    if (response.ok) {
                        output.innerHTML += `\\n<span class="warning">> Cancelling scan...</span>`;
                    }
                } catch (error) {
                    output.innerHTML += `\\n<span class="error">> Error cancelling scan: ${error.message}</span>`;
                }
            }
            
            function handleScanError(error) {
                output.innerHTML += `\\n<span class="error">> Scan error: ${error.message}</span>`;
                isScanning = false;
                updateUIForScanning(false);
            }
            
            function resetScanUI() {
                successfulHosts = [];
                successHostsEl.textContent = '0';
                failedHostsEl.textContent = '0';
                progressEl.textContent = '0%';
                resultsSection.style.display = 'none';
                currentScanId = null;
            }
            
            function updateUIForScanning(scanning) {
                isScanning = scanning;
                scanButton.disabled = scanning;
                cancelBtn.style.display = scanning ? 'block' : 'none';
                configBtn.style.display = scanning ? 'none' : 'block';
            }
            
            function validateScanParameters() {
                if (!selectedMode) {
                    showError(modeError, 'Please select a scanning mode');
                    return false;
                }
                if (hosts.length === 0) {
                    showError(fileError, 'Please upload a hosts file');
                    return false;
                }
                if (!isServerConnected) {
                    output.innerHTML += `\\n<span class="error">> Cannot start scan: server not connected.</span>`;
                    return false;
                }
                return true;
            }
            
            function updateScanButtonState() {
                scanButton.disabled = !(selectedMode && hosts.length > 0 && isServerConnected && !isScanning);
            }
            
            function parseHostsFile(content) {
                try {
                    hosts = [];
                    const lines = content.split('\\n');
                    let validHosts = 0;
                    for (let i = 0; i < lines.length; i++) {
                        let line = lines[i].trim();
                        if (line && !line.startsWith('#')) {
                            if (line.includes('://')) {
                                try {
                                    const url = new URL(line);
                                    line = url.hostname;
                                } catch (e) {
                                    const match = line.match(/^(?:https?:\\/\\/)?([^\\/]+)/i);
                                    if (match && match[1]) line = match[1];
                                }
                            }
                            if (line.includes(':')) line = line.split(':')[0];
                            if (isValidHostname(line) && !hosts.includes(line)) {
                                hosts.push(line);
                                validHosts++;
                            }
                        }
                    }
                    totalHostsEl.textContent = hosts.length;
                    output.innerHTML += `\\n<span class="success">> Loaded ${validHosts} valid hosts from file.</span>`;
                    if (validHosts === 0) showError(fileError, 'No valid hosts found in file');
                    updateScanButtonState();
                } catch (error) {
                    showError(fileError, `Error parsing file: ${error.message}`);
                }
            }
            
            function isValidHostname(hostname) {
                const regex = /^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$/;
                return regex.test(hostname) && hostname.length <= 253;
            }
            
            function showConfig() {
                output.innerHTML += `\\n<span class="info">> Server URL: ${SERVER_URL}</span>`;
                output.innerHTML += `\\n<span class="info">> Connection status: ${isServerConnected ? 'Connected' : 'Disconnected'}</span>`;
                output.innerHTML += `\\n<span class="info">> Selected mode: ${selectedMode || 'None'}</span>`;
                output.innerHTML += `\\n<span class="info">> Loaded hosts: ${hosts.length}</span>`;
            }
            
            async function copyResults() {
                try {
                    await navigator.clipboard.writeText(successfulHosts.join('\\n'));
                    output.innerHTML += `\\n<span class="success">> Results copied to clipboard.</span>`;
                } catch (err) {
                    output.innerHTML += `\\n<span class="error">> Failed to copy results: ${err}</span>`;
                }
            }
            
            async function fetchWithTimeout(url, options, timeout) {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                try {
                    const response = await fetch(url, { ...options, signal: controller.signal });
                    clearTimeout(timeoutId);
                    return response;
                } catch (error) {
                    clearTimeout(timeoutId);
                    if (error.name === 'AbortError') throw new Error(`Request timeout after ${timeout}ms`);
                    throw error;
                }
            }
        });
    </script>
</body>
</html>
"""

# Serve the HTML directly
@app.route('/')
def serve_frontend():
    return render_template_string(HTML_CONTENT)

# Your existing backend API routes continue here...
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online', 
        'timestamp': datetime.now().isoformat(),
        'active_scans': 0
    })

# Add other routes (scan, scan/<scan_id>, etc.) from your original code...

if __name__ == '__main__':
    print("🚀 HYDRA Scanner Server Starting...")
    print("📍 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
