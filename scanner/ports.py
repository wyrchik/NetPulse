import asyncio
import logging
from .logger import setup_logger
logger = setup_logger()
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080
]
async def grab_banner(reader, writer, port, ip):
    """Attempts to grab the banner from an open port."""
    try:
        if port in [80, 443, 8080]:
            request = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
        banner = await asyncio.wait_for(reader.read(1024), timeout=1.5)
        banner_str = banner.decode('utf-8', errors='ignore').strip()
        if port in [80, 443, 8080] and "HTTP" in banner_str:
            for line in banner_str.split('\r\n'):
                if line.lower().startswith('server:'):
                    return line.split(':', 1)[1].strip()
            return "Web Server"
        return banner_str.split('\n')[0][:50] if banner_str else ""
    except Exception:
        return ""
async def scan_port(ip: str, port: int):
    """Scans a single port."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=1.0)
        banner = await grab_banner(reader, writer, port, ip)
        writer.close()
        await writer.wait_closed()
        return {"port": port, "open": True, "banner": banner}
    except Exception:
        return None
async def scan_target_ports(ip: str, ports: list = None):
    """Scans multiple ports on a target IP concurrently."""
    if ports is None:
        ports = COMMON_PORTS
    tasks = [scan_port(ip, port) for port in ports]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res is not None and res.get("open")]
