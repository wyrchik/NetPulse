document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const stopBtn = document.getElementById('stop-btn');
    const startIpInput = document.getElementById('start-ip');
    const endIpInput = document.getElementById('end-ip');
    const portsInput = document.getElementById('ports-input');
    const speedInput = document.getElementById('speed-input');
    const tbody = document.getElementById('results-body');
    const foundText = document.getElementById('found-text');
    const speedText = document.getElementById('speed-text');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const topProgress = document.getElementById('top-progress');
    const scanSpinner = document.getElementById('scan-spinner');
    const scanBtnText = document.getElementById('scan-btn-text');
    const filterOnline = document.getElementById('filter-online');
    const deleteOfflineBtn = document.getElementById('delete-offline-btn');
    const exportCsvBtn = document.getElementById('export-csv-btn');
    const sortableHeaders = document.querySelectorAll('th.sortable');
    const speedDisplay = document.getElementById('speed-display');
    let stopRequested = false;
    let allResults = [];
    let currentSort = { column: null, asc: true };
    function logToConsole(msg) {
    }
    async function initNetworkInfo() {
        try {
            const res = await fetch('/api/network_info');
            const data = await res.json();
            startIpInput.value = data.start_ip || "";
            endIpInput.value = data.end_ip || "";
            logToConsole(`[INIT] Detected local network: ${data.local_ip}. Subnet configured.`);
        } catch(e) {
            logToConsole(`[WARN] Failed to auto-detect network.`);
        }
    }
    initNetworkInfo();
    speedInput.addEventListener('input', () => {
        speedDisplay.innerText = speedInput.value;
    });
    function ip2int(ip) {
        return ip.split('.').reduce((ipInt, octet) => (ipInt << 8) + parseInt(octet, 10), 0) >>> 0;
    }
    function int2ip(ipInt) {
        return ( (ipInt>>>24) +'.' + (ipInt>>16 & 255) +'.' + (ipInt>>8 & 255) +'.' + (ipInt & 255) );
    }
    let eventSource = null;
    stopBtn.addEventListener('click', () => {
        stopRequested = true;
        if (eventSource) {
            eventSource.close();
            fetch('/api/stop_scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_id: 'current_job' })
            });
            scanSpinner.classList.add('hidden');
            scanBtnText.innerText = "SCAN";
            scanBtn.disabled = false;
            speedText.innerText = "Scan STOPPED.";
            logToConsole(`[STOP] Scan aborted by user.`);
        }
    });
    scanBtn.addEventListener('click', async () => {
        const start = startIpInput.value.trim();
        const end = endIpInput.value.trim();
        if(!start || !end) {
            alert("Please enter both Start IP and End IP.");
            return;
        }
        stopRequested = false;
        allResults = [];
        tbody.innerHTML = '';
        scanSpinner.classList.remove('hidden');
        scanBtnText.innerText = "SCANNING...";
        scanBtn.disabled = true;
        const startInt = ip2int(start);
        const endInt = ip2int(end);
        if (startInt > endInt) {
            alert("Start IP must be <= End IP");
            resetProgress();
            return;
        }
        const totalIps = endInt - startInt + 1;
        const speed = parseInt(speedInput.value) || 200;
        const ports = portsInput.value.trim();
        let processed = 0;
        let foundCount = 0;
        speedText.innerText = `Intensity: ~${speed} concurrent`;
        logToConsole(`[SCAN] Starting real-time stream for range ${start} to ${end}...`);
        updateProgress(0);
        if (eventSource) eventSource.close();
        const url = `/api/scan_stream?start_ip=${start}&end_ip=${end}&ports=${ports}&speed=${speed}&job_id=current_job`;
        eventSource = new EventSource(url);
        eventSource.onmessage = function(event) {
            if (stopRequested) return;
            const data = JSON.parse(event.data);
            if (data.error) {
                alert("Error: " + data.error);
                eventSource.close();
                finishScan();
                return;
            }
            if (data.type === "progress") {
                processed++;
                let pct = Math.round((processed / totalIps) * 100);
                if (pct > 100) pct = 100;
                updateProgress(pct);
            } else if (data.type === "found") {
                allResults.push(data.device);
                foundCount++;
                foundText.innerText = `Found: ${foundCount} Devices`;
                logToConsole(`<span style="color:var(--green)">[SUCCESS] Found device: ${data.device.ip} (${data.device.os || 'Unknown'})</span>`);
                applySortAndRender();
            } else if (data.type === "done") {
                eventSource.close();
                updateProgress(100);
                finishScan();
            }
        };
        eventSource.onerror = function() {
            if (!stopRequested) {
                logToConsole(`[WARN] Stream ended.`);
                eventSource.close();
                finishScan();
            }
        };
        function finishScan() {
            scanSpinner.classList.add('hidden');
            scanBtnText.innerText = "SCAN";
            scanBtn.disabled = false;
            if(!stopRequested) speedText.innerText = "Scan COMPLETE.";
        }
    });
    sortableHeaders.forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.sort;
            if(currentSort.column === column) {
                currentSort.asc = !currentSort.asc;
            } else {
                currentSort.column = column;
                currentSort.asc = true;
            }
            sortableHeaders.forEach(h => h.querySelector('.sort-icon').innerText = '');
            th.querySelector('.sort-icon').innerText = currentSort.asc ? '▲' : '▼';
            applySortAndRender();
        });
    });
    function applySortAndRender() {
        let displayData = [...allResults];
        if(filterOnline.checked) {
            displayData = displayData.filter(d => d.is_alive);
        }
        if(currentSort.column === 'status') {
            displayData.sort((a, b) => {
                return currentSort.asc ? (a.is_alive === b.is_alive ? 0 : a.is_alive ? -1 : 1) 
                                       : (a.is_alive === b.is_alive ? 0 : a.is_alive ? 1 : -1);
            });
        } else if(currentSort.column === 'ip') {
            displayData.sort((a, b) => {
                const ipA = ip2int(a.ip);
                const ipB = ip2int(b.ip);
                return currentSort.asc ? ipA - ipB : ipB - ipA;
            });
        }
        renderTable(displayData);
    }
    filterOnline.addEventListener('change', applySortAndRender);
    deleteOfflineBtn.addEventListener('click', () => {
        allResults = allResults.filter(d => d.is_alive);
        applySortAndRender();
    });
    exportCsvBtn.addEventListener('click', () => {
        if(allResults.length === 0) {
            alert("No data to export.");
            return;
        }
        let txtContent = "NetPulse - Scan Results\n";
        txtContent += "=================================================================\n\n";
        allResults.forEach(d => {
            if (!d.is_alive) return;
            const name = d.hostname || (d.is_local ? 'localhost' : 'Unknown Device');
            const manufacturer = getManufacturer(d.mac);
            const os = d.os || "Unknown";
            const ping = d.latency ? `${d.latency}ms` : '-';
            txtContent += `[+] ${d.ip} (${name})\n`;
            txtContent += `    MAC: ${d.mac || 'N/A'} [${manufacturer}]\n`;
            txtContent += `    OS:  ${os}\n`;
            txtContent += `    Ping: ${ping}\n`;
            if (d.ports && d.ports.length > 0) {
                txtContent += `    Open Ports:\n`;
                d.ports.forEach(p => {
                    txtContent += `      - Port ${p.port} (${p.banner || 'No Banner'})\n`;
                });
            }
            txtContent += "\n";
        });
        const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", "vibescanner_log.txt");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        logToConsole("[EXPORT] Results saved to vibescanner_log.txt");
    });
    function updateProgress(pct) {
        if(progressFill) progressFill.style.width = pct + "%";
        if(progressPercent) progressPercent.innerText = pct + "%";
    }
    function resetProgress() {
        updateProgress(0);
        speedText.innerText = "Scan speed: 0 IPs/s";
    }
    function getManufacturer(mac) {
        if(!mac || mac === "Unknown") return "Generic Device";
        const prefix = mac.substring(0, 8).toUpperCase();
        const oui = {
            "00:1A:11": "Google",
            "00:50:56": "VMware",
            "00:0C:29": "VMware",
            "00:14:22": "Dell",
            "00:0A:95": "Apple",
            "E0:B9:BA": "Apple",
            "CC:29:F5": "Apple",
            "3C:22:FB": "Apple",
            "00:11:32": "Synology",
            "F8:1A:67": "TP-Link",
            "C4:6E:1F": "TP-Link",
            "00:1A:2B": "Samsung",
            "5C:0A:5B": "Samsung",
            "00:1E:4F": "Cisco",
            "00:00:0C": "Cisco"
        };
        return oui[prefix] || "Generic Device";
    }
    function renderTable(results) {
        const html = results.map(d => {
            const isOnline = d.is_alive;
            const statusClass = isOnline ? 'online' : 'offline';
            const statusText = isOnline ? 'Online' : 'Offline';
            const rowClass = isOnline ? '' : 'offline-row';
            let btnHtml = '';
            let portHtml = '';
            let deviceType = "Client";
            if(isOnline) {
                btnHtml = `<button class="btn-tools bf-btn" data-ip="${d.ip}" data-port="${d.ports && d.ports.length > 0 ? d.ports[0].port : 22}">Scan Ports</button>`;
                if (d.ports && d.ports.length > 0) {
                    const hasWeb = d.ports.find(p => p.port === 80 || p.port === 443 || p.port === 8080);
                    const hasApple = d.ports.find(p => p.port === 62078);
                    const hasSSH = d.ports.find(p => p.port === 22);
                    if (hasApple) deviceType = "Apple Device";
                    else if (hasWeb) deviceType = "Web Server / Router";
                    else if (hasSSH) deviceType = "Linux Server";
                    portHtml = d.ports.map(p => {
                        const bannerText = p.banner ? `<span class="port-banner">(${p.banner})</span>` : '';
                        return `<span class="port-badge">${p.port}${bannerText}</span>`;
                    }).join('');
                } else {
                    portHtml = `<span style="color: #666; font-size: 11px;">No open ports</span>`;
                }
            } else {
                btnHtml = `<button class="btn-tools btn-delete">🗑 Delete</button>`;
                portHtml = `-`;
            }
            const hostname = d.hostname || (d.is_local ? 'localhost' : (isOnline ? deviceType : 'Unreachable'));
            const manufacturer = getManufacturer(d.mac);
            const os = d.os || (isOnline ? 'Unknown' : '-');
            let pingClass = "ping-slow";
            let pingText = "-";
            if (isOnline) {
                const ms = Math.round(d.latency);
                pingText = ms + " ms";
                if (ms < 20) pingClass = "ping-fast";
                else if (ms < 100) pingClass = "ping-med";
            }
            return `
            <tr class="${rowClass}">
                <td><span class="dot ${statusClass}"></span> <span class="status-text ${statusClass}">${statusText}</span></td>
                <td style="font-weight: 500;">${hostname}</td>
                <td style="color: var(--cyan);">${d.ip} ${d.is_local ? '(You)' : ''}</td>
                <td>${os}</td>
                <td class="${pingClass}">${pingText}</td>
                <td style="font-family: monospace; font-size: 13px;">${d.mac || '-'}</td>
                <td style="color: var(--text-muted);">${manufacturer}</td>
                <td>${portHtml}</td>
                <td>${btnHtml}</td>
            </tr>
            `;
        }).join('');
        tbody.innerHTML = html;
        document.querySelectorAll('.bf-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                openBruteForceModal(e.target.dataset.ip, e.target.dataset.port);
            });
        });
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('tr').remove();
            });
        });
    }
    const bfModal = document.getElementById('bf-modal');
    const bfClose = document.getElementById('bf-close');
    const bfStartBtn = document.getElementById('bf-start-btn');
    const bfLog = document.getElementById('bf-log');
    const openBruteForceModal = (ip, port) => {
        document.getElementById('bf-ip').value = ip;
        document.getElementById('bf-port').value = port;
        bfLog.innerHTML = "";
        bfModal.classList.remove('hidden');
    };
    bfClose.addEventListener('click', () => { bfModal.classList.add('hidden'); });
    bfStartBtn.addEventListener('click', async () => {
        const ip = document.getElementById('bf-ip').value;
        const port = document.getElementById('bf-port').value;
        const username = document.getElementById('bf-user').value;
        const delay = document.getElementById('bf-delay').value;
        bfStartBtn.disabled = true;
        bfLog.innerHTML = `> Attacking ${ip}:${port} as ${username}...<br>> Delay: ${delay}ms between attempts...<br>> Testing 500+ passwords...<br>`;
        try {
            const res = await fetch('/api/bruteforce', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip, port, username, delay: parseInt(delay) || 0 })
            });
            const data = await res.json();
            if(data.success) {
                bfLog.innerHTML += `<br>[SUCCESS] Password Found!<br>User: ${username}<br>Pass: ${data.password}`;
            } else {
                bfLog.innerHTML += `<br>[FAILED] ${data.message}`;
            }
        } catch(e) {
            bfLog.innerHTML += `<br>[ERROR] Server disconnected.`;
        } finally {
            bfStartBtn.disabled = false;
        }
    });
});