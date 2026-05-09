# NetPulse

**NetPulse** is a lightning-fast, professional-grade network auditing and discovery tool. Built for speed and accuracy, it leverages asynchronous real-time streaming to sweep networks, detect operating systems, and identify open ports in seconds.

![NetPulse Interface](screenshot_placeholder.png) *(You can replace this with your actual photo)*

## Key Features
- **Real-Time Discovery:** IPs appear on your screen instantly the millisecond they respond. No waiting for chunks to finish.
- **OS Fingerprinting:** Automatically guesses the operating system (Windows, Linux, Router) based on network TTL logic.
- **Banner Grabbing:** Actively probes open web ports (80, 443) to retrieve server banners (e.g., Apache, Nginx).
- **Latency Monitoring:** Color-coded ping latency visualization.
- **Hardware Identification:** Resolves MAC addresses to their physical manufacturers.
- **Glassmorphism UI:** A stunning, premium dark-mode interface with smooth animations.

## Getting Started

You **do not** need to install Python, Node.js, or any other complex dependencies. NetPulse is compiled as a standalone portable executable.

1. Download the latest `NetPulse.exe` file.
2. Double-click `NetPulse.exe` to start the engine.
3. Your default web browser will automatically open the NetPulse Dashboard (typically at `http://127.0.0.1:5000`).

## Usage Guide
- The tool automatically detects your local network subnet and pre-fills the IP range.
- Adjust the **Intensity** slider to control how many simultaneous connections are made (higher = faster, but may drop packets on weak routers).
- Enter specific **Ports** (comma-separated, e.g. `22,80,443`) to check during the sweep.
- Use the **Export (CSV)** button to save a detailed `.txt` log of your findings for further analysis.

---
*Created by Wyrchik*
