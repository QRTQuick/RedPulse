import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import psutil
import subprocess
import threading
import time
import os
import sys
import requests
import tempfile
import shutil

# -------------------------
# CONFIG
# -------------------------
CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/YourGitHub/RedPulse/version.txt"
EXE_URL = "https://raw.githubusercontent.com/YourGitHub/RedPulse/RedPulse.exe"
RELEASE_NOTE_URL = "https://raw.githubusercontent.com/YourGitHub/RedPulse/main/release note"
CHECK_INTERVAL = 1  # seconds

# -------------------------
# COLORS & STYLES
# -------------------------
BG_COLOR = "#000000"
FG_COLOR = "#FF3333"
BTN_BG = "#FF3333"
BTN_FG = "white"
TAB_BG = "#111111"
TAB_FG = "white"
FONT_MAIN = ("Roboto", 12)
FONT_TITLE = ("Roboto", 14, "bold")
PROGRESS_COLOR = "#FF4444"

# -------------------------
# AUTO-UPDATE
# -------------------------
def check_update():
    try:
        online_version = requests.get(UPDATE_URL).text.strip()
        return online_version != CURRENT_VERSION, online_version
    except:
        return False, CURRENT_VERSION

def auto_update():
    try:
        r = requests.get(EXE_URL)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "RedPulse_new.exe")
        with open(temp_path, "wb") as f:
            f.write(r.content)
        current_exe = sys.executable
        backup_path = current_exe + ".bak"
        shutil.move(current_exe, backup_path)
        shutil.move(temp_path, current_exe)
        subprocess.Popen([current_exe])
        sys.exit()
    except Exception as e:
        messagebox.showerror("Update Error", f"Auto-update failed: {e}")

# -------------------------
# MAIN APP
# -------------------------
class RedPulseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RedPulse Pro - Quick Red Tech")
        self.geometry("780x520")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self.proc = None
        self.monitoring = False
        self.history_files = []

        # -------------------------
        # MENU BAR
        # -------------------------
        self.menu_bar = tk.Menu(self, bg=TAB_BG, fg=TAB_FG)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=TAB_BG, fg=TAB_FG)
        file_menu.add_command(label="Run File/EXE", command=self.run_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=TAB_BG, fg=TAB_FG)
        help_menu.add_command(label="About RedPulse", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # -------------------------
        # TAB VIEW
        # -------------------------
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
        style.configure('TNotebook.Tab', background=TAB_BG, foreground=TAB_FG, font=("Roboto", 12, "bold"))
        style.map("TNotebook.Tab", background=[("selected", BG_COLOR)], foreground=[("selected", FG_COLOR)])
        style.configure('TProgressbar', thickness=20, troughcolor="#333333", background=PROGRESS_COLOR)

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both", padx=10, pady=10)

        self.main_tab = tk.Frame(self.tab_control, bg=BG_COLOR)
        self.update_tab = tk.Frame(self.tab_control, bg=BG_COLOR)
        self.settings_tab = tk.Frame(self.tab_control, bg=BG_COLOR)
        self.about_tab = tk.Frame(self.tab_control, bg=BG_COLOR)
        self.release_tab = tk.Frame(self.tab_control, bg=BG_COLOR)

        self.tab_control.add(self.main_tab, text="Main Function")
        self.tab_control.add(self.update_tab, text="App Update")
        self.tab_control.add(self.settings_tab, text="Settings")
        self.tab_control.add(self.about_tab, text="About & History")
        self.tab_control.add(self.release_tab, text="Release Notes")

        # -------------------------
        # MAIN FUNCTION TAB
        # -------------------------
        self.label_script = tk.Label(self.main_tab, text="No process running", font=FONT_TITLE, fg=FG_COLOR, bg=BG_COLOR)
        self.label_script.pack(pady=(20, 10))

        btn_frame = tk.Frame(self.main_tab, bg=BG_COLOR)
        btn_frame.pack(pady=15)

        self.btn_run = tk.Button(btn_frame, text="Run File / EXE", command=self.run_file,
                                 bg=BTN_BG, fg=BTN_FG, font=("Roboto", 13, "bold"),
                                 relief="flat", width=20, height=2, cursor="hand2")
        self.btn_run.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="Stop", command=self.stop_file, state="disabled",
                                  bg=BTN_BG, fg=BTN_FG, font=("Roboto", 13, "bold"),
                                  relief="flat", width=20, height=2, cursor="hand2")
        self.btn_stop.grid(row=0, column=1, padx=10)

        cpu_frame = tk.Frame(self.main_tab, bg="#111111", bd=1, relief="ridge")
        cpu_frame.pack(pady=8, fill="x", padx=20)
        self.cpu_label = tk.Label(cpu_frame, text="CPU: 0%", font=FONT_MAIN, fg=FG_COLOR, bg="#111111")
        self.cpu_label.pack(anchor="w", padx=10, pady=2)
        self.cpu_bar = ttk.Progressbar(cpu_frame, length=700, mode="determinate")
        self.cpu_bar.pack(padx=10, pady=5)

        mem_frame = tk.Frame(self.main_tab, bg="#111111", bd=1, relief="ridge")
        mem_frame.pack(pady=8, fill="x", padx=20)
        self.mem_label = tk.Label(mem_frame, text="Memory: 0 MB", font=FONT_MAIN, fg=FG_COLOR, bg="#111111")
        self.mem_label.pack(anchor="w", padx=10, pady=2)
        self.mem_bar = ttk.Progressbar(mem_frame, length=700, mode="determinate")
        self.mem_bar.pack(padx=10, pady=5)

        self.time_label = tk.Label(self.main_tab, text="Runtime: 0s", font=FONT_MAIN, fg=FG_COLOR, bg=BG_COLOR)
        self.time_label.pack(pady=10)

        # -------------------------
        # APP UPDATE TAB
        # -------------------------
        self.version_label = tk.Label(self.update_tab, text=f"Current Version: {CURRENT_VERSION}", font=FONT_MAIN, fg=FG_COLOR, bg=BG_COLOR)
        self.version_label.pack(pady=(20, 10))
        self.btn_update = tk.Button(self.update_tab, text="Check for Update", command=self.manual_update,
                                    bg=BTN_BG, fg=BTN_FG, font=FONT_MAIN, relief="flat", width=25, height=2, cursor="hand2")
        self.btn_update.pack(pady=10)
        self.update_progress = ttk.Progressbar(self.update_tab, length=550, mode="indeterminate")
        self.update_progress.pack(pady=10)

        # -------------------------
        # SETTINGS TAB
        # -------------------------
        settings_text = (
            "⚙️ RedPulse Settings & History\n\n"
            "Recent Files Opened:\n- None yet\n\n"
            "Shortcut Keys:\n- Run File/EXE: Ctrl+R\n- Stop Process: Ctrl+S\n- Check Update: Ctrl+U\n\n"
            "History:\n- No updates run yet\n\n"
            "Appearance:\n- Dark mode (black background)\n\n"
            "Paths:\n- Default Python path: System default\n- Default EXE path: None\n\n"
            "Notes:\n- Settings customization coming soon..."
        )
        self.settings_textbox = scrolledtext.ScrolledText(self.settings_tab, width=90, height=28,
                                                          font=FONT_MAIN, bg=BG_COLOR, fg=FG_COLOR, relief="flat", borderwidth=0)
        self.settings_textbox.insert(tk.END, settings_text)
        self.settings_textbox.config(state="disabled")
        self.settings_textbox.pack(pady=10, padx=10)

        # -------------------------
        # ABOUT & HISTORY TAB
        # -------------------------
        about_text = (
            "🔴 RedPulse Pro v1.0.0 by Quick Red Tech\n\n"
            "Your ultimate developer utility tool.\n\n"
            "Quick Red Tech previously developed successful tools:\n"
            "1. RedMaxima — intelligent desktop assistant\n"
            "2. RedQuota — resource monitoring utility\n\n"
            "RedPulse Pro is the refined product after learning from past experiences.\n\n"
            "Shortcut Keys:\n- Run File/EXE: Ctrl+R\n- Stop Process: Ctrl+S\n\n"
            "How to use:\n1. Go to Main Function tab\n2. Click 'Run File / EXE'\n3. Monitor CPU/Memory and runtime"
        )
        self.about_textbox = scrolledtext.ScrolledText(self.about_tab, width=90, height=28,
                                                       font=FONT_MAIN, bg=BG_COLOR, fg=FG_COLOR, relief="flat", borderwidth=0)
        self.about_textbox.insert(tk.END, about_text)
        self.about_textbox.config(state="disabled")
        self.about_textbox.pack(pady=10, padx=10)

        # -------------------------
        # RELEASE NOTES TAB
        # -------------------------
        self.release_textbox = scrolledtext.ScrolledText(self.release_tab, width=90, height=28,
                                                         font=FONT_MAIN, bg=BG_COLOR, fg=FG_COLOR, relief="flat", borderwidth=0)
        self.release_textbox.pack(pady=10, padx=10)

        def load_release_notes():
            try:
                r = requests.get(RELEASE_NOTE_URL)
                if r.status_code == 200:
                    self.release_textbox.insert(tk.END, r.text)
                else:
                    self.release_textbox.insert(tk.END, "Failed to load release notes.")
            except Exception as e:
                self.release_textbox.insert(tk.END, f"Error: {e}")
            self.release_textbox.config(state="disabled")

        load_release_notes()

        # -------------------------
        # START THREADS & SHORTCUTS
        # -------------------------
        threading.Thread(target=self.update_checker, daemon=True).start()
        self.bind_all("<Control-r>", lambda e: self.run_file())
        self.bind_all("<Control-s>", lambda e: self.stop_file())

        for btn in [self.btn_run, self.btn_stop, self.btn_update]:
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#FF5555"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BTN_BG))

    # -------------------------
    # RUN FILE / EXE
    # -------------------------
    def run_file(self):
        if self.monitoring:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
        if not file_path:
            return

        self.label_script.config(text=f"Running: {os.path.basename(file_path)}")
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.history_files.append(os.path.basename(file_path))

        try:
            if file_path.endswith(".py"):
                self.proc = subprocess.Popen([sys.executable, file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                self.proc = subprocess.Popen([file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.monitoring = True
            threading.Thread(target=self.monitor_process, daemon=True).start()
            threading.Thread(target=self.check_errors, daemon=True).start()
        except Exception as e:
            self.show_error(e)
            self.stop_file()

    def stop_file(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        self.proc = None
        self.monitoring = False
        self.label_script.config(text="Process stopped")
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.cpu_bar["value"] = 0
        self.mem_bar["value"] = 0
        self.cpu_label.config(text="CPU: 0%")
        self.mem_label.config(text="Memory: 0 MB")
        self.time_label.config(text="Runtime: 0s")

    # -------------------------
    # MONITOR CPU/MEMORY/RUNTIME
    # -------------------------
    def monitor_process(self):
        start_time = time.time()
        while self.proc and self.proc.poll() is None:
            try:
                p = psutil.Process(self.proc.pid)
                cpu = p.cpu_percent(interval=0.1)
                mem = p.memory_info().rss / (1024*1024)
                runtime = int(time.time() - start_time)

                self.cpu_label.config(text=f"CPU: {cpu:.1f}%")
                self.cpu_bar["value"] = min(cpu, 100)
                self.mem_label.config(text=f"Memory: {mem:.1f} MB")
                self.mem_bar["value"] = min(mem/500*100, 100)
                self.time_label.config(text=f"Runtime: {runtime}s")
                time.sleep(CHECK_INTERVAL)
            except psutil.NoSuchProcess:
                break

        self.monitoring = False
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")

    # -------------------------
    # CHECK ERRORS
    # -------------------------
    def check_errors(self):
        if not self.proc:
            return
        try:
            stdout, stderr = self.proc.communicate()
            if stderr:
                self.show_error(stderr.decode())
        except Exception as e:
            self.show_error(str(e))

    # -------------------------
    # SHOW ERROR
    # -------------------------
    def show_error(self, text):
        messagebox.showerror("Error Occurred", str(text))

    # -------------------------
    # MANUAL UPDATE
    # -------------------------
    def manual_update(self):
        self.update_progress.start()
        def run_check():
            has_update, online_ver = check_update()
            self.update_progress.stop()
            if has_update:
                if messagebox.askyesno("Update Available", f"Version {online_ver} available. Update now?"):
                    auto_update()
            else:
                messagebox.showinfo("Update", "You are on the latest version.")
        threading.Thread(target=run_check, daemon=True).start()

    # -------------------------
    # AUTO UPDATE CHECKER
    # -------------------------
    def update_checker(self):
        time.sleep(2)
        has_update, online_ver = check_update()
        if has_update:
            if messagebox.askyesno("Update Available", f"Version {online_ver} available. Update now?"):
                auto_update()

    # -------------------------
    # SHOW ABOUT POPUP
    # -------------------------
    def show_about(self):
        messagebox.showinfo("About RedPulse Pro",
            "RedPulse Pro v1.0.0\n"
            "Quick Red Tech\n"
            "Developer Utility Tool\n\n"
            "Previous Tools:\n"
            "1. RedMaxima — intelligent desktop assistant\n"
            "2. RedQuota — resource monitoring utility\n\n"
            "RedPulse Pro is the refined product after learning from past experiences."
        )

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app = RedPulseApp()
    app.mainloop()