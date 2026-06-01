#!/usr/bin/env python3
import os
import sys
import json
import shutil
import platform
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog

APPID = "247000"
GAME_SUBPATH = os.path.join("Nomad Games", "Talisman", "saved_game")

# --- Configuration des Chemins / Path Configurations ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLOTS_DIR = os.path.join(SCRIPT_DIR, "talisman_save_slots")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "talisman_manager_config.json")
os.makedirs(SLOTS_DIR, exist_ok=True)

# --- Dictionnaires de Traduction / Translation Dictionaries ---
LOCALES = {
    "en": {
        "title": "Talisman - Save Manager",
        "info_frame": " Information ",
        "game_path": "Game folder:",
        "not_found": "Not found!",
        "btn_modify": "✏️ Modify",
        "running_warn": "⚠️ ATTENTION: Talisman is running. Close it before any action.",
        "col_name": "Slot Name",
        "col_files": "Files",
        "col_date": "Modification Date",
        "btn_refresh": "🔄 Refresh",
        "btn_save": "📥 Save Current Game",
        "btn_load": "📤 Load Selected Slot",
        "btn_rename": "✏️ Rename",
        "btn_delete": "❌ Delete",
        "browse_title": "Select Talisman 'saved_game' folder",
        "path_updated_title": "Path Updated",
        "path_updated_msg": "New target folder configured:\n",
        "err_title": "Error",
        "err_no_path": "The specified save folder is missing or invalid.",
        "warn_title": "Empty",
        "warn_no_files": "No save files found in:\n",
        "save_prompt_title": "Save Game",
        "save_prompt_msg": "Name for the new slot:",
        "overwrite_title": "Overwrite?",
        "overwrite_msg": "The slot '{}' already exists. Do you want to overwrite it?",
        "success_title": "Success",
        "success_save": "Slot '{}' saved successfully.",
        "confirm_title": "Confirmation",
        "confirm_load": "ATTENTION: The current game will be OVERWRITTEN by '{}'.\nContinue?",
        "success_load": "Slot '{}' has been loaded into the game.",
        "rename_title": "Rename",
        "rename_msg": "New name for '{}':",
        "err_exists": "A slot with this name already exists.",
        "delete_title": "Delete",
        "delete_msg": "Are you sure you want to PERMANENTLY delete slot '{}'?",
        "sel_required_title": "Selection Required",
        "sel_required_msg": "Please select a slot from the list.",
        "files_text": "files"
    },
    "fr": {
        "title": "Talisman - Gestionnaire de Sauvegardes",
        "info_frame": " Informations ",
        "game_path": "Dossier de jeu :",
        "not_found": "Introuvable !",
        "btn_modify": "✏️ Modifier",
        "running_warn": "⚠️ ATTENTION : Talisman est en cours d'exécution. Fermez-le avant toute action.",
        "col_name": "Nom du Slot",
        "col_files": "Fichiers",
        "col_date": "Date de modification",
        "btn_refresh": "🔄 Rafraîchir",
        "btn_save": "📥 Sauvegarder Partie",
        "btn_load": "📤 Charger Slot",
        "btn_rename": "✏️ Renommer",
        "btn_delete": "❌ Supprimer",
        "browse_title": "Sélectionner le dossier 'saved_game' de Talisman",
        "path_updated_title": "Chemin mis à jour",
        "path_updated_msg": "Nouveau dossier cible configuré :\n",
        "err_title": "Erreur",
        "err_no_path": "Le dossier de sauvegarde spécifié est introuvable ou invalide.",
        "warn_title": "Vide",
        "warn_no_files": "Aucun fichier de sauvegarde trouvé dans :\n",
        "save_prompt_title": "Sauvegarder",
        "save_prompt_msg": "Nom du nouveau slot :",
        "overwrite_title": "Écraser ?",
        "overwrite_msg": "Le slot '{}' existe déjà. Voulez-vous l'écraser ?",
        "success_title": "Succès",
        "success_save": "Slot '{}' sauvegardé avec succès.",
        "confirm_title": "Confirmation",
        "confirm_load": "ATTENTION : La partie actuelle en jeu va être ÉCRASÉE par '{}'.\nContinuer ?",
        "success_load": "Le slot '{}' a été chargé dans le jeu.",
        "rename_title": "Renommer",
        "rename_msg": "Nouveau nom pour '{}' :",
        "err_exists": "Un slot portant ce nom existe déjà.",
        "delete_title": "Suppression",
        "delete_msg": "Êtes-vous sûr de vouloir supprimer DÉFINITIVEMENT le slot '{}' ?",
        "sel_required_title": "Sélection requise",
        "sel_required_msg": "Veuillez sélectionner un slot dans la liste.",
        "files_text": "fichiers"
    }
}

def get_steam_roots():
    roots = set()
    home = os.path.expanduser("~")
    system = platform.system()

    if system == "Linux":
        roots.update([
            os.path.join(home, ".steam", "steam"),
            os.path.join(home, ".local", "share", "Steam"),
            os.path.join(home, ".steam", "root"),
            os.path.join(home, ".steam", "debian-installation"),
            os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam")
        ])
    elif system == "Windows":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        roots.update([
            os.path.join(program_files_x86, "Steam"),
            os.path.join(program_files, "Steam")
        ])
    elif system == "Darwin":
        roots.add(os.path.join(home, "Library", "Application Support", "Steam"))

    discovered = list(roots)
    for r in discovered:
        vdf = os.path.join(r, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            try:
                with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if '"path"' in line:
                            parts = line.split('"')
                            if len(parts) >= 4:
                                path = parts[3].replace("\\\\", "\\")
                                roots.add(path)
            except Exception:
                pass
    return [r for r in roots if os.path.isdir(r)]

def detect_save_dir():
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            cand = os.path.join(appdata, GAME_SUBPATH)
            if os.path.isdir(cand):
                return cand

    for lib in get_steam_roots():
        pfx = os.path.join(lib, "steamapps", "compatdata", APPID, "pfx", "drive_c", "users")
        if os.path.isdir(pfx):
            try:
                for u in os.listdir(pfx):
                    cand = os.path.join(pfx, u, "AppData", "Roaming", GAME_SUBPATH)
                    if os.path.isdir(cand):
                        return cand
            except Exception:
                continue
    return ""

def is_game_running():
    system = platform.system()
    try:
        if system == "Windows":
            tasks = subprocess.check_output(["tasklist"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return "talisman" in tasks.lower()
        else:
            p = subprocess.Popen(["pgrep", "-fi", "talisman"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = p.communicate()
            return p.returncode == 0
    except Exception:
        return False

# --- Main GUI Class ---
class TalismanManagerGUI:
    def __init__(self, root):
        self.root = root
        self.lang = self.load_config()
        self.save_dir = detect_save_dir()
        
        self.root.geometry("680x470")
        self.root.minsize(620, 420)
        
        self.create_widgets()
        self.update_ui_text()
        self.refresh_slots()
        self.check_game_status()

    def load_config(self):
        """Loads configuration or defaults to English."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    return config.get("lang", "en")
            except Exception:
                pass
        return "en"

    def save_config(self):
        """Saves current language configuration."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"lang": self.lang}, f)
        except Exception:
            pass

    def create_widgets(self):
        # --- Top Status Frame ---
        self.status_frame = tk.LabelFrame(self.root, padx=10, pady=5)
        self.status_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_path_title = tk.Label(self.status_frame, font=("TkDefaultFont", 9, "bold"))
        self.lbl_path_title.grid(row=0, column=0, sticky="w")
        
        self.lbl_path = tk.Label(self.status_frame, wraplength=360, justify="left")
        self.lbl_path.grid(row=0, column=1, sticky="w", padx=5)

        self.btn_browse = tk.Button(self.status_frame, command=self.browse_save_dir, font=("TkDefaultFont", 8))
        self.btn_browse.grid(row=0, column=2, sticky="e", padx=5)

        # Language Selector Combobox
        self.lang_var = tk.StringVar(value="English" if self.lang == "en" else "Français")
        self.combo_lang = ttk.Combobox(self.status_frame, textvariable=self.lang_var, values=["English", "Français"], state="readonly", width=8)
        self.combo_lang.grid(row=0, column=3, sticky="e", padx=5)
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_language_change)

        self.lbl_warn = tk.Label(self.status_frame, fg="dark orange", font=("TkDefaultFont", 9, "bold"))
        self.lbl_warn.grid(row=1, column=0, columnspan=4, sticky="w", pady=2)

        # --- Central Frame (Treeview List) ---
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.columns = ("name", "files", "date")
        self.tree = ttk.Treeview(list_frame, columns=self.columns, show="headings", selectmode="browse")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Lower Action Buttons ---
        self.btn_frame = tk.Frame(self.root, pady=5)
        self.btn_frame.pack(fill="x", padx=10)

        self.btn_refresh_widget = tk.Button(self.btn_frame, command=self.refresh_slots)
        self.btn_refresh_widget.pack(side="left", padx=2)
        
        self.btn_save_widget = tk.Button(self.btn_frame, bg="#d4edda", command=self.save_current)
        self.btn_save_widget.pack(side="left", padx=2)
        
        self.btn_load_widget = tk.Button(self.btn_frame, bg="#cce5ff", command=self.load_slot)
        self.btn_load_widget.pack(side="left", padx=2)
        
        self.btn_rename_widget = tk.Button(self.btn_frame, command=self.rename_slot)
        self.btn_rename_widget.pack(side="left", padx=2)
        
        self.btn_delete_widget = tk.Button(self.btn_frame, bg="#f8d7da", command=self.delete_slot)
        self.btn_delete_widget.pack(side="left", padx=2)

    def update_ui_text(self):
        """Refreshes all text strings dynamically based on selected language."""
        t = LOCALES[self.lang]
        
        self.root.title(t["title"])
        self.status_frame.config(text=t["info_frame"])
        self.lbl_path_title.config(text=t["game_path"])
        self.btn_browse.config(text=t["btn_modify"])
        
        if self.save_dir:
            self.lbl_path.config(text=self.save_dir, fg="green")
        else:
            self.lbl_path.config(text=t["not_found"], fg="red")

        self.tree.heading("name", text=t["col_name"])
        self.tree.heading("files", text=t["col_files"])
        self.tree.heading("date", text=t["col_date"])
        
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("files", width=90, anchor="center")
        self.tree.column("date", width=160, anchor="center")

        self.btn_refresh_widget.config(text=t["btn_refresh"])
        self.btn_save_widget.config(text=t["btn_save"])
        self.btn_load_widget.config(text=t["btn_load"])
        self.btn_rename_widget.config(text=t["btn_rename"])
        self.btn_delete_widget.config(text=t["btn_delete"])

    def on_language_change(self, event):
        """Triggered when user selects a different language from the dropdown menu."""
        selected = self.lang_var.get()
        self.lang = "en" if selected == "English" else "fr"
        self.save_config()
        self.update_ui_text()
        self.refresh_slots()

    def browse_save_dir(self):
        t = LOCALES[self.lang]
        initial_dir = self.save_dir if self.save_dir else os.path.expanduser("~")
        selected_dir = filedialog.askdirectory(title=t["browse_title"], initialdir=initial_dir)
        
        if selected_dir:
            self.save_dir = os.path.normpath(selected_dir)
            self.lbl_path.config(text=self.save_dir, fg="green")
            messagebox.showinfo(t["path_updated_title"], f"{t['path_updated_msg']}{self.save_dir}")

    def check_game_status(self):
        t = LOCALES[self.lang]
        if is_game_running():
            self.lbl_warn.config(text=t["running_warn"])
        else:
            self.lbl_warn.config(text="")
        self.root.after(3000, self.check_game_status)

    def refresh_slots(self):
        t = LOCALES[self.lang]
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(SLOTS_DIR):
            return

        for d in sorted(os.listdir(SLOTS_DIR)):
            full_path = os.path.join(SLOTS_DIR, d)
            if os.path.isdir(full_path):
                num_files = len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])
                mtime = os.path.getmtime(full_path)
                date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
                self.tree.insert("", "end", iid=d, values=(d, f"{num_files} {t['files_text']}", date_str))

    def get_selected_slot(self):
        t = LOCALES[self.lang]
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(t["sel_required_title"], t["sel_required_msg"])
            return None
        return selected[0]

    def save_current(self):
        t = LOCALES[self.lang]
        if not self.save_dir or not os.path.isdir(self.save_dir):
            messagebox.showerror(t["err_title"], t["err_no_path"])
            return

        files = [f for f in os.listdir(self.save_dir) if os.path.isfile(os.path.join(self.save_dir, f))]
        if not files:
            messagebox.showwarning(t["warn_title"], f"{t['warn_no_files']}{self.save_dir}")
            return

        default_name = f"save_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
        name = simpledialog.askstring(t["save_prompt_title"], t["save_prompt_msg"], initialvalue=default_name)
        if not name:
            return

        name = name.replace("/", "_").replace("\\", "_")
        dest = os.path.join(SLOTS_DIR, name)

        if os.path.exists(dest):
            if not messagebox.askyesno(t["overwrite_title"], t["overwrite_msg"].format(name)):
                return
            shutil.rmtree(dest)

        os.makedirs(dest)
        for f in files:
            shutil.copy2(os.path.join(self.save_dir, f), os.path.join(dest, f))
        
        os.utime(dest, None)
        self.refresh_slots()
        messagebox.showinfo(t["success_title"], t["success_save"].format(name))

    def load_slot(self):
        t = LOCALES[self.lang]
        if not self.save_dir:
            messagebox.showerror(t["err_title"], t["err_no_path"])
            return

        slot = self.get_selected_slot()
        if not slot:
            return

        if not messagebox.askyesno(t["confirm_title"], t["confirm_load"].format(slot)):
            return

        slot_path = os.path.join(SLOTS_DIR, slot)
        os.makedirs(self.save_dir, exist_ok=True)

        for f in os.listdir(slot_path):
            src_file = os.path.join(slot_path, f)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, os.path.join(self.save_dir, f))

        messagebox.showinfo(t["success_title"], t["success_load"].format(slot))

    def rename_slot(self):
        t = LOCALES[self.lang]
        slot = self.get_selected_slot()
        if not slot:
            return

        new_name = simpledialog.askstring(t["rename_title"], t["rename_msg"].format(slot), initialvalue=slot)
        if not new_name or new_name == slot:
            return

        new_name = new_name.replace("/", "_").replace("\\", "_")
        new_path = os.path.join(SLOTS_DIR, new_name)

        if os.path.exists(new_path):
            messagebox.showerror(t["err_title"], t["err_exists"])
            return

        os.rename(os.path.join(SLOTS_DIR, slot), new_path)
        self.refresh_slots()

    def delete_slot(self):
        t = LOCALES[self.lang]
        slot = self.get_selected_slot()
        if not slot:
            return

        if messagebox.askyesno(t["delete_title"], t["delete_msg"].format(slot)):
            shutil.rmtree(os.path.join(SLOTS_DIR, slot))
            self.refresh_slots()

# --- Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TalismanManagerGUI(root)
    root.mainloop()
