import ipaddress
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTableWidget, 
    QTableWidgetItem, QProgressBar, QHeaderView, QMessageBox,
    QCheckBox, QSlider, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from gui.worker import ScanWorker
from scanner.discovery import get_local_ip

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetPulse")
        self.resize(1200, 800)
        
        # Global Stylesheet mimicking the Web UI
        self.setStyleSheet("""
            QMainWindow { background-color: #12141c; }
            QWidget#centralWidget { background-color: #12141c; }
            QLabel { color: #d1d5db; font-family: 'Inter', sans-serif; font-size: 12px; }
            
            QLineEdit { 
                background-color: #1a1d27; 
                border: 1px solid #2d3343; 
                color: #e0e0e0; 
                padding: 6px 12px; 
                border-radius: 6px; 
            }
            QLineEdit:focus { border: 1px solid #00e5ff; }
            
            QPushButton { 
                background-color: transparent;
                color: #d1d5db; 
                border: 1px solid #2d3343; 
                padding: 6px 15px; 
                border-radius: 6px; 
                font-size: 12px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.05); }
            
            QPushButton#btnScan { 
                background-color: rgba(0, 229, 255, 0.1); 
                color: #00e5ff; 
                border: 1px solid #00e5ff; 
                font-weight: bold;
            }
            QPushButton#btnScan:hover { background-color: rgba(0, 229, 255, 0.2); }
            QPushButton#btnScan:disabled { border-color: #2d3343; color: #555; background-color: transparent; }
            
            QPushButton#btnStop {
                font-weight: bold;
            }
            QPushButton#btnStop:hover { border-color: #ff5252; color: #ff5252; }
            
            QTableWidget { 
                background-color: #161923; 
                border: 1px solid #2d3343; 
                border-radius: 8px; 
                color: #d1d5db; 
                gridline-color: transparent;
                selection-background-color: rgba(255, 255, 255, 0.05);
                outline: none;
            }
            QHeaderView::section { 
                background-color: #161923; 
                color: #8b92a5; 
                padding: 12px; 
                border: none; 
                border-bottom: 1px solid #2d3343; 
                font-weight: bold; 
                font-size: 10px; 
                text-transform: uppercase; 
                letter-spacing: 1px;
            }
            QTableWidget::item { 
                padding: 5px 12px; 
                border-bottom: 1px solid #1f2330; 
            }
            
            QCheckBox { color: #d1d5db; font-size: 12px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #2d3343; background: #1a1d27; }
            QCheckBox::indicator:checked { background: #ff5e00; border-color: #ff5e00; }
            
            QSlider::groove:horizontal { border: none; height: 4px; background: #2d3343; border-radius: 2px; }
            QSlider::handle:horizontal { background: #e0e0e0; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
            QSlider::sub-page:horizontal { background: #ff5e00; border-radius: 2px; }
            
            QProgressBar { border: none; background-color: #2d3343; border-radius: 3px; max-height: 6px; text-align: center; color: transparent; }
            QProgressBar::chunk { background-color: #00e5ff; border-radius: 3px; }
            
            QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 0; }
            QScrollBar::handle:vertical { background: #2d3343; min-height: 20px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #4a5568; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # HEADER
        header_layout = QHBoxLayout()
        
        # Logo + Title
        logo_label = QLabel("◎")
        logo_label.setStyleSheet("color: #5b8bb5; font-size: 24px;")
        title_label = QLabel("NetPulse")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        author_label = QLabel("Created by Wyrchik")
        author_label.setStyleSheet("font-size: 10px; color: #6b7280; padding-top: 6px;")
        
        left_header = QHBoxLayout()
        left_header.addWidget(logo_label)
        left_header.addWidget(title_label)
        left_header.addWidget(author_label)
        left_header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        header_layout.addLayout(left_header)
        header_layout.addStretch()
        
        # Right Controls
        right_header = QVBoxLayout()
        right_header.setSpacing(10)
        
        top_controls = QHBoxLayout()
        self.ip_start = QLineEdit()
        self.ip_start.setFixedWidth(120)
        self.ip_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_end = QLineEdit()
        self.ip_end.setFixedWidth(120)
        self.ip_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        to_label = QLabel("to")
        to_label.setStyleSheet("color: #6b7280;")
        
        self.btn_scan = QPushButton("SCAN")
        self.btn_scan.setObjectName("btnScan")
        self.btn_scan.setFixedWidth(80)
        self.btn_stop = QPushButton("■ STOP")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setEnabled(False)
        
        top_controls.addWidget(self.ip_start)
        top_controls.addWidget(to_label)
        top_controls.addWidget(self.ip_end)
        top_controls.addWidget(self.btn_scan)
        top_controls.addWidget(self.btn_stop)
        
        bottom_controls = QHBoxLayout()
        ports_label = QLabel("Ports:")
        ports_label.setStyleSheet("color: #6b7280;")
        self.ports_input = QLineEdit("80,443,22")
        self.ports_input.setFixedWidth(150)
        
        intensity_label = QLabel("Intensity:")
        intensity_label.setStyleSheet("color: #6b7280;")
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(10, 1000)
        self.intensity_slider.setValue(200)
        self.intensity_slider.setFixedWidth(100)
        self.intensity_val = QLabel("200")
        self.intensity_slider.valueChanged.connect(lambda v: self.intensity_val.setText(str(v)))
        
        bottom_controls.addStretch()
        bottom_controls.addWidget(ports_label)
        bottom_controls.addWidget(self.ports_input)
        bottom_controls.addSpacing(15)
        bottom_controls.addWidget(intensity_label)
        bottom_controls.addWidget(self.intensity_slider)
        bottom_controls.addWidget(self.intensity_val)
        
        right_header.addLayout(top_controls)
        right_header.addLayout(bottom_controls)
        right_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addLayout(right_header)
        main_layout.addLayout(header_layout)

        # TOOLBAR
        toolbar_layout = QHBoxLayout()
        self.cb_online_only = QCheckBox("Show only Online")
        self.cb_online_only.setChecked(True)
        
        self.btn_delete_offline = QPushButton("🗑 Delete All Offline")
        self.btn_export = QPushButton("⬇ Export (CSV)")
        
        toolbar_layout.addWidget(self.cb_online_only)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_delete_offline)
        toolbar_layout.addWidget(self.btn_export)
        
        main_layout.addLayout(toolbar_layout)

        # TABLE
        self.table = QTableWidget(0, 9)
        headers = ["STATUS", "DEVICE NAME", "IP ADDRESS", "OS", "LATENCY", "MAC ADDRESS", "MANUFACTURER", "PORTS & SERVICES", "TOOLS"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        main_layout.addWidget(self.table)

        # FOOTER
        footer_layout = QHBoxLayout()
        self.lbl_found = QLabel("Found: 0 Devices")
        self.lbl_found.setStyleSheet("color: #8b92a5; font-size: 11px;")
        
        self.lbl_speed = QLabel("Scan speed: 0 IPs/s")
        self.lbl_speed.setStyleSheet("color: #8b92a5; font-size: 11px;")
        
        lbl_prog = QLabel("Progress:")
        lbl_prog.setStyleSheet("color: #8b92a5; font-size: 11px;")
        
        self.progress = QProgressBar()
        self.progress.setFixedWidth(150)
        self.progress.setValue(0)
        
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet("color: #8b92a5; font-size: 11px;")
        
        footer_layout.addWidget(self.lbl_found)
        footer_layout.addWidget(QLabel("|", styleSheet="color: #4a5568;"))
        footer_layout.addWidget(self.lbl_speed)
        footer_layout.addWidget(QLabel("|", styleSheet="color: #4a5568;"))
        footer_layout.addWidget(lbl_prog)
        footer_layout.addWidget(self.progress)
        footer_layout.addWidget(self.lbl_pct)
        footer_layout.addStretch()
        
        main_layout.addLayout(footer_layout)

        # Internal state
        self.worker = None
        self.total_ips = 0
        self.scanned_ips = 0
        self.found_devices = 0
        
        self.btn_scan.clicked.connect(self.toggle_scan)
        self.btn_stop.clicked.connect(self.stop_scan)
        self.prefill_ips()

    def prefill_ips(self):
        local_ip = get_local_ip()
        try:
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            self.ip_start.setText(str(network.network_address + 1))
            self.ip_end.setText(str(network.broadcast_address - 1))
        except:
            self.ip_start.setText(local_ip)
            self.ip_end.setText(local_ip)

    def toggle_scan(self):
        start_ip = self.ip_start.text()
        end_ip = self.ip_end.text()
        ports_str = self.ports_input.text()
        speed = self.intensity_slider.value()

        try:
            start_addr = ipaddress.IPv4Address(start_ip)
            end_addr = ipaddress.IPv4Address(end_ip)
            if start_addr > end_addr: raise ValueError("Start IP must be <= End IP")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start_addr), int(end_addr) + 1)]
        ports = []
        if ports_str:
            for p in ports_str.split(','):
                try: ports.append(int(p.strip()))
                except: pass

        self.table.setRowCount(0)
        self.total_ips = len(ip_list)
        self.scanned_ips = 0
        self.found_devices = 0
        self.progress.setMaximum(self.total_ips)
        self.progress.setValue(0)
        self.lbl_pct.setText("0%")
        self.lbl_found.setText("Found: 0 Devices")

        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)

        local_ip = get_local_ip()
        self.worker = ScanWorker(ip_list, speed, ports, local_ip)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.found_signal.connect(self.on_found)
        self.worker.done_signal.connect(self.on_done)
        self.worker.start()

    def on_progress(self):
        self.scanned_ips += 1
        self.progress.setValue(self.scanned_ips)
        pct = int((self.scanned_ips / self.total_ips) * 100) if self.total_ips else 0
        self.lbl_pct.setText(f"{pct}%")

    def on_found(self, device):
        self.found_devices += 1
        self.lbl_found.setText(f"Found: {self.found_devices} Devices")
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # STATUS
        status_item = QTableWidgetItem("● Online")
        status_item.setForeground(Qt.GlobalColor.green)
        self.table.setItem(row, 0, status_item)
        
        # DEVICE NAME
        hostname = device.get('hostname', '')
        if hostname == "Unknown Device": hostname = ""
        self.table.setItem(row, 1, QTableWidgetItem(hostname))
        
        # IP ADDRESS
        ip_item = QTableWidgetItem(device['ip'])
        ip_item.setForeground(Qt.GlobalColor.cyan)
        self.table.setItem(row, 2, ip_item)
        
        # OS
        self.table.setItem(row, 3, QTableWidgetItem(device.get('os', '')))
        
        # LATENCY
        lat = device.get('latency', 0)
        lat_item = QTableWidgetItem(f"{lat:.1f} ms")
        if lat < 10: lat_item.setForeground(Qt.GlobalColor.green)
        elif lat < 100: lat_item.setForeground(Qt.GlobalColor.yellow)
        else: lat_item.setForeground(Qt.GlobalColor.red)
        self.table.setItem(row, 4, lat_item)
        
        # MAC ADDRESS
        mac = device.get('mac', '')
        if mac == "Unknown": mac = ""
        self.table.setItem(row, 5, QTableWidgetItem(mac))
        
        # MANUFACTURER (Placeholder for now)
        self.table.setItem(row, 6, QTableWidgetItem(""))
        
        # PORTS
        ports_str = ", ".join([str(p['port']) for p in device.get('ports', [])])
        self.table.setItem(row, 7, QTableWidgetItem(ports_str))
        
        # TOOLS
        self.table.setItem(row, 8, QTableWidgetItem(""))

    def on_done(self):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setValue(self.total_ips)
        self.lbl_pct.setText("100%")

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
        self.on_done()
