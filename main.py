#!/usr/bin/env python3
import os
import sys
import shutil
import platform
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog

APPID = "247000"
GAME_SUBPATH = os.path.join("Nomad Games", "Talisman", "saved_game")

# --- Configuration des Chemins ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLOTS_DIR = os.path.join(SCRIPT_DIR, "talisman_save_slots")
os.makedirs(SLOTS_DIR, exist_ok=True)

def get_steam_roots():
    """Détecte les dossiers racines de Steam et les bibliothèques secondaires."""
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
    elif system == "Darwin": # macOS
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
    """Trouve dynamiquement le dossier de sauvegarde selon l'OS."""
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
    """Vérifie si Talisman est en cours d'exécution."""
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

# --- Classe Principale GUI ---
class TalismanManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Talisman - Gestionnaire de Sauvegardes")
        self.root.geometry("650x470")
        self.root.minsize(600, 420)
        
        self.save_dir = detect_save_dir()
        
        self.create_widgets()
        self.refresh_slots()
        self.check_game_status()

    def create_widgets(self):
        # --- Zone Statut Supérieure ---
        status_frame = tk.LabelFrame(self.root, text=" Informations ", padx=10, pady=5)
        status_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(status_frame, text="Dossier de jeu :", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w")
        
        # Label affichant le chemin actuel
        self.lbl_path = tk.Label(status_frame, text=self.save_dir if self.save_dir else "Introuvable !", fg="green" if self.save_dir else "red", wraplength=420, justify="left")
        self.lbl_path.grid(row=0, column=1, sticky="w", padx=5)

        # Bouton pour modifier manuellement le dossier
        self.btn_browse = tk.Button(status_frame, text="✏️ Modifier", command=self.browse_save_dir, font=("TkDefaultFont", 8))
        self.btn_browse.grid(row=0, column=2, sticky="e", padx=5)

        self.lbl_warn = tk.Label(status_frame, text="", fg="dark orange", font=("TkDefaultFont", 9, "bold"))
        self.lbl_warn.grid(row=1, column=0, columnspan=3, sticky="w", pady=2)

        # --- Zone Centrale (Liste des Slots) ---
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("name", "files", "date")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Nom du Slot")
        self.tree.heading("files", text="Fichiers")
        self.tree.heading("date", text="Date de modification")
        
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("files", width=80, anchor="center")
        self.tree.column("date", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Zone Boutons Latérale / Inférieure ---
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill="x", padx=10)

        tk.Button(btn_frame, text="🔄 Rafraîchir", command=self.refresh_slots).pack(side="left", padx=2)
        tk.Button(btn_frame, text="📥 Sauvegarder Partie", bg="#d4edda", command=self.save_current).pack(side="left", padx=2)
        tk.Button(btn_frame, text="📤 Charger Slot", bg="#cce5ff", command=self.load_slot).pack(side="left", padx=2)
        tk.Button(btn_frame, text="✏️ Renommer", command=self.rename_slot).pack(side="left", padx=2)
        tk.Button(btn_frame, text="❌ Supprimer", bg="#f8d7da", command=self.delete_slot).pack(side="left", padx=2)

    def browse_save_dir(self):
        """Permet à l'utilisateur de choisir manuellement le dossier saved_game."""
        initial_dir = self.save_dir if self.save_dir else os.path.expanduser("~")
        selected_dir = filedialog.askdirectory(title="Sélectionner le dossier 'saved_game' de Talisman", initialdir=initial_dir)
        
        if selected_dir:
            self.save_dir = os.path.normpath(selected_dir)
            self.lbl_path.config(text=self.save_dir, fg="green")
            messagebox.showinfo("Chemin mis à jour", f"Nouveau dossier cible configuré :\n{self.save_dir}")

    def check_game_status(self):
        """Boucle de surveillance pour notifier si le jeu tourne."""
        if is_game_running():
            self.lbl_warn.config(text="⚠️ ATTENTION : Talisman est en cours d'exécution. Fermez-le avant toute action.")
        else:
            self.lbl_warn.config(text="")
        self.root.after(3000, self.check_game_status)

    def refresh_slots(self):
        """Met à jour la liste des dossiers de sauvegarde."""
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
                self.tree.insert("", "end", iid=d, values=(d, f"{num_files} fichiers", date_str))

    def get_selected_slot(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un slot dans la liste.")
            return None
        return selected[0]

    def save_current(self):
        if not self.save_dir or not os.path.isdir(self.save_dir):
            messagebox.showerror("Erreur", f"Le dossier de sauvegarde spécifié est introuvable ou invalide.")
            return

        files = [f for f in os.listdir(self.save_dir) if os.path.isfile(os.path.join(self.save_dir, f))]
        if not files:
            messagebox.showwarning("Vide", f"Aucun fichier de sauvegarde trouvé dans :\n{self.save_dir}")
            return

        default_name = f"partie_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
        name = simpledialog.askstring("Sauvegarder", "Nom du nouveau slot :", initialvalue=default_name)
        if not name:
            return

        name = name.replace("/", "_").replace("\\", "_")
        dest = os.path.join(SLOTS_DIR, name)

        if os.path.exists(dest):
            if not messagebox.askyesno("Écraser ?", f"Le slot '{name}' existe déjà. Voulez-vous l'écraser ?"):
                return
            shutil.rmtree(dest)

        os.makedirs(dest)
        for f in files:
            shutil.copy2(os.path.join(self.save_dir, f), os.path.join(dest, f))
        
        os.utime(dest, None)
        self.refresh_slots()
        messagebox.showinfo("Succès", f"Slot '{name}' sauvegardé avec succès.")

    def load_slot(self):
        if not self.save_dir:
            messagebox.showerror("Erreur", "Veuillez d'abord configurer un dossier de jeu valide.")
            return

        slot = self.get_selected_slot()
        if not slot:
            return

        if not messagebox.askyesno("Confirmation", f"ATTENTION : La partie actuelle en jeu va être ÉCRASÉE par '{slot}'.\nContinuer ?"):
            return

        slot_path = os.path.join(SLOTS_DIR, slot)
        os.makedirs(self.save_dir, exist_ok=True)

        for f in os.listdir(slot_path):
            src_file = os.path.join(slot_path, f)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, os.path.join(self.save_dir, f))

        messagebox.showinfo("Succès", f"Le slot '{slot}' a été chargé dans le jeu.")

    def rename_slot(self):
        slot = self.get_selected_slot()
        if not slot:
            return

        new_name = simpledialog.askstring("Renommer", f"Nouveau nom pour '{slot}' :", initialvalue=slot)
        if not new_name or new_name == slot:
            return

        new_name = new_name.replace("/", "_").replace("\\", "_")
        new_path = os.path.join(SLOTS_DIR, new_name)

        if os.path.exists(new_path):
            messagebox.showerror("Erreur", "Un slot portant ce nom existe déjà.")
            return

        os.rename(os.path.join(SLOTS_DIR, slot), new_path)
        self.refresh_slots()

    def delete_slot(self):
        slot = self.get_selected_slot()
        if not slot:
            return

        if messagebox.askyesno("Suppression", f"Êtes-vous sûr de vouloir supprimer DÉFINITIVEMENT le slot '{slot}' ?"):
            shutil.rmtree(os.path.join(SLOTS_DIR, slot))
            self.refresh_slots()

# --- Point d'entrée ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TalismanManagerGUI(root)
    root.mainloop()
