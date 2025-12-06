#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import json
from collections import defaultdict
from pathlib import Path
import threading

class LogAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Analyzer")
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")
        
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
        
        title = tk.Label(header_frame, text="Log Analyzer for DSL team", 
                        font=("Arial", 24, "bold"), bg="#3498db", fg="white")
        title.pack(expand=True)

        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Log file section
        log_section = tk.LabelFrame(main_frame, text="📁 Log File", 
                                   font=("Arial", 12, "bold"), 
                                   bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        log_section.pack(fill="x", pady=(0, 20))
        
        self.log_entry = tk.Entry(log_section, font=("Arial", 11))
        self.log_entry.pack(fill="x", pady=(10, 10))
        
        log_btn_frame = tk.Frame(log_section, bg="#f8f9fa")
        log_btn_frame.pack(fill="x")
        tk.Button(log_btn_frame, text="Browse Log File", 
                 command=self.browse_log, bg="#3498db", fg="white", 
                 font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8,
                 cursor="hand2").pack(side="left", padx=(0, 10))
        
        # Output section
        output_section = tk.LabelFrame(main_frame, text="💾 Output Report", 
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
        self.stats_frame = tk.LabelFrame(main_frame, text="📊 Quick Stats Preview", 
                                        font=("Arial", 12, "bold"), 
                                        bg="#f8f9fa", fg="#2c3e50", padx=20, pady=15)
        self.stats_frame.pack(fill="x", pady=(0, 20))
        
        self.stats_label = tk.Label(self.stats_frame, text="Select a log file to see stats...", 
                                   font=("Arial", 11), bg="#f8f9fa", fg="#95a5a6")
        self.stats_label.pack(pady=10)
        
        # Action buttons
        btn_frame = tk.Frame(main_frame, bg="#f8f9fa")
        btn_frame.pack(pady=20)
        
        self.generate_btn = tk.Button(btn_frame, text="GENERATE REPORT", 
                                     font=("Arial", 14, "bold"), 
                                     bg="#27ae60", fg="white", height=2, 
                                     relief="flat", padx=40, cursor="hand2",
                                     command=self.start_analysis)
        self.generate_btn.pack(pady=10)
        
        # Progress
        self.progress_frame = tk.Frame(main_frame, bg="#f8f9fa")
        self.progress_frame.pack(fill="x", pady=10)
        self.progress = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=5)
        
        self.status_label = tk.Label(main_frame, text="✅ Ready to analyze your Jira logs!", 
                                    font=("Arial", 11, "bold"), bg="#f8f9fa", fg="#27ae60")
        self.status_label.pack(pady=10)

    
    def browse_log(self):
        filename = filedialog.askopenfilename(
            title="Select Jira Log File",
            filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")]
        )
        if filename:
            self.log_entry.delete(0, tk.END)
            self.log_entry.insert(0, filename)
            self.update_stats_preview(filename)
    
    def update_stats_preview(self, log_path):
        try:
            log_file = Path(log_path)
            if not log_file.exists():
                return
            size_mb = log_file.stat().st_size / 1024 / 1024
            self.stats_label.config(text=f"📄 {log_file.name}\n💾 Size: {size_mb:.1f} MB")
        except:
            pass
    
    def start_analysis(self):
        log_path = self.log_entry.get().strip()
        output_name = self.output_entry.get().strip()
        
        if not log_path or not Path(log_path).exists():
            messagebox.showerror("Error", "Please select a valid log file!")
            return
        
        if not output_name:
            messagebox.showerror("Error", "Please enter output filename!")
            return
        
        self.log_file = Path(log_path)
        output_dir = self.log_file.parent
        self.output_path = output_dir / output_name
        
        self.generate_btn.config(state="disabled", text="ANALYZING...")
        self.progress.start(10)
        self.status_label.config(text="Analyzing log file...", fg="#f39c12")
        
        thread = threading.Thread(target=self.analyze_logs)
        thread.daemon = True
        thread.start()
    
    def analyze_logs(self):
        try:
            request_stats, folder_stats = self.parse_logs()
            self.generate_report(request_stats, folder_stats)
            self.root.after(0, self.analysis_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("❌ Analysis Failed", f"Error:\n{str(e)}"))
            self.root.after(0, self.reset_ui)
    
    def parse_logs(self):
        request_stats = defaultdict(int)
        folder_stats = defaultdict(int)

        request_regex_with_body = re.compile(
            r'/request:\s*([^:\s]+):\s*(Recoverable fail|Unrecoverable fail)'
            r'\[[^\]]*\](?:\[[^\]]*\])*\{CODE:(\d+)\}.*Body:\s*(\{.*?\})(?=\s*$|\s+Wed|\s+Nov|\s+\[|$)',
            re.DOTALL
        )
        
        request_regex_no_body = re.compile(
            r'/request:\s*([^:\s]+):\s*(Recoverable fail|Unrecoverable fail)'
            r'\[[^\]]*\](?:\[[^\]]*\])*\{CODE:(\d+)\}'
        )

        folder_regex = re.compile(
            r'Failed to get folder content:\s*(/[^.]+?)(?:\. Cause:|$)'
        )

        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = request_regex_with_body.search(line)
                if m:
                    request_name, error_type, code, body_json = m.groups()
                    try:
                        data = json.loads(body_json.strip())
                        message = data.get('message') or \
                                 (data.get('errorMessages', [None])[0] if data.get('errorMessages') else None) or \
                                 'No message'
                    except:
                        message = 'Parse error'
                else:
                    m = request_regex_no_body.search(line)
                    if m:
                        request_name, error_type, code = m.groups()
                        message = 'No message'
                    else:
                        fm = folder_regex.search(line)
                        if fm:
                            full_path = fm.group(1)
                            parts = [p for p in full_path.split('/') if p]
                            if len(parts) >= 2:
                                root = f"{parts[0]}/{parts[1]}"
                            else:
                                root = parts[0]
                            folder_stats[root] += 1
                        continue
                
                key = (request_name, error_type, code, message)
                request_stats[key] += 1

        return request_stats, folder_stats
    
    def generate_report(self, request_stats, folder_stats):
        lines = []
        lines.append("FAILURE ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")

        per_request = defaultdict(list)
        for (req, err_type, code, msg), count in request_stats.items():
            per_request[req].append((err_type, code, msg, count))

        for req_name, entries in sorted(per_request.items()):
            total = sum(c for _, _, _, c in entries)
            err_type, code, msg, _ = max(entries, key=lambda x: x[3])
            line = f"{req_name} - failed {total} times - with ({err_type}) - {code}"
            if msg != 'No message':
                line += f" - \"{msg}\""
            lines.append(line)

        lines.append("")
        lines.append("FOLDER/ENTITY FAILURE SUMMARY")
        lines.append("=" * 60)
        lines.append("")

        for folder, count in sorted(folder_stats.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"{folder} failed {count} times")

        self.output_path.write_text("\n".join(lines), encoding='utf-8')
    
    def analysis_complete(self):
        messagebox.showinfo("SUCCESS! ✅", 
                           f"Report generated successfully!\n\n📄 Saved to:\n{self.output_path}\n\n")
        self.reset_ui()
    
    def reset_ui(self):
        self.generate_btn.config(state="normal", text="GENERATE REPORT")
        self.progress.stop()
        self.status_label.config(text="Ready to analyze your Jira logs!", fg="#27ae60")

if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerGUI(root)
    root.mainloop()
