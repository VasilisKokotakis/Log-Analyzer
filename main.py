#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import json
from collections import defaultdict
from pathlib import Path
import threading
import subprocess
import sys

CONNECTORS_DIR = Path(__file__).parent / "connectors"


def load_connectors():
    connectors = {}
    if CONNECTORS_DIR.exists():
        for f in sorted(CONNECTORS_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                connectors[data["name"]] = data
            except Exception:
                pass
    return connectors


class LogAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Analyzer")
        self.root.geometry("750x800")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")

        self.connectors = load_connectors()
        self.log_file = None
        self.output_path = None

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 20, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Arial', 12), foreground='#7f8c8d')
        style.configure('Custom.TButton', font=('Arial', 11, 'bold'), padding=10)

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#3498db", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="Log Analyzer",
                 font=("Arial", 24, "bold"), bg="#3498db", fg="white").pack(expand=True)

        # Main content
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=40, pady=15)

        # Connector section
        connector_section = tk.LabelFrame(main_frame, text="Connector",
                                          font=("Arial", 12, "bold"),
                                          bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        connector_section.pack(fill="x", pady=(0, 20))

        self.connector_var = tk.StringVar()
        connector_names = list(self.connectors.keys())

        if connector_names:
            self.connector_var.set(connector_names[0])
        else:
            self.connector_var.set("No connectors found")

        ttk.Combobox(connector_section,
                     textvariable=self.connector_var,
                     values=connector_names,
                     state="readonly",
                     font=("Arial", 11)).pack(fill="x", pady=(10, 5))

        # Log file section
        log_section = tk.LabelFrame(main_frame, text="Log File",
                                    font=("Arial", 12, "bold"),
                                    bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        log_section.pack(fill="x", pady=(0, 20))

        self.log_entry = tk.Entry(log_section, font=("Arial", 11))
        self.log_entry.pack(fill="x", pady=(10, 10))

        tk.Button(log_section, text="Browse Log File",
                  command=self.browse_log, bg="#3498db", fg="white",
                  font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8,
                  cursor="hand2").pack(side="left", padx=(0, 10))

        # Output section
        output_section = tk.LabelFrame(main_frame, text="Output Report",
                                       font=("Arial", 12, "bold"),
                                       bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        output_section.pack(fill="x", pady=(0, 20))

        output_frame = tk.Frame(output_section, bg="#f8f9fa")
        output_frame.pack(fill="x", pady=(10, 5))

        tk.Label(output_frame, text="Filename:", font=("Arial", 10, "bold"),
                 bg="#f8f9fa").pack(side="left")
        self.output_entry = tk.Entry(output_frame, font=("Arial", 11), width=20)
        self.output_entry.insert(0, "failure_report.txt")
        self.output_entry.pack(side="left", padx=(10, 0))
        tk.Label(output_frame, text=" (saved next to log file)",
                 font=("Arial", 9), bg="#f8f9fa", fg="#7f8c8d").pack(side="left", padx=(10, 0))

        # Stats preview
        self.stats_frame = tk.LabelFrame(main_frame, text="Quick Stats Preview",
                                         font=("Arial", 12, "bold"),
                                         bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        self.stats_frame.pack(fill="x", pady=(0, 20))

        self.stats_label = tk.Label(self.stats_frame, text="Select a log file to see stats...",
                                    font=("Arial", 11), bg="#f8f9fa", fg="#95a5a6")
        self.stats_label.pack(pady=10)

        # Generate button
        self.generate_btn = tk.Button(main_frame, text="GENERATE REPORT",
                                      font=("Arial", 14, "bold"),
                                      bg="#27ae60", fg="white", height=2,
                                      relief="flat", cursor="hand2",
                                      command=self.start_analysis)
        self.generate_btn.pack(fill="x", pady=(20, 5))

        self.open_folder_btn = tk.Button(main_frame, text="Open Report Folder",
                                         font=("Arial", 11),
                                         bg="#ecf0f1", fg="#bdc3c7", height=1,
                                         relief="flat", cursor="arrow",
                                         state="disabled",
                                         command=self.open_report_folder)
        self.open_folder_btn.pack(fill="x", pady=(0, 10))

        # Progress
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=5)

        self.status_label = tk.Label(main_frame, text="Ready to analyze!",
                                     font=("Arial", 11, "bold"), bg="#f8f9fa", fg="#27ae60")
        self.status_label.pack(pady=10)

    def browse_log(self):
        filename = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")]
        )
        if filename:
            self.log_entry.delete(0, tk.END)
            self.log_entry.insert(0, filename)
            self.update_stats_preview(filename)

    def update_stats_preview(self, log_path):
        try:
            log_file = Path(log_path)
            size_mb = log_file.stat().st_size / 1024 / 1024
            self.stats_label.config(
                text=f"{log_file.name}   |   {size_mb:.1f} MB",
                fg="#2c3e50"
            )
        except Exception as e:
            self.stats_label.config(text=f"Could not read file: {e}", fg="#e74c3c")

    def get_current_connector(self):
        return self.connectors.get(self.connector_var.get())

    def start_analysis(self):
        connector = self.get_current_connector()
        log_path = self.log_entry.get().strip()
        output_name = self.output_entry.get().strip()

        if not connector:
            messagebox.showerror("Error", "Please select a valid connector!")
            return
        if not log_path or not Path(log_path).exists():
            messagebox.showerror("Error", "Please select a valid log file!")
            return
        if not output_name:
            messagebox.showerror("Error", "Please enter an output filename!")
            return

        self.log_file = Path(log_path)
        self.output_path = self.log_file.parent / output_name

        self.generate_btn.config(state="disabled", text="ANALYZING...")
        self.open_folder_btn.config(state="disabled", fg="#bdc3c7", cursor="arrow")
        self.progress.start(10)
        self.status_label.config(text="Analyzing log file...", fg="#f39c12")

        thread = threading.Thread(target=self.analyze_logs, args=(connector,), daemon=True)
        thread.start()

    def analyze_logs(self, connector):
        try:
            request_stats, path_stats = self.parse_logs(connector)
            self.generate_report(connector, request_stats, path_stats)
            self.root.after(0, self.analysis_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analysis Failed", f"Error:\n{str(e)}"))
            self.root.after(0, self.reset_ui)

    def parse_logs(self, connector):
        request_stats = defaultdict(int)
        path_stats = defaultdict(int)

        compiled_patterns = []
        for p in connector.get("request_patterns", []):
            compiled_patterns.append({
                "regex": re.compile(p["regex"]),
                "has_json_body": p.get("has_json_body", False),
                "body_fields": p.get("body_fields", ["message"]),
            })

        path_pattern_str = connector.get("path_pattern")
        path_regex = re.compile(path_pattern_str) if path_pattern_str else None
        path_depth = connector.get("path_depth", 2)

        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                matched = False

                for p in compiled_patterns:
                    m = p["regex"].search(line)
                    if not m:
                        continue

                    groups = m.groupdict()
                    endpoint = groups.get("endpoint", "unknown")
                    error_type = groups.get("error_type", "unknown")
                    code = groups.get("code", "unknown")

                    if p["has_json_body"] and "body_json" in groups:
                        message = self._extract_message(groups["body_json"], p["body_fields"])
                    else:
                        message = "No message"

                    request_stats[(endpoint, error_type, code, message)] += 1
                    matched = True
                    break

                if not matched and path_regex:
                    pm = path_regex.search(line)
                    if pm:
                        parts = [seg for seg in pm.group(1).split('/') if seg]
                        root = "/".join(parts[:path_depth])
                        path_stats[root] += 1

        return request_stats, path_stats

    def _extract_message(self, body_json, fields):
        try:
            data = json.loads(body_json.strip())
            for field in fields:
                val = data.get(field)
                if isinstance(val, list):
                    val = val[0] if val else None
                if val:
                    return str(val)
        except (json.JSONDecodeError, ValueError):
            return "Parse error"
        return "No message"

    def generate_report(self, connector, request_stats, path_stats):
        cfg = connector.get("report", {})
        title = cfg.get("title", "FAILURE ANALYSIS REPORT")
        requests_section = cfg.get("requests_section", "REQUEST FAILURE SUMMARY")
        paths_section = cfg.get("paths_section", "PATH FAILURE SUMMARY")

        lines = [title, "=" * 60, ""]

        if request_stats:
            lines += [requests_section, "-" * 60, ""]
            per_endpoint = defaultdict(list)
            for (endpoint, err_type, code, msg), count in request_stats.items():
                per_endpoint[endpoint].append((err_type, code, msg, count))

            for endpoint, entries in sorted(per_endpoint.items()):
                total = sum(c for _, _, _, c in entries)
                err_type, code, msg, _ = max(entries, key=lambda x: x[3])
                line = f"{endpoint} - failed {total} times - with ({err_type}) - {code}"
                if msg not in ("No message", "Parse error"):
                    line += f' - "{msg}"'
                lines.append(line)
            lines.append("")

        if path_stats:
            lines += [paths_section, "-" * 60, ""]
            for path, count in sorted(path_stats.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"{path} failed {count} times")

        self.output_path.write_text("\n".join(lines), encoding='utf-8')

    def analysis_complete(self):
        messagebox.showinfo("Success", f"Report saved to:\n{self.output_path}")
        self.open_folder_btn.config(state="normal", fg="#2c3e50", cursor="hand2")
        self.reset_ui()

    def open_report_folder(self):
        folder = str(self.output_path.parent)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", folder])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def reset_ui(self):
        self.generate_btn.config(state="normal", text="GENERATE REPORT")
        self.progress.stop()
        self.status_label.config(text="Ready to analyze!", fg="#27ae60")


if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerGUI(root)
    root.mainloop()
