import os
import subprocess
import threading
import json
import shlex
import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import customtkinter as ctk

# -------------------------
# CONFIG
# -------------------------

MAIN_DIR = r""
LOG_PATH = os.path.join("Logs", "Tool.log")
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUPS = 5
SAFE_COMMANDS = (
    "adb devices","adb version","adb help","adb start-server","adb kill-server","adb get-state","adb reconnect","adb usb","adb reboot","adb reboot recovery",
    "fastboot devices","fastboot version","fastboot help","fastboot reboot","fastboot reboot recovery",
)
SAFE_PREFIXES = (
    "fastboot getvar","fastboot oem device-info","adb shell getprop",
)

# -------------------------
# LOGGING
# -------------------------

def ensure_logs_dir():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
def rotate_logs_if_needed():
    try:
        ensure_logs_dir()
        if os.path.isfile(LOG_PATH) and os.path.getsize(LOG_PATH) >= LOG_MAX_BYTES:
            for i in range(LOG_BACKUPS, 0, -1):
                src = f"{LOG_PATH}.{i}"
                dst = f"{LOG_PATH}.{i+1}"
                if os.path.exists(src):
                    if i == LOG_BACKUPS:
                        try:
                            os.remove(src)
                        except Exception:
                            pass
                    else:
                        os.replace(src, dst)
            try:
                os.replace(LOG_PATH, f"{LOG_PATH}.1")
            except Exception:
                pass
    except Exception:
        pass
def write_log_entry(level: str, message: str) -> None:
    """Append a structured JSON line {timestamp, level, message} to the log file."""
    ensure_logs_dir()
    rotate_logs_if_needed()
    payload = {
        "timestamp": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
        "level": (level or "INFO").upper(),
        "message": str(message),
    }
    try:
        line = json.dumps(payload, ensure_ascii=False)
    except Exception:
        line = f"[{payload['timestamp']}] {payload['level']}: {payload['message']}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# -------------------------
# CONSOLE (CTkTextbox)
# -------------------------

CONSOLE_COLORS = {
    "INFO": "#64B5F6",
    "SUCCESS": "#2E8B57",
    "ERROR": "#A92B2B",
    "CMD": "#F39C12",
    "WARNING": "#FBC02D"
}
def init_console(parent) -> ctk.CTkTextbox:
    """Initialize styled CTkTextbox console."""
    txt = ctk.CTkTextbox(
        parent,
        wrap="word",
        font=FONT_CODE,
        activate_scrollbars=True,
        corner_radius=8
    )
    txt.configure(state="disabled")
    for level, color in CONSOLE_COLORS.items():
        tag = f"LEVEL_{level}"
        txt.tag_config(tag, foreground=color)

    return txt
def append_console(text: str, level="INFO", timestamp=True):
    """Append new line to console with colored tag + log file entry."""
    raw_message = str(text)
    ui_text = raw_message
    if timestamp:
        now = datetime.now().strftime("%I:%M:%S %p")
        ui_text = f"[{now}] {raw_message}"
    normalized_level = (level or "INFO").upper()
    tag_name = f"LEVEL_{normalized_level}"
    app.after(0, _append_console_ui, ui_text, raw_message, normalized_level, tag_name)
def _append_console_ui(ui_text: str, raw_message: str, level: str, tag_name: str):
    # store in buffer for filtering
    CONSOLE_BUFFER.append((ui_text, level))
    if len(CONSOLE_BUFFER) > CONSOLE_BUFFER_MAX:
        del CONSOLE_BUFFER[: len(CONSOLE_BUFFER) - CONSOLE_BUFFER_MAX]
    _refresh_console_view()
    write_log_entry(level, raw_message)
def replace_last_console_line(new_text: str, level: str = "INFO"):
    """Replace last line in console with styled text."""
    tag_name = f"LEVEL_{level.upper()}"
    app.after(0, _replace_last_console_line_ui, new_text, tag_name)
def _replace_last_console_line_ui(text: str, tag_name: str):
    if CONSOLE_BUFFER:
        last_text, last_level = CONSOLE_BUFFER[-1]
        level = tag_name.replace("LEVEL_", "")
        CONSOLE_BUFFER[-1] = (text, level)
    _refresh_console_view()
def clear_console():
    CONSOLE_BUFFER.clear()
    _refresh_console_view()
CONSOLE_BUFFER: List[Tuple[str, str]] = []
CURRENT_CONSOLE_FILTER = "ALL"
CONSOLE_BUFFER_MAX = 1000
def _refresh_console_view():
    try:
        console.configure(state="normal")
        console.delete("1.0", "end")
        allowed = CURRENT_CONSOLE_FILTER.upper()
        for ui_text, level in CONSOLE_BUFFER:
            if allowed != "ALL" and level.upper() != allowed:
                continue
            tag_name = f"LEVEL_{level.upper()}"
            console.insert("end", ui_text + "\n", tag_name)
        console.see("end")
    finally:
        console.configure(state="disabled")

# -------------------------
# UI HELPERS (REUSABLE)
# -------------------------

def center_buttons(parent, buttons: List[ctk.CTkButton]) -> None:
    """Center a list of CTkButtons in a new inner frame under 'parent'."""
    inner = ctk.CTkFrame(parent, fg_color="transparent")
    inner.pack()
    for i, btn in enumerate(buttons):
        side_pad = 10 if i == 0 else 10
        btn.pack(in_=inner, side="left", padx=side_pad)

# -------------------------
# UI STYLES
# -------------------------

PALETTE = {
    "primary": "#1f6aa5",
    "primary_hover": "#144870",
    "secondary": "#3a3a3a",
    "secondary_hover": "#4a4a4a",
    "success": "#2E8B57",
    "success_hover": "#3CB371",
    "danger": "#A92B2B",
    "danger_hover": "#B03A3A",
    "warning": "#FBC02D",
    "info": "#64B5F6",
    "accent": "#F39C12",
}
RADIUS = 10
PADDING_X = 10
PADDING_Y = 8
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 16, "bold")
FONT_LABEL = ("Segoe UI", 13)
FONT_LABEL_BOLD = ("Segoe UI", 13, "bold")
FONT_CODE = ("Consolas", 14)
FONT_BUTTON = ("Segoe UI", 12, "bold")
BUTTON_STYLES = {
    "primary": {"fg": PALETTE["primary"], "hover": PALETTE["primary_hover"], "width": 120},
    "secondary": {"fg": PALETTE["secondary"], "hover": PALETTE["secondary_hover"], "width": 120},
    "success": {"fg": PALETTE["success"], "hover": PALETTE["success_hover"], "width": 120},
    "danger": {"fg": PALETTE["danger"], "hover": PALETTE["danger_hover"], "width": 120},
}
def create_button(parent, text: str, command, variant: str = "primary", width: int | None = None):
    style = BUTTON_STYLES.get(variant, BUTTON_STYLES["primary"])
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width or style["width"],
        fg_color=style["fg"],
        hover_color=style["hover"],
        font=FONT_BUTTON,
    )
def read_log_text() -> str:
    """Read and format log entries from the structured log file."""
    try:
        if not os.path.isfile(LOG_PATH):
            return "Log file not found."
        lines = []
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.rstrip("\n")
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    ts = obj.get("timestamp", "?")
                    lvl = obj.get("level", "INFO")
                    msg = obj.get("message", "")
                    lines.append(f"[{ts}] [{lvl}] {msg}")
                except Exception:
                    lines.append(raw)
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to read log file: {e}"
def open_logs_modal():
    win = ctk.CTkToplevel(app)
    win.title("Logs")
    win.geometry("720x460")
    win.grab_set()
    container = ctk.CTkFrame(win, corner_radius=12)
    container.pack(fill="both", expand=True, padx=10, pady=10)
    header = ctk.CTkFrame(container, corner_radius=10)
    header.pack(fill="x", padx=10, pady=(10, 6))
    ctk.CTkLabel(header, text="Application Logs", font=FONT_SUBTITLE).pack(side="left")
    btns = ctk.CTkFrame(header, fg_color="transparent")
    btns.pack(side="right")
    def do_refresh():
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("1.0", read_log_text())
        txt.configure(state="disabled")
    def do_open_folder():
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            os.startfile(os.path.abspath(os.path.dirname(LOG_PATH)))
        except Exception as e:
            show_dialog("error", "Open Folder", str(e))
    def do_export():
        try:
            from tkinter import filedialog
            target = filedialog.asksaveasfilename(title="Export Logs", defaultextension=".log",
                                                 filetypes=[("Log files","*.log"), ("Text files","*.txt"), ("All files","*.*")])
            if not target:
                return
            with open(target, "w", encoding="utf-8") as out:
                out.write(read_log_text())
            append_console(f"[INFO] Logs exported to: {target}")
        except Exception as e:
            show_dialog("error", "Export Logs", str(e))
    def do_clear():
        try:
            if os.path.isfile(LOG_PATH):
                os.remove(LOG_PATH)
            do_refresh()
            append_console("[INFO] Logs cleared.")
        except Exception as e:
            show_dialog("error", "Clear Logs", str(e))
    create_button(btns, "Refresh", do_refresh, variant="secondary").pack(side="left", padx=6)
    create_button(btns, "Open Folder", do_open_folder, variant="secondary").pack(side="left", padx=6)
    create_button(btns, "Export", do_export, variant="secondary").pack(side="left", padx=6)
    create_button(btns, "Clear", do_clear, variant="danger").pack(side="left", padx=6)
    txt = ctk.CTkTextbox(container, wrap="none", font=FONT_CODE, corner_radius=10)
    txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    txt.insert("1.0", read_log_text())
    txt.configure(state="disabled")

# -------------------------
# SUBPROCESS
# -------------------------

def run_subprocess(cmd: str, capture_output: bool = True) -> Tuple[int, str]:
    try:
        proc = subprocess.run(shlex.split(cmd), capture_output=capture_output, text=True, timeout=30)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 1, "[ERROR] Command timed out."
    except Exception as e:
        return 1, f"[ERROR] Exception: {e}"

# -------------------------
# CUSTOM DIALOGS
# -------------------------

def show_dialog(dialog_type: str, title: str, message: str) -> bool | None:
    win = ctk.CTkToplevel(app)
    win.title(title)
    win.geometry("420x220")
    win.grab_set()
    win.resizable(False, False)
    colors = {
        "info":    ("ℹ️", PALETTE["info"]),
        "warning": ("⚠️", PALETTE["warning"]),
        "error":   ("❌", PALETTE["danger"]),
        "confirm": ("❓", PALETTE["primary"]),
    }
    icon, color = colors.get(dialog_type, ("ℹ️", "#3BAFDA"))
    ctk.CTkLabel(win, text=f"{icon} {title}",
                 font=FONT_SUBTITLE,
                 text_color=color).pack(pady=(15, 8))
    msg_box = ctk.CTkTextbox(win, height=80, width=380,
                             corner_radius=8, wrap="word",
                             font=FONT_LABEL)
    msg_box.pack(padx=15, pady=6, fill="both", expand=True)
    msg_box.insert("1.0", message)
    msg_box.configure(state="disabled")
    result = None
    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack(pady=12)
    def close_with(value=None):
        nonlocal result
        result = value
        win.destroy()
    if dialog_type == "confirm":
        create_button(btn_frame, text="Yes", command=lambda: close_with(True), variant="success").pack(side="left", padx=10)
        create_button(btn_frame, text="No", command=lambda: close_with(False), variant="danger").pack(side="left", padx=10)
    else:
        ok_btn = create_button(btn_frame, text="OK", command=close_with, variant="primary")
        ok_btn.pack()
    win.wait_window()
    return result

# -------------------------
# COMMAND RUNNER
# -------------------------

def show_confirm_command(cmd: str):
    return show_dialog("confirm", "Confirm Command", f"Run this command?\n\n{cmd}")
def run_command_thread(cmd: str, require_confirmation=True):
    def worker():
        if require_confirmation and not is_harmless(cmd):
            if not confirm_destructive(cmd):
                append_console("[INFO] Command aborted by user.")
                return
        append_console(cmd, "CMD")
        code, out = run_subprocess(cmd)
        if out:
            append_console(out, "INFO")
        append_console(f"Exit code: {code}", "INFO")
    threading.Thread(target=worker, daemon=True).start()
def is_harmless(cmd: str) -> bool:
    normalized = " ".join(cmd.strip().lower().replace('"','').split())
    if normalized in SAFE_COMMANDS:
        return True
    return any(normalized.startswith(prefix) for prefix in SAFE_PREFIXES)

def confirm_destructive(cmd: str) -> bool:
    destructive_keywords = [
        " wipe ", " format ", "erase", "oem unlock", "flashing unlock", "flashing unlock_critical"
    ]
    lower = f" {cmd.lower()} "
    if any(k in lower for k in destructive_keywords):
        return bool(show_dialog("confirm", "Dangerous Command", f"This command may be destructive:\n\n{cmd}\n\nProceed?"))
    return True



# -------------------------
# DEVICE DETECTION
# -------------------------

def parse_adb_output(adb_out: str) -> List[Tuple[str, str]]:
    """Parse ADB devices output and return list of (serial, state) tuples."""
    lines = [l.strip() for l in adb_out.splitlines()
             if l.strip() and not l.startswith("List of devices attached")]
    return [(l.split()[0], l.split()[1]) for l in lines if len(l.split()) >= 2]
def get_device_state() -> Tuple[str, Optional[str]]:
    """Check device state and return (mode, serial)."""
    code_fb, out_fb = run_subprocess("fastboot devices")
    if code_fb == 0 and out_fb:
        return "FASTBOOT", out_fb.split()[0]
    code_adb, out_adb = run_subprocess("adb devices")
    if code_adb == 0 and out_adb:
        devs = parse_adb_output(out_adb)
        if devs:
            serial, state = devs[0]
            st = state.lower()
            if st == "device":
                return "ADB", serial
            if st == "sideload":
                return "SIDELOAD", serial
            if st == "unauthorized":
                return "UNAUTHORIZED", serial
            if st in ("recovery", "online"):
                return "ADB", serial
    return "NONE", None

# -------------------------
# DEVICE FOLDER UTILS
# -------------------------

def find_recovery_path(device_folder: str) -> Optional[str]:
    """Find recovery folder in device directory."""
    for c in ["Recoverys", "Recoveries", "Recovery"]:
        p = os.path.join(device_folder, c)
        if os.path.isdir(p):
            return p
    return None
def find_rom_path(device_folder: str) -> Optional[str]:
    """Find ROMs folder in device directory."""
    p = os.path.join(device_folder, "Roms")
    return p if os.path.isdir(p) else None
def find_boot_path(device_folder: str) -> Optional[str]:
    """Find boot folder in device directory."""
    recovery = find_recovery_path(device_folder)
    if not recovery:
        return None
    boot_p = os.path.join(recovery, "Boot")
    return boot_p if os.path.isdir(boot_p) else recovery

# -------------------------
# MODALS
# -------------------------

def show_device_folder_modal() -> Optional[str]:
    """Show device selection modal and return selected device folder path."""
    if not os.path.isdir(MAIN_DIR):
        show_dialog("error", "Missing Folder", f"Main folder not found:\n{MAIN_DIR or '(not set)'}")
        return None
    win = ctk.CTkToplevel(app)
    win.title("Select Device")
    win.geometry("420x360")
    win.grab_set()
    win.resizable(False, False)
    container = ctk.CTkFrame(win, corner_radius=12)
    container.pack(fill="both", expand=True, padx=12, pady=12)
    ctk.CTkLabel(container, text="Choose a Device Folder", font=FONT_SUBTITLE).pack(pady=(8, 6))
    list_frame = ctk.CTkScrollableFrame(container, corner_radius=10, width=360, height=200)
    list_frame.pack(fill="both", expand=True, padx=10, pady=6)
    selected: Dict[str, str] = {"path": None}
    def on_select(path: str):
        selected["path"] = path
        win.destroy()
    items = [d for d in os.listdir(MAIN_DIR) if os.path.isdir(os.path.join(MAIN_DIR, d))]
    if not items:
        ctk.CTkLabel(list_frame, text="No device folders found.", font=FONT_LABEL).pack(pady=20)
    else:
        for d in items:
            full_path = os.path.join(MAIN_DIR, d)
            btn = create_button(list_frame, text=d, command=lambda p=full_path: on_select(p), variant="primary")
            btn.pack(fill="x", padx=6, pady=4)
    action_frame = ctk.CTkFrame(container, fg_color="transparent")
    action_frame.pack(fill="x", pady=(10, 6))
    create_button(action_frame, "Cancel", lambda: win.destroy(), variant="secondary").pack(side="right", padx=8)
    win.wait_window()
    return selected["path"]

# -------------------------
# COMMAND RUNNER
# -------------------------

def show_custom_command_modal() -> Optional[str]:
    """Show custom command modal and return entered command."""
    sel = ctk.CTkToplevel(app)
    sel.title("Custom Command")
    sel.geometry("520x280")
    sel.grab_set()
    sel.minsize(500, 260)
    container = ctk.CTkFrame(sel, corner_radius=12)
    container.pack(fill="both", expand=True, padx=10, pady=10)
    ctk.CTkLabel(container, text="💻 Enter ADB/Fastboot command", font=FONT_SUBTITLE).pack(pady=(12, 8))
    picks_frame = ctk.CTkFrame(container, corner_radius=8)
    picks_frame.pack(padx=10, pady=(2, 8), fill="x")
    ctk.CTkLabel(picks_frame, text="Quick picks", font=FONT_LABEL_BOLD).pack(anchor="w", padx=10, pady=(8, 4))
    picks_inner = ctk.CTkFrame(picks_frame, fg_color="transparent")
    picks_inner.pack(fill="x", padx=10, pady=(0, 8))
    picks_inner.grid_columnconfigure(0, weight=1)
    predefined = [
        ("adb devices", "List ADB devices"),
        ("adb reboot", "Reboot device"),
        ("adb reboot recovery", "Reboot to recovery"),
        ("adb reboot bootloader", "Reboot to bootloader"),
        ("fastboot devices", "List Fastboot devices"),
        ("fastboot reboot", "Fastboot reboot"),
        ("fastboot reboot recovery", "Fastboot reboot to recovery"),
        ("fastboot reboot bootloader", "Fastboot reboot to bootloader"),
        ("fastboot getvar serialno", "Serial number"),
        ("fastboot getvar unlocked", "Bootloader status"),
        ("fastboot getvar secure", "Secure boot status"),
        ("fastboot format cache", "Format cache partition"),
        ("fastboot format userdata", "Format userdata partition"),
    ]
    pick_values = [p[0] for p in predefined]
    pick_display = [f"{cmd}  —  {desc}" for cmd, desc in predefined]
    selected_var = ctk.StringVar(value=pick_display[0])
    drop = ctk.CTkOptionMenu(picks_inner, values=pick_display, variable=selected_var, width=360)
    drop.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    def apply_pick():
        idx = pick_display.index(selected_var.get()) if selected_var.get() in pick_display else 0
        entry.delete(0, ctk.END)
        entry.insert(0, pick_values[idx])
    create_button(picks_inner, text="Use", command=apply_pick, variant="secondary", width=80).grid(row=0, column=1, sticky="e")
    entry = ctk.CTkEntry(container, placeholder_text="adb devices", width=480, font=FONT_CODE)
    entry.pack(pady=8)
    cmd_value = {"value": None}
    def on_ok():
        cmd_value["value"] = entry.get().strip()
        sel.destroy()
    def on_cancel():
        sel.destroy()
    btn_frame = ctk.CTkFrame(container, fg_color="transparent")
    btn_frame.pack(side="bottom", fill="x", pady=10)
    create_button(btn_frame, text="Run", command=on_ok, variant="success").pack(side="left", padx=12)
    create_button(btn_frame, text="Cancel", command=on_cancel, variant="danger").pack(side="right", padx=12)
    sel.wait_window()
    return cmd_value["value"]
def show_directory_picker_modal(title: str = "Select Folder") -> Optional[str]:
    """Show a simple directory picker dialog"""
    from tkinter import filedialog
    directory = filedialog.askdirectory(
        title=title,
        initialdir=MAIN_DIR if MAIN_DIR else os.path.expanduser("~")
    )
    return directory if directory else None
def show_file_selection_modal(paths: List[str], title: str = "Select a file") -> Optional[str]:
    sel = ctk.CTkToplevel(app)
    sel.title("Select File")
    sel.geometry("520x360")
    sel.grab_set()
    sel.resizable(False, False)
    container = ctk.CTkFrame(sel, corner_radius=12)
    container.pack(fill="both", expand=True, padx=12, pady=12)
    ctk.CTkLabel(container, text=title, font=FONT_SUBTITLE).pack(pady=(6, 10))
    scroll = ctk.CTkScrollableFrame(container, corner_radius=8, width=480, height=230)
    scroll.pack(fill="both", expand=True, pady=(0, 10))
    choice = {"path": None}
    def choose(p: str):
        choice["path"] = p
        sel.destroy()
    for p in sorted(paths):
        create_button(scroll, text=os.path.basename(p), command=lambda pp=p: choose(pp),
                      variant="secondary", width=460).pack(pady=4, padx=4)
    bottom = ctk.CTkFrame(container, fg_color="transparent")
    bottom.pack()
    create_button(bottom, "Cancel", lambda: sel.destroy(), variant="danger", width=120).pack(pady=4)
    sel.wait_window()
    return choice["path"]

# -------------------------
# ACTIONS
# -------------------------

def update_status_bar(last_action: str = ""):
    mode, serial = get_device_state()
    status_label.configure(text=f"Device: {serial or 'None'}    |    Mode: {mode}")
    if last_action:
        status_progress.configure(text=last_action)
def action_check_device():
    append_console("[ACTION] Check device", "INFO")
    mode, serial = get_device_state()
    if mode=="NONE":
        show_dialog("info", "Device Check", "No device connected.")
    elif mode=="UNAUTHORIZED":
        show_dialog("warning", "Device Check", "Device unauthorized. Enable USB debugging.")
    else:
        show_dialog("info", "Device Check", f"Device: {serial}\nMode: {mode}")
    update_status_bar()
def action_flash_generic(folder_type, fastboot_partition):
    append_console(f"[ACTION] Flash {fastboot_partition}", "INFO")
    mode, _ = get_device_state()
    if mode != "FASTBOOT":
        show_dialog("error", "Wrong Mode", f"Device must be in FASTBOOT mode. Current: {mode}")
        return
    folder = find_recovery_path(selected_device_folder) if folder_type=="recovery" else find_boot_path(selected_device_folder)
    if not folder:
        show_dialog("error", "Missing Folder", f"No {folder_type} folder found under device folder.")
        return
    imgs = [os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith(".img")]
    if not imgs:
        show_dialog("error", "No Images", f"No .img files found in {folder_type} folder.")
        return
    selected_file = show_file_selection_modal(imgs, f"Available {folder_type} images:")
    if not selected_file:
        append_console("[INFO] No image selected.", "INFO")
        return
    if not show_dialog("confirm", "Confirm Flash", f"Flash {fastboot_partition} partition?\n\nFile: {os.path.basename(selected_file)}"):
        append_console(f"[INFO] {fastboot_partition} flash cancelled by user.", "INFO")
        return

    run_command_thread(f'fastboot flash {fastboot_partition} "{selected_file}"')
    update_status_bar()
def action_flash_recovery(): action_flash_generic("recovery","recovery")
def action_flash_boot(): action_flash_generic("boot","boot")
def action_flash_super():
    append_console("[ACTION] Flash super_empty.img", "INFO")
    mode, _ = get_device_state()
    if mode != "FASTBOOT":
        show_dialog("error", "Wrong Mode", "Device must be in FASTBOOT mode")
        return
    recovery_dir = find_recovery_path(selected_device_folder)
    if not recovery_dir:
        show_dialog("error", "Missing Folder", "No recovery folder found")
        return
    super_file = os.path.join(recovery_dir,"super_empty.img")
    if not os.path.isfile(super_file):
        show_dialog("error", "Missing File", "super_empty.img not found")
        return
    if not show_dialog("confirm", "Confirm Super Flash", f"Flash super_empty.img to device?\n\nThis will wipe the super partition.\n\nFile: {os.path.basename(super_file)}"):
        append_console("[INFO] Super flash cancelled by user.", "INFO")
        return

    run_command_thread(f'fastboot flash super "{super_file}"')
    update_status_bar()
def action_adb_sideload():
    append_console("[ACTION] ADB Sideload", "INFO")
    mode, _ = get_device_state()
    if mode != "SIDELOAD":
        show_dialog("error", "Wrong Mode", "Device must be in ADB SIDELOAD mode")
        return
    rom_dir = find_rom_path(selected_device_folder)
    if not rom_dir:
        show_dialog("error", "Missing Folder", "No Roms folder found")
        return
    zips = [os.path.join(rom_dir,f) for f in os.listdir(rom_dir) if f.lower().endswith(".zip")]
    if not zips:
        show_dialog("error", "No ZIPs", "No .zip files found in Roms folder")
        return
    selected_file = show_file_selection_modal(zips,"Available ZIP files:")
    if not selected_file:
        append_console("[INFO] No ZIP selected","INFO")
        return
    if not show_dialog("confirm", "Confirm Sideload", f"Start ADB sideload with this file?\n\n{os.path.basename(selected_file)}"):
        append_console("[INFO] Sideload cancelled by user.", "INFO")
        return

    append_console(f"[INFO] Starting sideload: {selected_file}")
    def run_sideload():
        process = subprocess.Popen(["adb","sideload",selected_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        last_percent = None
        printed_progress = False
        for line in iter(process.stdout.readline,''):
            line = line.rstrip()
            if not line:
                continue
            match = re.search(r"\(~(\d+)%\)", line)
            if match:
                percent = match.group(1)
                if last_percent is None:
                    append_console(line, "INFO")
                    printed_progress = True
                elif percent != last_percent:
                    replace_last_console_line(line, "INFO")
                last_percent = percent
                update_status_bar(f"Sideload:{percent}%")
            else:
                append_console(line,"INFO")
        process.wait()
        if printed_progress:
            final_text = line if 'line' in locals() and line else ("sideload complete" if process.returncode==0 else "sideload failed")
            replace_last_console_line(final_text, "SUCCESS" if process.returncode==0 else "ERROR")
        append_console("[SUCCESS] Sideload completed" if process.returncode==0 else "[ERROR] Sideload failed",
                       "SUCCESS" if process.returncode==0 else "ERROR")
    threading.Thread(target=run_sideload, daemon=True).start()
def action_reboot(target):
    append_console(f"[ACTION] Reboot to {target}", "INFO")
    mode, _ = get_device_state()
    if target=="system":
        if mode=="FASTBOOT":
            run_command_thread("fastboot reboot", False)
        elif mode in ("ADB","SIDELOAD"):
            run_command_thread("adb reboot", False)
        else:
            show_dialog("error","No Device","No device found to reboot.")
    elif target=="recovery":
        if mode=="FASTBOOT":
            run_command_thread("fastboot reboot recovery", False)
        elif mode in ("ADB","SIDELOAD"):
            run_command_thread("adb reboot recovery", False)
        else:
            show_dialog("error","No Device","No device found to reboot.")
    update_status_bar()
def action_custom_command():
    append_console("[ACTION] Custom Command", "INFO")
    cmd = show_custom_command_modal()
    if cmd:
        run_command_thread(cmd)
    else:
        append_console("[INFO] Custom command cancelled.", "INFO")
def action_change_device():
    global selected_device_folder
    append_console("[ACTION] Change Device", "INFO")
    new_folder = show_device_folder_modal()
    if new_folder and new_folder != selected_device_folder:
        selected_device_folder = new_folder
        selected_label.configure(text=f"Selected Device : {os.path.basename(selected_device_folder)}")
        append_console(f"[INFO] Switched to device folder: {selected_device_folder}", "INFO")
        update_status_bar()
    elif new_folder:
        append_console("[INFO] Same device folder selected.", "INFO")
    else:
        append_console("[INFO] Device change cancelled.", "INFO")
def ensure_main_dir() -> bool:
    """Ensure MAIN_DIR is set to an existing directory; prompt user if needed."""
    global MAIN_DIR
    if MAIN_DIR and os.path.isdir(MAIN_DIR):
        return True
    chosen_dir = show_directory_picker_modal("Select Main ROMs Folder")
    if not chosen_dir:
        return False
    MAIN_DIR = chosen_dir
    append_console(f"[INFO] Set main folder: {MAIN_DIR}", "INFO")
    return True
def action_change_main_dir():
    append_console("[ACTION] Change Main Folder", "INFO")
    global MAIN_DIR, selected_device_folder
    chosen_dir = show_directory_picker_modal("Select Main ROMs Folder")
    if not chosen_dir:
        append_console("[INFO] Main folder change cancelled.", "INFO")
        return
    MAIN_DIR = chosen_dir
    append_console(f"[INFO] Main folder set to: {MAIN_DIR}", "INFO")
    if selected_device_folder and not os.path.commonpath([os.path.abspath(selected_device_folder), os.path.abspath(MAIN_DIR)]) == os.path.abspath(MAIN_DIR):
        selected_device_folder = None
        selected_label.configure(text="Selected Device : None")
        update_status_bar("Main folder changed; device cleared")

# -------------------------
# GUI
# -------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Custom ROM Flashing Tool")
app.geometry("1200x600")
app.protocol("WM_DELETE_WINDOW", app.destroy)
app.grid_rowconfigure(0, weight=0)
app.grid_rowconfigure(1, weight=5)  # Give console even more space
app.grid_columnconfigure(1, weight=1)
sidebar = ctk.CTkFrame(app, width=200, corner_radius=8)
sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
sidebar.grid_propagate(False)
ctk.CTkLabel(sidebar,text="ROM Menu", font=FONT_TITLE).pack(pady=(18,6), padx=PADDING_X)
ctk.CTkLabel(sidebar,text="Select actions on the right", font=FONT_LABEL).pack(pady=(0,12), padx=PADDING_X)
buttons = [
    ("Flash Recovery", action_flash_recovery, "primary"),
    ("Flash Boot", action_flash_boot, "primary"),
    ("Flash super_empty", action_flash_super, "primary"),
    ("ADB Sideload (ROM ZIP)", action_adb_sideload, "primary"),
    ("View Logs", open_logs_modal, "secondary"),
    ("Change Main Folder", action_change_main_dir, "secondary"),
    ("Reboot → System", lambda: action_reboot("system"), "secondary"),
    ("Reboot → Recovery", lambda: action_reboot("recovery"), "secondary"),
    ("Custom Command", action_custom_command, "secondary"),
    ("Check Device", action_check_device, "secondary"),
    ("Change Device", action_change_device, "secondary"),
    ("Exit", app.destroy, "danger")
]
for text, cmd, variant in buttons:
    btn = create_button(sidebar, text=text, command=cmd, variant=variant, width=190)
    btn.pack(pady=6, padx=PADDING_X)
main_frame = ctk.CTkFrame(app, corner_radius=RADIUS)
main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
main_frame.grid_rowconfigure(2, weight=0)  # Don't expand the box frame
main_frame.grid_columnconfigure(0, weight=1)
ctk.CTkLabel(main_frame, text="Custom ROM Flashing Utility", font=FONT_TITLE).grid(row=0,column=0, sticky="w", padx=14, pady=(8,6))
ctk.CTkLabel(main_frame,text="Workflow: Select device folder → choose action → follow prompts.\nKeep adb & fastboot in PATH. Logs in logs/tool.log",font=FONT_LABEL,wraplength=760,justify="left").grid(row=1,column=0, sticky="w", padx=14,pady=(0,6))
box_frame = ctk.CTkFrame(main_frame, corner_radius=RADIUS)
box_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=8)
selected_label = ctk.CTkLabel(box_frame, text="Selected Device : None", font=FONT_LABEL_BOLD)
selected_label.grid(row=0,column=0, sticky="w", padx=12,pady=(10,10))
console_frame = ctk.CTkFrame(app, corner_radius=RADIUS)
console_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0,10))
console_frame.grid_rowconfigure(1, weight=1)
console_frame.grid_columnconfigure(0, weight=1)
filters_bar = ctk.CTkFrame(console_frame, fg_color="transparent")
filters_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,0))
filters_bar.grid_columnconfigure(0, weight=1)
def _set_console_filter(value: str):
    global CURRENT_CONSOLE_FILTER
    CURRENT_CONSOLE_FILTER = value.upper()
    _refresh_console_view()
toolbar = ctk.CTkFrame(filters_bar, fg_color="transparent")
toolbar.pack(side="left")
create_button(toolbar, text="ALL", command=lambda: _set_console_filter("ALL"), variant="secondary", width=70).pack(side="left", padx=4)
create_button(toolbar, text="INFO", command=lambda: _set_console_filter("INFO"), variant="secondary", width=70).pack(side="left", padx=4)
create_button(toolbar, text="SUCCESS", command=lambda: _set_console_filter("SUCCESS"), variant="secondary", width=90).pack(side="left", padx=4)
create_button(toolbar, text="ERROR", command=lambda: _set_console_filter("ERROR"), variant="secondary", width=80).pack(side="left", padx=4)
create_button(toolbar, text="CMD", command=lambda: _set_console_filter("CMD"), variant="secondary", width=70).pack(side="left", padx=4)
create_button(toolbar, text="WARNING", command=lambda: _set_console_filter("WARNING"), variant="secondary", width=100).pack(side="left", padx=4)
create_button(filters_bar, text="Clear Console", command=clear_console, variant="secondary", width=140).pack(side="left", padx=8)
console = init_console(console_frame)
console.grid(row=1,column=0, sticky="nsew", padx=8, pady=8)
append_console("Custom ROM Flashing Tool - Ready", "INFO")
append_console("Select a device folder and choose an action from the menu", "INFO")
status_bar = ctk.CTkFrame(app,height=26, corner_radius=0)
status_bar.grid(row=2,column=0,columnspan=2, sticky="ew")
status_label = ctk.CTkLabel(status_bar, text="Device: None    |    Mode: NONE", anchor="w", font=FONT_LABEL)
status_label.pack(side="left", padx=10)
status_progress = ctk.CTkLabel(status_bar, text="", anchor="w", font=FONT_LABEL)
status_progress.pack(side="left", padx=10)

# -------------------------
# STARTUP
# -------------------------

def start_app():
    global selected_device_folder
    if not ensure_main_dir():
        append_console("[ERROR] No main folder selected. Exiting.", "ERROR")
        show_dialog("info","Exit","No main folder selected. Exiting application.")
        app.destroy()
        return
    selected_device_folder = show_device_folder_modal()
    if not selected_device_folder:
        append_console("[ERROR] No device folder selected. Exiting.", "ERROR")
        show_dialog("info","Exit","No device selected. Exiting application.")
        app.destroy()
    else:
        selected_label.configure(text=f"Selected Device : {os.path.basename(selected_device_folder)}")
        append_console(f"[INFO] Selected device folder: {selected_device_folder}", "INFO")
        update_status_bar()
        append_console("[INFO] Tool started. Version: 1.0", "INFO")
        write_log_entry("INFO", "Tool started")
app.after(100, start_app)
app.mainloop()