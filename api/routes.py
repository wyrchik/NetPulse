from flask import Blueprint, jsonify, request
import json
import os
import asyncio
from scanner.ports import scan_target_ports
api_blueprint = Blueprint('api', __name__)
from scanner.discovery import sweep_ips, get_mac_from_arp, get_local_ip, get_hostname
import ipaddress
@api_blueprint.route('/network_info', methods=['GET'])
def network_info():
    """Returns local IP and subnet to prefill UI."""
    local_ip = get_local_ip()
    if local_ip.startswith("127."):
        return jsonify({"local_ip": local_ip, "start_ip": "127.0.0.1", "end_ip": "127.0.0.255"})
    try:
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return jsonify({
            "local_ip": local_ip,
            "start_ip": str(network.network_address + 1),
            "end_ip": str(network.broadcast_address - 1)
        })
    except Exception:
        return jsonify({"local_ip": local_ip, "start_ip": local_ip, "end_ip": local_ip})
import queue
import threading
from flask import Response
scan_jobs = {}
@api_blueprint.route('/scan_stream', methods=['GET'])
def scan_stream():
    """Streams scan results to the client using SSE."""
    start_ip = request.args.get('start_ip')
    end_ip = request.args.get('end_ip')
    ports_str = request.args.get('ports', '80,443,22,21,445')
    speed = int(request.args.get('speed', 200))
    job_id = request.args.get('job_id', 'default')
    try:
        if not start_ip or not end_ip:
            return Response(f"data: {json.dumps({'error': 'IPs required'})}\n\n", mimetype='text/event-stream')
        start_addr = ipaddress.IPv4Address(start_ip)
        end_addr = ipaddress.IPv4Address(end_ip)
        if start_addr > end_addr:
            return Response(f"data: {json.dumps({'error': 'Start IP > End IP'})}\n\n", mimetype='text/event-stream')
        ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start_addr), int(end_addr) + 1)]
        ports = []
        if ports_str:
            for p in ports_str.split(','):
                try: ports.append(int(p.strip()))
                except: pass
        local_ip = get_local_ip()
        result_queue = queue.Queue()
        stop_event = threading.Event()
        scan_jobs[job_id] = stop_event
        def run_async_scan():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from scanner.discovery import stream_scan
            loop.run_until_complete(stream_scan(ip_list, speed, ports, local_ip, result_queue, stop_event))
            loop.close()
        threading.Thread(target=run_async_scan, daemon=True).start()
        def generate():
            try:
                while True:
                    if stop_event.is_set():
                        break
                    try:
                        event = result_queue.get(timeout=1.0)
                        yield f"data: {json.dumps(event)}\n\n"
                        if event["type"] == "done":
                            break
                    except queue.Empty:
                        yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            finally:
                stop_event.set()
                if job_id in scan_jobs:
                    del scan_jobs[job_id]
        return Response(generate(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
    except Exception as e:
        return Response(f"data: {json.dumps({'error': str(e)})}\n\n", mimetype='text/event-stream')
@api_blueprint.route('/stop_scan', methods=['POST'])
def stop_scan():
    """Stops an ongoing scan stream."""
    data = request.get_json() or {}
    job_id = data.get('job_id', 'default')
    if job_id in scan_jobs:
        scan_jobs[job_id].set()
    return jsonify({"status": "stopped"})
@api_blueprint.route('/scan_range', methods=['POST'])
def scan_range():
    """Scans a range of IPs (Angry IP Scanner style)."""
    try:
        data = request.get_json()
        start_ip = data.get('start_ip')
        end_ip = data.get('end_ip')
        ports_str = data.get('ports', '80,443,22,21,445')
        if not start_ip or not end_ip:
            return jsonify({"error": "Start and End IPs are required"}), 400
        try:
            start_addr = ipaddress.IPv4Address(start_ip)
            end_addr = ipaddress.IPv4Address(end_ip)
        except ValueError:
            return jsonify({"error": "Invalid IP address format"}), 400
        if start_addr > end_addr:
            return jsonify({"error": "Start IP must be <= End IP"}), 400
        ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start_addr), int(end_addr) + 1)]
        ports = []
        if ports_str:
            for p in ports_str.split(','):
                try:
                    ports.append(int(p.strip()))
                except:
                    pass
        local_ip = get_local_ip()
        speed = int(data.get('speed', 200))
        ping_results = asyncio.run(sweep_ips(ip_list, speed))
        final_results = []
        for ping_result in ping_results:
            if len(ping_result) == 4:
                ip, is_alive, latency, os_guess = ping_result
            else:
                ip, is_alive = ping_result
                latency, os_guess = 0.0, "Unknown"
            mac = "Unknown"
            hostname = "Unreachable"
            open_ports = []
            if is_alive:
                mac = get_mac_from_arp(ip)
                hostname = asyncio.run(get_hostname(ip))
                if ports:
                    open_ports = asyncio.run(scan_target_ports(ip, ports))
            final_results.append({
                "ip": ip,
                "hostname": hostname,
                "is_alive": is_alive,
                "mac": mac,
                "is_local": ip == local_ip,
                "os": os_guess,
                "latency": latency,
                "ports": open_ports
            })
        return jsonify(final_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
from scanner.bruteforce import run_bruteforce
@api_blueprint.route('/bruteforce', methods=['POST'])
def bruteforce():
    """Initiates a dictionary attack on a specific IP and port."""
    try:
        data = request.get_json()
        target_ip = data.get('ip')
        port = data.get('port', 22)
        username = data.get('username', 'root')
        protocol = data.get('protocol', 'SSH')
        delay = int(data.get('delay', 0))
        if not target_ip:
            return jsonify({"error": "IP is required"}), 400
        result = asyncio.run(run_bruteforce(target_ip, port, username, protocol, delay_ms=delay))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
