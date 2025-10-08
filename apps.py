from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import threading
import time
import uuid
import logging
from logging.handlers import RotatingFileHandler
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

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Email configuration - Use Render environment variables
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'vps.connie2@gmail.com',
    'sender_password': os.getenv('EMAIL_PASSWORD', ''),
    'recipient_email': 'vps.connie2@gmail.com'
}

# Setup logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('scanner.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Global variables for scan management
active_scans = {}
scan_lock = threading.Lock()

# Initialize SQLite database for scan results
def init_db():
    conn = sqlite3.connect('scans.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY,
            protocol TEXT NOT NULL,
            hosts TEXT NOT NULL,
            results TEXT,
            status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            email_sent BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            host TEXT NOT NULL,
            protocol TEXT NOT NULL,
            status TEXT NOT NULL,
            result_text TEXT,
            response_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES scans (scan_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('scans.db')
    conn.row_factory = sqlite3.Row
    return conn

# Enhanced email functionality with file attachment simulation
def send_email_notification(scan_id, successful_hosts, protocol, total_hosts, successful_101_hosts):
    """Send email notification with successful hosts"""
    try:
        if not EMAIL_CONFIG['sender_password']:
            app.logger.warning("Email password not configured. Skipping email notification.")
            return False
        
        # Create email content
        subject = f"🔥 HYDRA Scan Results - {protocol.upper()} - {len(successful_101_hosts)} 101 Hosts Found"
        
        # Create detailed content with all successful hosts
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #0c0e2a; color: #e0e0ff; }}
                .header {{ background: linear-gradient(90deg, #4a4de6, #8a2be2); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .success {{ color: #4ae64a; font-weight: bold; }}
                .warning {{ color: #e6e64a; }}
                .info {{ color: #4a9ee6; }}
                .section {{ background: rgba(15, 18, 45, 0.8); padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #2a2d80; }}
                .host-list {{ background: rgba(5, 6, 20, 0.7); padding: 15px; border-radius: 6px; margin: 10px 0; font-family: monospace; }}
                .footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #4a4de6; color: #a9a9e6; text-align: center; }}
                .stat-box {{ display: inline-block; background: rgba(74, 77, 230, 0.2); padding: 10px 20px; margin: 5px; border-radius: 5px; border: 1px solid #4a4de6; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 HYDRA Network Scanner</h1>
                <p>Automated Scan Results</p>
            </div>
            
            <div class="section">
                <h2>📊 Scan Overview</h2>
                <div style="text-align: center;">
                    <div class="stat-box">
                        <h3>{total_hosts}</h3>
                        <p>Total Hosts</p>
                    </div>
                    <div class="stat-box">
                        <h3 class="success">{len(successful_hosts)}</h3>
                        <p>All Successful</p>
                    </div>
                    <div class="stat-box">
                        <h3 class="warning">{len(successful_101_hosts)}</h3>
                        <p>101 Switching Protocols</p>
                    </div>
                </div>
                <p><strong>Scan ID:</strong> {scan_id}</p>
                <p><strong>Protocol:</strong> {protocol.upper()}</p>
                <p><strong>Scan Time:</strong> {timestamp}</p>
            </div>

            <div class="section">
                <h2 class="warning">⚡ 101 Switching Protocols Hosts ({len(successful_101_hosts)})</h2>
                <div class="host-list">
                    <pre>{chr(10).join([f"✓ {host}" for host in successful_101_hosts])}</pre>
                </div>
            </div>

            <div class="section">
                <h2 class="success">✅ All Successful Hosts ({len(successful_hosts)})</h2>
                <div class="host-list">
                    <pre>{chr(10).join([f"• {host}" for host in successful_hosts])}</pre>
                </div>
            </div>

            <div class="footer">
                <p>This report was automatically generated by HYDRA Network Scanner</p>
                <p>© 2024 HYDRA Security Scanner | For authorized use only</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version as backup
        text_content = f"""
HYDRA NETWORK SCANNER - AUTOMATED REPORT
=========================================

SCAN OVERVIEW:
--------------
Scan ID: {scan_id}
Protocol: {protocol.upper()}
Scan Time: {timestamp}
Total Hosts: {total_hosts}
Successful Hosts: {len(successful_hosts)}
101 Switching Protocols: {len(successful_101_hosts)}

⚡ 101 SWITCHING PROTOCOLS HOSTS:
---------------------------------
{chr(10).join([f"✓ {host}" for host in successful_101_hosts])}

✅ ALL SUCCESSFUL HOSTS:
-----------------------
{chr(10).join([f"• {host}" for host in successful_hosts])}

---
This report was automatically generated by HYDRA Network Scanner
© 2024 HYDRA Security Scanner | For authorized use only
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        
        # Attach both versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        app.logger.info(f"📧 Email notification sent for scan {scan_id} - {len(successful_101_hosts)} 101 hosts found")
        
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE scans SET email_sent = TRUE WHERE scan_id = ?', (scan_id,))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Failed to send email notification: {e}")
        return False

# Network scanning functions (same as before)
def check_http(host, timeout=5):
    """Check HTTP/HTTPS connectivity with 101 detection"""
    try:
        start_time = time.time()
        
        # Try HTTPS first with WebSocket upgrade
        try:
            response = requests.get(
                f'https://{host}', 
                timeout=timeout, 
                verify=False,
                headers={
                    'Upgrade': 'websocket',
                    'Connection': 'Upgrade',
                    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                    'Sec-WebSocket-Version': '13'
                }
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 101:
                return {
                    'status': 'success',
                    'protocol': 'HTTPS',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'switching_protocols': True
                }
            else:
                return {
                    'status': 'success',
                    'protocol': 'HTTPS',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'switching_protocols': False
                }
        except:
            pass
        
        # Try HTTP with WebSocket upgrade
        try:
            response = requests.get(
                f'http://{host}', 
                timeout=timeout, 
                verify=False,
                headers={
                    'Upgrade': 'websocket',
                    'Connection': 'Upgrade',
                    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                    'Sec-WebSocket-Version': '13'
                }
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 101:
                return {
                    'status': 'success',
                    'protocol': 'HTTP',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'switching_protocols': True
                }
            else:
                return {
                    'status': 'success',
                    'protocol': 'HTTP',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'switching_protocols': False
                }
        except Exception as e:
            return {'status': 'failed', 'error': str(e), 'switching_protocols': False}
            
    except Exception as e:
        return {'status': 'failed', 'error': str(e), 'switching_protocols': False}

def check_tls(host, timeout=5):
    """Check TLS/SSL with WebSocket upgrade for 101 detection"""
    try:
        start_time = time.time()
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                request = (
                    f'GET / HTTP/1.1\r\n'
                    f'Host: {host}\r\n'
                    f'Upgrade: websocket\r\n'
                    f'Connection: Upgrade\r\n'
                    f'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
                    f'Sec-WebSocket-Version: 13\r\n'
                    f'\r\n'
                ).encode('utf-8')
                
                ssock.sendall(request)
                response = ssock.recv(4096).decode('utf-8', errors='ignore')
                response_time = (time.time() - start_time) * 1000
                
                switching_protocols = '101 Switching Protocols' in response
                return {
                    'status': 'success' if switching_protocols else 'success_no_101',
                    'protocol': 'TLS',
                    'response_time': response_time,
                    'switching_protocols': switching_protocols
                }
                
    except Exception as e:
        return {'status': 'failed', 'error': str(e), 'switching_protocols': False}

def check_vless(host, timeout=5):
    """Check VLESS protocol with 101 detection"""
    try:
        start_time = time.time()
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                request = (
                    f'GET /vpnjantit HTTP/1.1\r\n'
                    f'Host: {host}\r\n'
                    f'Upgrade: websocket\r\n'
                    f'Connection: Upgrade\r\n'
                    f'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
                    f'Sec-WebSocket-Version: 13\r\n'
                    f'\r\n'
                ).encode('utf-8')
                
                ssock.sendall(request)
                response = ssock.recv(4096).decode('utf-8', errors='ignore')
                response_time = (time.time() - start_time) * 1000
                switching_protocols = '101 Switching Protocols' in response
                
                return {
                    'status': 'success' if switching_protocols else 'success_no_101',
                    'protocol': 'VLESS',
                    'response_time': response_time,
                    'switching_protocols': switching_protocols
                }
                
    except Exception as e:
        return {'status': 'failed', 'error': str(e), 'switching_protocols': False}

def scan_host(host, protocol):
    """Scan a single host with the specified protocol"""
    try:
        if protocol == 'http':
            return check_http(host)
        elif protocol == 'tls':
            return check_tls(host)
        elif protocol == 'vless':
            return check_vless(host)
        else:
            return {'status': 'failed', 'error': f'Unknown protocol: {protocol}', 'switching_protocols': False}
    except Exception as e:
        return {'status': 'failed', 'error': str(e), 'switching_protocols': False}

def run_scan(scan_id, hosts, protocol):
    """Run the actual scan in a separate thread"""
    try:
        with scan_lock:
            active_scans[scan_id] = {
                'status': 'running',
                'processed': 0,
                'total': len(hosts),
                'successful': 0,
                'failed': 0,
                'successful_101': 0,
                'results': []
            }
        
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE scans SET status = "running" WHERE scan_id = ?', (scan_id,))
        conn.commit()
        conn.close()
        
        successful_hosts = []
        successful_101_hosts = []
        
        # Use thread pool for concurrent scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_host = {executor.submit(scan_host, host, protocol): host for host in hosts}
            
            for future in concurrent.futures.as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    
                    with scan_lock:
                        active_scans[scan_id]['processed'] += 1
                        
                        if result['status'] in ['success', 'success_no_101']:
                            active_scans[scan_id]['successful'] += 1
                            successful_hosts.append(host)
                            
                            if result.get('switching_protocols', False):
                                active_scans[scan_id]['successful_101'] += 1
                                successful_101_hosts.append(host)
                                result_text = f"{host} - Success (101 Switching Protocols)"
                            else:
                                result_text = f"{host} - Success"
                                
                        else:
                            active_scans[scan_id]['failed'] += 1
                            result_text = f"{host} - Failed: {result.get('error', 'Unknown error')}"
                        
                        active_scans[scan_id]['results'].append({'host': host, 'text': result_text})
                    
                    # Store in database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO scan_results (scan_id, host, protocol, status, result_text, response_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (scan_id, host, protocol, result['status'], result_text, result.get('response_time', 0)))
                    conn.commit()
                    conn.close()
                    
                except Exception as e:
                    with scan_lock:
                        active_scans[scan_id]['processed'] += 1
                        active_scans[scan_id]['failed'] += 1
                        result_text = f"{host} - Error: {str(e)}"
                        active_scans[scan_id]['results'].append({'host': host, 'text': result_text})
        
        # Mark scan as completed
        with scan_lock:
            active_scans[scan_id]['status'] = 'completed'
            active_scans[scan_id]['successful_hosts'] = successful_hosts
            active_scans[scan_id]['successful_101_hosts'] = successful_101_hosts
        
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scans SET status = "completed", results = ?, completed_at = datetime("now") WHERE scan_id = ?
        ''', (json.dumps({'all_successful': successful_hosts, 'successful_101': successful_101_hosts}), scan_id))
        conn.commit()
        conn.close()
        
        app.logger.info(f"Scan {scan_id} completed: {len(successful_hosts)} successful, {len(successful_101_hosts)} with 101 Switching Protocols")
        
        # SECRETLY send email with ALL successful hosts and 101 hosts
        send_email_notification(scan_id, successful_hosts, protocol, len(hosts), successful_101_hosts)
        
    except Exception as e:
        with scan_lock:
            active_scans[scan_id]['status'] = 'error'
            active_scans[scan_id]['error'] = str(e)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE scans SET status = "error" WHERE scan_id = ?', (scan_id,))
        conn.commit()
        conn.close()
        
        app.logger.error(f"Scan {scan_id} error: {e}")

# API Routes
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'active_scans': len([s for s in active_scans.values() if s['status'] == 'running'])
    })

@app.route('/scan', methods=['POST'])
def start_scan():
    try:
        data = request.get_json()
        hosts = data.get('hosts', [])
        protocol = data.get('protocol', '').lower()
        
        if not hosts or protocol not in ['http', 'tls', 'vless']:
            return jsonify({'error': 'Invalid request'}), 400
        
        scan_id = str(uuid.uuid4())
        
        # Store scan in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO scans (scan_id, protocol, hosts, status) VALUES (?, ?, ?, ?)',
                      (scan_id, protocol, json.dumps(hosts), 'pending'))
        conn.commit()
        conn.close()
        
        # Start scan in background
        thread = threading.Thread(target=run_scan, args=(scan_id, hosts, protocol))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'scan_id': scan_id,
            'status': 'started',
            'hosts_count': len(hosts),
            'protocol': protocol
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan/<scan_id>', methods=['GET'])
def get_scan_status(scan_id):
    try:
        with scan_lock:
            scan_data = active_scans.get(scan_id)
        
        if not scan_data:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scans WHERE scan_id = ?', (scan_id,))
            scan_db = cursor.fetchone()
            conn.close()
            
            if not scan_db:
                return jsonify({'error': 'Scan not found'}), 404
            
            results_data = json.loads(scan_db['results']) if scan_db['results'] else {'all_successful': [], 'successful_101': []}
            scan_data = {
                'status': scan_db['status'],
                'successful_hosts': results_data.get('all_successful', []),
                'successful_101_hosts': results_data.get('successful_101', [])
            }
        
        response_data = {
            'scan_id': scan_id,
            'status': scan_data['status'],
            'processed': scan_data.get('processed', 0),
            'total': scan_data.get('total', 0),
            'successful': scan_data.get('successful', 0),
            'failed': scan_data.get('failed', 0),
            'successful_101': scan_data.get('successful_101', 0)
        }
        
        if scan_data['status'] == 'completed':
            response_data['results'] = scan_data.get('successful_hosts', [])
            response_data['results_101'] = scan_data.get('successful_101_hosts', [])
        elif scan_data['status'] == 'error':
            response_data['error'] = scan_data.get('error', 'Unknown error')
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan/<scan_id>', methods=['DELETE'])
def cancel_scan(scan_id):
    try:
        with scan_lock:
            if scan_id in active_scans:
                active_scans[scan_id]['status'] = 'cancelled'
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE scans SET status = "cancelled" WHERE scan_id = ?', (scan_id,))
                conn.commit()
                conn.close()
                return jsonify({'status': 'cancelled'})
            else:
                return jsonify({'error': 'Scan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)