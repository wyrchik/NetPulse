import asyncio
import platform
import subprocess
import re
import socket
import logging
from .logger import setup_logger
logger = setup_logger()
def get_local_ip():
    """Gets the primary local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
async def ping_ip(ip: str):
    """Pings an IP asynchronously."""
    param_count = '-n' if platform.system().lower() == 'windows' else '-c'
    param_wait = '-w' if platform.system().lower() == 'windows' else '-W'
    wait_val = '1000' if platform.system().lower() == 'windows' else '1'
    try:
        process = await asyncio.create_subprocess_exec(
            'ping', param_count, '1', param_wait, wait_val, ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await process.communicate()
        output = stdout.decode('utf-8', errors='ignore')
        if process.returncode == 0:
            logger.info(f"[ALIVE] {ip}")
            ttl_match = re.search(r'[Tt][Tt][Ll]=(\d+)', output)
            ttl = int(ttl_match.group(1)) if ttl_match else 0
            time_match = re.search(r'[Tt]ime[=<]([\d\.]+)\s*ms', output)
            if not time_match:
                time_match = re.search(r'[Чч]ас[=<]([\d\.]+)\s*мс', output) 
            latency = float(time_match.group(1)) if time_match else 1.0
            os_guess = "Unknown"
            if 0 < ttl <= 64: os_guess = "Linux/Mac"
            elif 64 < ttl <= 128: os_guess = "Windows"
            elif 128 < ttl <= 255: os_guess = "Router"
            return ip, True, latency, os_guess
        else:
            logger.info(f"[DEAD] {ip}")
            return ip, False, 0.0, "Unknown"
    except Exception as e:
        logger.info(f"[DEAD] {ip}")
        return ip, False, 0.0, "Unknown"
async def sweep_ips(ip_list: list, speed: int = 500):
    """Sweeps a list of IPs for active ones safely using a semaphore."""
    sem = asyncio.Semaphore(speed) 
    async def sem_ping(ip):
        async with sem:
            return await ping_ip(ip)
    tasks = [sem_ping(ip) for ip in ip_list]
    results = await asyncio.gather(*tasks)
    return results
def get_mac_from_arp(ip: str):
    """Looks up MAC address from ARP cache."""
    try:
        if platform.system().lower() == 'windows':
            output = subprocess.check_output(['arp', '-a', ip]).decode()
            match = re.search(r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})', output)
            return match.group(0).replace('-', ':').upper() if match else "Unknown"
        else:
            output = subprocess.check_output(['arp', '-n', ip]).decode()
            match = re.search(r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})', output)
            return match.group(0).upper() if match else "Unknown"
    except Exception:
        return "Unknown"
async def get_hostname(ip: str):
    """Attempts to resolve the hostname of an IP address."""
    loop = asyncio.get_event_loop()
    try:
        host, _ = await asyncio.wait_for(
            loop.run_in_executor(None, socket.getnameinfo, (ip, 0), socket.NI_NAMEREQD),
            timeout=0.5
        )
        return host
    except Exception:
        return "Unknown Device"
async def stream_scan(ip_list: list, speed: int, ports: list, local_ip: str, result_queue, stop_event):
    """Streams scan results to a queue in real-time."""
    sem = asyncio.Semaphore(speed)
    from scanner.ports import scan_target_ports
    async def process_ip(ip):
        if stop_event.is_set():
            return
        async with sem:
            try:
                ip_res, is_alive, latency, os_guess = await ping_ip(ip)
                result_queue.put({"type": "progress"})
                if is_alive:
                    mac = get_mac_from_arp(ip)
                    hostname = await get_hostname(ip)
                    open_ports = []
                    if ports:
                        open_ports = await scan_target_ports(ip, ports)
                    device = {
                        "ip": ip,
                        "hostname": hostname,
                        "is_alive": True,
                        "mac": mac,
                        "is_local": ip == local_ip,
                        "os": os_guess,
                        "latency": latency,
                        "ports": open_ports
                    }
                    result_queue.put({"type": "found", "device": device})
            except Exception:
                pass
    tasks = [process_ip(ip) for ip in ip_list]
    await asyncio.gather(*tasks)
    result_queue.put({"type": "done"})
