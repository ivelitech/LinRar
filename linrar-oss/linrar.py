import os
import sys
import json
import shutil
import tarfile
import zipfile
import subprocess
import threading
import tempfile
import datetime
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False

APP_NAME = "LinRAR"
APP_VERSION = "0.0.5"

DONATE_URL = "https://github.com/sponsors/linrar-project"

CONFIG_DIR = os.path.expanduser("~/.config/linrar")
CONFIG_FILE = os.path.join(CONFIG_DIR, "prefs.json")


def load_prefs():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_prefs(prefs):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(prefs, f)
    except Exception:
        pass

TAR_MODES_WRITE = {
    ".tar": "w",
    ".tar.gz": "w:gz", ".tgz": "w:gz",
    ".tar.bz2": "w:bz2", ".tbz2": "w:bz2",
    ".tar.xz": "w:xz", ".txz": "w:xz",
}
TAR_MODES_READ = {
    ".tar": "r",
    ".tar.gz": "r:gz", ".tgz": "r:gz",
    ".tar.bz2": "r:bz2", ".tbz2": "r:bz2",
    ".tar.xz": "r:xz", ".txz": "r:xz",
}

ARCHIVE_EXTENSIONS = [
    ".tar.gz", ".tar.bz2", ".tar.xz",  
    ".tgz", ".tbz2", ".txz",
    ".zip", ".tar", ".rar", ".7z",
]

ICON_FOLDER = "\U0001F4C1"   # 📁
ICON_FILE = "\U0001F4C4"     # 📄
ICON_UP = "\u2B06"           # ⬆
ICON_ADD = "\u2795"          # ➕
ICON_EXTRACT = "\U0001F4E4"  # 📤
ICON_TEST = "\u2705"         # ✅
ICON_VIEW = "\U0001F441"     # 👁
ICON_DELETE = "\U0001F5D1"   # 🗑
ICON_FIND = "\U0001F50D"     # 🔍
ICON_WIZARD = "\U0001FA84"   # 🪄
ICON_INFO = "\u2139"         # ℹ
ICON_REPAIR = "\U0001F6E0"   # 🛠
ICON_HEART = "\u2764"        # ❤


def get_ext(path):
    """Return the recognized archive extension (handles .tar.gz etc.)."""
    name = os.path.basename(path).lower()
    for ext in ARCHIVE_EXTENSIONS:
        if name.endswith(ext):
            return ext
    return os.path.splitext(name)[1]


def human_size(n):
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024.0:
            return f"{int(n)} {unit}" if unit == "bytes" else f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def format_mtime(dt):
    if dt is None:
        return ""
    try:
        return dt.strftime("%-m/%-d/%Y %I:%M %p")
    except Exception:
        return dt.strftime("%m/%d/%Y %I:%M %p")


def which_any(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


class ArchiveError(Exception):
    pass


class Archive:
    def __init__(self, path):
        self.path = path
        self.ext = get_ext(path)

    def list_entries(self):
        """Return list of dicts: name, size, is_dir, mtime (datetime or None)."""
        if self.ext == ".zip":
            with zipfile.ZipFile(self.path) as z:
                out = []
                for info in z.infolist():
                    try:
                        mtime = datetime.datetime(*info.date_time)
                    except Exception:
                        mtime = None
                    out.append({
                        "name": info.filename.rstrip("/"),
                        "size": info.file_size,
                        "is_dir": info.filename.endswith("/"),
                        "mtime": mtime,
                    })
                return out
        elif self.ext in TAR_MODES_READ:
            mode = TAR_MODES_READ[self.ext]
            with tarfile.open(self.path, mode) as t:
                out = []
                for m in t.getmembers():
                    try:
                        mtime = datetime.datetime.fromtimestamp(m.mtime)
                    except Exception:
                        mtime = None
                    out.append({
                        "name": m.name.rstrip("/"),
                        "size": m.size,
                        "is_dir": m.isdir(),
                        "mtime": mtime,
                    })
                return out
        elif self.ext == ".rar":
            return self._list_rar()
        elif self.ext == ".7z":
            return self._list_via_7z()
        else:
            raise ArchiveError(f"Unsupported archive type: {self.ext}")

    def _list_rar(self):
        exe = which_any("unrar")
        if exe:
            result = subprocess.run([exe, "lb", self.path], capture_output=True, text=True)
            names = [l for l in result.stdout.splitlines() if l.strip()]
            return [{"name": n.rstrip("/"), "size": 0, "is_dir": n.endswith("/"), "mtime": None}
                    for n in names]
        exe = which_any("unar", "lsar")
        if exe:
            result = subprocess.run(["lsar", self.path] if shutil.which("lsar") else [exe, "-l", self.path],
                                     capture_output=True, text=True)
            names = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            return [{"name": n.rstrip("/"), "size": 0, "is_dir": n.endswith("/"), "mtime": None}
                    for n in names]
        raise ArchiveError(
            "'unrar' is not installed. Install it to browse .rar files, "
            "e.g.: sudo apt install unrar"
        )

    def _list_via_7z(self):
        exe = which_any("7z", "7za", "7zr")
        if not exe:
            raise ArchiveError(
                "7-Zip is not installed. Install p7zip to work with .7z files, "
                "e.g.: sudo apt install p7zip-full"
            )
        result = subprocess.run([exe, "l", "-slt", self.path],
                                 capture_output=True, text=True)
        entries, cur = [], {}
        for line in result.stdout.splitlines():
            if line.startswith("Path = ") and cur.get("name"):
                entries.append(cur)
                cur = {}
            if line.startswith("Path = "):
                cur["name"] = line[len("Path = "):].rstrip("/")
            elif line.startswith("Size = "):
                cur["size"] = int(line[len("Size = "):] or 0)
            elif line.startswith("Attributes = "):
                cur["is_dir"] = "D" in line
            elif line.startswith("Modified = "):
                raw = line[len("Modified = "):].strip()
                try:
                    cur["mtime"] = datetime.datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    cur["mtime"] = None
        if cur.get("name"):
            entries.append(cur)
        out = []
        for e in entries:
            if not e.get("name"):
                continue
            e.setdefault("size", 0)
            e.setdefault("is_dir", False)
            e.setdefault("mtime", None)
            out.append(e)
        return out

    def extract_all(self, dest_dir, progress_cb=None):
        os.makedirs(dest_dir, exist_ok=True)
        if self.ext == ".zip":
            with zipfile.ZipFile(self.path) as z:
                members = z.infolist()
                for i, m in enumerate(members):
                    z.extract(m, dest_dir)
                    if progress_cb:
                        progress_cb(i + 1, len(members), m.filename)
        elif self.ext in TAR_MODES_READ:
            mode = TAR_MODES_READ[self.ext]
            with tarfile.open(self.path, mode) as t:
                members = t.getmembers()
                for i, m in enumerate(members):
                    t.extract(m, dest_dir, filter="data")
                    if progress_cb:
                        progress_cb(i + 1, len(members), m.name)
        elif self.ext == ".rar":
            exe = which_any("unrar")
            if exe:
                subprocess.run([exe, "x", "-y", self.path, dest_dir + os.sep], check=True)
            else:
                exe = which_any("unar")
                if not exe:
                    raise ArchiveError(
                        "Install 'unrar' or 'unar' to extract .rar files, "
                        "e.g.: sudo apt install unrar"
                    )
                subprocess.run([exe, "-o", dest_dir, self.path], check=True)
        elif self.ext == ".7z":
            exe = which_any("7z", "7za", "7zr")
            if not exe:
                raise ArchiveError(
                    "Install p7zip to extract .7z files, "
                    "e.g.: sudo apt install p7zip-full"
                )
            subprocess.run([exe, "x", "-y", f"-o{dest_dir}", self.path], check=True)
        else:
            raise ArchiveError(f"Unsupported archive type: {self.ext}")

    def extract_names(self, names, dest_dir, progress_cb=None):
        """Extract only the given entry names (files, not whole-archive)."""
        os.makedirs(dest_dir, exist_ok=True)
        if self.ext == ".zip":
            with zipfile.ZipFile(self.path) as z:
                valid = set(z.namelist())
                for i, n in enumerate(names):
                    target = n if n in valid else n
                    z.extract(target, dest_dir)
                    if progress_cb:
                        progress_cb(i + 1, len(names), n)
        elif self.ext in TAR_MODES_READ:
            mode = TAR_MODES_READ[self.ext]
            with tarfile.open(self.path, mode) as t:
                for i, n in enumerate(names):
                    t.extract(n, dest_dir, filter="data")
                    if progress_cb:
                        progress_cb(i + 1, len(names), n)
        else:
        
            with tempfile.TemporaryDirectory() as tmp:
                self.extract_all(tmp, progress_cb=progress_cb)
                for n in names:
                    src = os.path.join(tmp, n)
                    dst = os.path.join(dest_dir, n)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    elif os.path.exists(src):
                        shutil.copy2(src, dst)

    def test(self):
        """Return (ok: bool, message: str)."""
        if self.ext == ".zip":
            with zipfile.ZipFile(self.path) as z:
                bad = z.testzip()
                if bad:
                    return False, f"Corrupt entry detected: {bad}"
                return True, f"All {len(z.namelist())} entries passed the CRC check."
        elif self.ext in TAR_MODES_READ:
            mode = TAR_MODES_READ[self.ext]
            count = 0
            try:
                with tarfile.open(self.path, mode) as t:
                    for m in t.getmembers():
                        if m.isfile():
                            f = t.extractfile(m)
                            if f:
                                f.read()
                        count += 1
                return True, f"All {count} entries read successfully."
            except Exception as e:
                return False, f"Archive test failed: {e}"
        elif self.ext == ".rar":
            exe = which_any("unrar")
            if not exe:
                return False, "'unrar' is not installed, cannot test this archive."
            r = subprocess.run([exe, "t", self.path], capture_output=True, text=True)
            return r.returncode == 0, (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else
                                        ("OK" if r.returncode == 0 else r.stderr.strip()))
        elif self.ext == ".7z":
            exe = which_any("7z", "7za", "7zr")
            if not exe:
                return False, "p7zip is not installed, cannot test this archive."
            r = subprocess.run([exe, "t", self.path], capture_output=True, text=True)
            ok = "Everything is Ok" in r.stdout
            return ok, ("Everything is Ok" if ok else r.stdout[-400:])
        return False, "Unsupported archive type."

    @staticmethod
    def create(archive_path, source_paths, progress_cb=None, arc_prefix=""):
        ext = get_ext(archive_path)
        if ext == ".zip":
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as z:
                all_files = list(_walk_all(source_paths, arc_prefix))
                for i, (full, arc) in enumerate(all_files):
                    z.write(full, arc)
                    if progress_cb:
                        progress_cb(i + 1, len(all_files), arc)
        elif ext in TAR_MODES_WRITE:
            mode = TAR_MODES_WRITE[ext]
            with tarfile.open(archive_path, mode) as t:
                all_files = list(_walk_all(source_paths, arc_prefix))
                for i, (full, arc) in enumerate(all_files):
                    t.add(full, arcname=arc)
                    if progress_cb:
                        progress_cb(i + 1, len(all_files), arc)
        else:
            raise ArchiveError(
                f"Creating {ext} archives isn't supported (proprietary format). "
                f"Use .zip or .tar.gz instead."
            )


def _walk_all(paths, arc_prefix=""):
    """Yield (full_path, arcname) pairs for a list of files/dirs."""
    prefix = (arc_prefix.strip("/") + "/") if arc_prefix else ""
    for p in paths:
        p = Path(p)
        base = p.parent
        if p.is_dir():
            for root, dirs, files in os.walk(p):
                for f in files:
                    full = os.path.join(root, f)
                    arc = prefix + os.path.relpath(full, base)
                    yield full, arc
                if not files and not dirs:
                    yield root, prefix + os.path.relpath(root, base) + "/"
        else:
            yield str(p), prefix + p.name


def get_dir_listing(entries, current_path):
    """Given the full flat entry list, return only the immediate children
    of current_path (like a folder view in a file manager)."""
    current_path = current_path.strip("/")
    prefix = current_path + "/" if current_path else ""
    children = {}
    for e in entries:
        name = e["name"]
        if prefix and not name.startswith(prefix):
            continue
        rest = name[len(prefix):] if prefix else name
        if not rest:
            continue
        parts = rest.split("/", 1)
        child_name = parts[0]
        is_subdir = len(parts) > 1 or e["is_dir"]
        if child_name not in children:
            children[child_name] = {"name": child_name, "is_dir": is_subdir,
                                     "size": 0, "mtime": None}
        if is_subdir:
            children[child_name]["is_dir"] = True
        else:
            children[child_name]["size"] = e.get("size", 0)
            children[child_name]["mtime"] = e.get("mtime")
    return list(children.values())



_AppBase = TkinterDnD.Tk if HAS_DND else tk.Tk


class LinRARApp(_AppBase):
    def __init__(self, open_path=None):
        super().__init__()
        self.title(f"{APP_NAME}")
        self.geometry("900x580")
        self.minsize(600, 380)

        self.current_archive = None
        self.entries_cache = []
        self.current_folder = ""       
        self.row_data = {}             
        self.prefs = load_prefs()

        self._build_menu()
        self._build_toolbar()
        self._build_pathbar()
        self._build_listing()
        self._build_statusbar()
        self._bind_shortcuts()
        self._update_title()

        if open_path:
            self.open_archive(open_path)

        if not self.prefs.get("hide_support_popup"):
            self.after(700, self.show_support_popup)


    def _build_menu(self):
        menubar = tk.Menu(self)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Open...", accelerator="Ctrl+O", command=self.action_open)
        m_file.add_command(label="New Archive...", accelerator="Ctrl+N", command=self.action_new)
        m_file.add_command(label="Close Archive", command=self.action_close)
        m_file.add_separator()
        m_file.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=m_file)

        m_cmd = tk.Menu(menubar, tearoff=0)
        m_cmd.add_command(label="Add Files...", command=self.action_add)
        m_cmd.add_command(label="Extract To...", command=self.action_extract_all)
        m_cmd.add_command(label="Extract Selected...", command=self.action_extract_selected)
        m_cmd.add_command(label="Test Archive", command=self.action_test)
        m_cmd.add_command(label="Delete Selected", command=self.action_delete_selected)
        m_cmd.add_command(label="Repair Archive", command=self.action_repair)
        menubar.add_cascade(label="Commands", menu=m_cmd)

        m_tools = tk.Menu(menubar, tearoff=0)
        m_tools.add_command(label="Find...", accelerator="Ctrl+F", command=self.action_find)
        menubar.add_cascade(label="Tools", menu=m_tools)

        m_fav = tk.Menu(menubar, tearoff=0)
        m_fav.add_command(label="Add to Favorites", command=self.action_favorites_stub)
        menubar.add_cascade(label="Favorites", menu=m_fav)

        m_opt = tk.Menu(menubar, tearoff=0)
        m_opt.add_command(label="Preferences...", command=self.action_options_stub)
        menubar.add_cascade(label="Options", menu=m_opt)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label=f"{ICON_HEART} Support LinRAR...", command=self.action_donate)
        m_help.add_separator()
        m_help.add_command(label="About LinRAR", command=self.action_about)
        menubar.add_cascade(label="Help", menu=m_help)

        self.config(menu=menubar)

   
    def _toolbar_button(self, parent, icon, label, command):
        frame = tk.Frame(parent, bd=1, relief="flat", cursor="hand2")
        icon_lbl = tk.Label(frame, text=icon, font=("Sans", 18))
        icon_lbl.pack(side=tk.TOP)
        text_lbl = tk.Label(frame, text=label, font=("Sans", 8))
        text_lbl.pack(side=tk.TOP)
        for w in (frame, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", lambda e, f=frame: f.configure(relief="raised"))
            w.bind("<Leave>", lambda e, f=frame: f.configure(relief="flat"))
        frame.pack(side=tk.LEFT, padx=6, pady=2)
        return frame

    def _build_toolbar(self):
        bar = tk.Frame(self, bd=1, relief="raised")
        bar.pack(side=tk.TOP, fill=tk.X)

        self._toolbar_button(bar, ICON_ADD, "Add", self.action_add)
        self._toolbar_button(bar, ICON_EXTRACT, "Extract To", self.action_extract_all)
        self._toolbar_button(bar, ICON_TEST, "Test", self.action_test)
        self._toolbar_button(bar, ICON_VIEW, "View", self.action_view)
        self._toolbar_button(bar, ICON_DELETE, "Delete", self.action_delete_selected)
        ttk.Separator(bar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        self._toolbar_button(bar, ICON_FIND, "Find", self.action_find)
        self._toolbar_button(bar, ICON_WIZARD, "Wizard", self.action_wizard)
        self._toolbar_button(bar, ICON_INFO, "Info", self.action_info)
        self._toolbar_button(bar, ICON_REPAIR, "Repair", self.action_repair)

        
        donate = tk.Label(bar, text=f"{ICON_HEART} Donate", font=("Sans", 9),
                           fg="#a83246", cursor="hand2", padx=10)
        donate.pack(side=tk.RIGHT, padx=6)
        donate.bind("<Button-1>", lambda e: self.action_donate())

   
    def _build_pathbar(self):
        bar = tk.Frame(self, bd=1, relief="sunken")
        bar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        self.up_btn = tk.Label(bar, text=ICON_UP, font=("Sans", 12), cursor="hand2")
        self.up_btn.pack(side=tk.LEFT, padx=(4, 8))
        self.up_btn.bind("<Button-1>", lambda e: self.action_go_up())

        self.path_var = tk.StringVar(value="No archive open")
        path_entry = tk.Entry(bar, textvariable=self.path_var, state="readonly",
                               relief="flat", bd=0, font=("Sans", 10))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

   
    def _build_listing(self):
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.listing_container = container

       
        self.tree_frame = tk.Frame(container)
        columns = ("name", "size", "type", "modified")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings",
                                  selectmode="extended")
        self.tree.heading("name", text="Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("type", text="Type")
        self.tree.heading("modified", text="Modified")
        self.tree.column("name", width=380, anchor="w")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("type", width=110, anchor="w")
        self.tree.column("modified", width=150, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.bind("<Double-1>", self.on_double_click)

        
        self.drop_frame = tk.Frame(container, bg="#f5f5f5", highlightthickness=2,
                                    highlightbackground="#c9c9c9", highlightcolor="#c9c9c9")
        inner = tk.Frame(self.drop_frame, bg="#f5f5f5")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(inner, text=ICON_FOLDER, font=("Sans", 40), bg="#f5f5f5").pack()
        open_btn = tk.Button(inner, text=f"{ICON_EXTRACT}  Open Archive", font=("Sans", 12),
                              padx=16, pady=8, command=self.action_open)
        open_btn.pack(pady=(10, 8))
        dnd_text = "or drag and drop an archive file here" if HAS_DND else \
                    "(drag & drop needs the optional tkinterdnd2 package)"
        tk.Label(inner, text=dnd_text, font=("Sans", 9), fg="#777777",
                 bg="#f5f5f5").pack()

        self.show_drop_zone()

       
        if HAS_DND:
            for widget in (self, self.drop_frame, inner, self.tree):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self.on_drop_files)

    def show_drop_zone(self):
        self.tree_frame.pack_forget()
        self.drop_frame.pack(fill=tk.BOTH, expand=True)

    def show_tree(self):
        self.drop_frame.pack_forget()
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

    def on_drop_files(self, event):
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            paths = [event.data]
        if not paths:
            return
        path = paths[0]
        if get_ext(path) not in (".zip", ".tar", ".rar", ".7z", *TAR_MODES_READ):
            messagebox.showinfo(APP_NAME, f"'{os.path.basename(path)}' isn't a "
                                 f"supported archive format.")
            return
        self.open_archive(path)

    def _build_statusbar(self):
        bottom = tk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(2, 0))

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(bottom, textvariable=self.status_var, anchor="w", relief="sunken",
                 bd=1).pack(side=tk.TOP, fill=tk.X)

    def _bind_shortcuts(self):
        self.bind("<Control-o>", lambda e: self.action_open())
        self.bind("<Control-n>", lambda e: self.action_new())
        self.bind("<Control-f>", lambda e: self.action_find())
        self.bind("<Delete>", lambda e: self.action_delete_selected())
        self.bind("<BackSpace>", lambda e: self.action_go_up())

    
    def _update_title(self):
        if self.current_archive:
            self.title(f"{os.path.basename(self.current_archive.path)} - {APP_NAME}")
        else:
            self.title(APP_NAME)

    def set_status(self, text):
        self.status_var.set(text)
        self.update_idletasks()

    def run_progress(self, current, total, name):
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = current
        self.set_status(f"{current}/{total}: {name}")
        self.update_idletasks()

    def full_path_of(self, child_name):
        return f"{self.current_folder}/{child_name}" if self.current_folder else child_name

    def expand_to_full_names(self, entries):
        """Given selected child entries (possibly folders), return the full
        archive-relative names of every leaf file/folder they cover."""
        names = []
        for e in entries:
            full = self.full_path_of(e["name"])
            if e["is_dir"]:
                prefix = full + "/"
                names.extend(x["name"] for x in self.entries_cache
                             if x["name"] == full or x["name"].startswith(prefix))
                if not any(x["name"].startswith(prefix) or x["name"] == full
                           for x in self.entries_cache):
                    names.append(full)
            else:
                names.append(full)
        return names

    def refresh_listing(self):
        if not self.current_archive:
            self.tree.delete(*self.tree.get_children())
            self.show_drop_zone()
            return
        try:
            self.entries_cache = self.current_archive.list_entries()
        except ArchiveError as e:
            messagebox.showerror(APP_NAME, str(e))
            return
        self.current_folder = ""
        self.show_tree()
        self.render_current_folder()

    def render_current_folder(self):
        self.tree.delete(*self.tree.get_children())
        self.row_data.clear()

        children = get_dir_listing(self.entries_cache, self.current_folder)
        children.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))

        n_folders = sum(1 for e in children if e["is_dir"])
        n_files = len(children) - n_folders

        for e in children:
            icon = ICON_FOLDER if e["is_dir"] else ICON_FILE
            kind = "File folder" if e["is_dir"] else self._type_label(e["name"])
            size = "" if e["is_dir"] else human_size(e.get("size", 0))
            modified = format_mtime(e.get("mtime"))
            iid = self.tree.insert("", tk.END,
                                    values=(f"{icon}  {e['name']}", size, kind, modified))
            self.row_data[iid] = e

        archive_label = os.path.basename(self.current_archive.path) if self.current_archive else ""
        shown_path = f"{archive_label}:/{self.current_folder}" if self.current_folder else f"{archive_label}:/"
        self.path_var.set(shown_path)
        self.up_btn.configure(fg="black" if self.current_folder else "gray")

        self.set_status(f"Total {n_folders} folder(s), {n_files} file(s)")
        self.progress["value"] = 0

    def _type_label(self, name):
        ext = os.path.splitext(name)[1].lstrip(".").upper()
        return f"{ext} File" if ext else "File"

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        entry = self.row_data.get(sel[0])
        if not entry:
            return
        if entry["is_dir"]:
            self.current_folder = self.full_path_of(entry["name"])
            self.render_current_folder()
        else:
            self.action_view()

    def action_go_up(self):
        if not self.current_folder:
            return
        parts = self.current_folder.rstrip("/").split("/")
        self.current_folder = "/".join(parts[:-1])
        self.render_current_folder()

  
    def open_archive(self, path):
        try:
            self.current_archive = Archive(path)
            self.refresh_listing()
            self._update_title()
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Could not open archive:\n{e}")

    def action_open(self):
        path = filedialog.askopenfilename(
            title="Open Archive",
            filetypes=[
                ("All supported", "*.zip *.tar *.tar.gz *.tgz *.tar.bz2 *.tbz2 "
                                   "*.tar.xz *.txz *.rar *.7z"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.open_archive(path)

    def action_close(self):
        self.current_archive = None
        self.entries_cache = []
        self.current_folder = ""
        self.tree.delete(*self.tree.get_children())
        self.path_var.set("No archive open")
        self.set_status("Ready")
        self.show_drop_zone()
        self._update_title()

    def action_new(self):
        files = filedialog.askopenfilenames(title="Select files/folders to archive")
        if not files:
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Archive As",
            defaultextension=".zip",
            filetypes=[("Zip", "*.zip"), ("Tar GZ", "*.tar.gz"),
                       ("Tar BZ2", "*.tar.bz2"), ("Tar XZ", "*.tar.xz"),
                       ("Tar", "*.tar")],
        )
        if not save_path:
            return

        def worker():
            try:
                Archive.create(save_path, files, progress_cb=self.run_progress)
                self.set_status(f"Created {save_path}")
                self.open_archive(save_path)
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Failed to create archive:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

   
    def action_add(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open or create an archive first.")
            return
        if self.current_archive.ext not in (".zip", *TAR_MODES_WRITE):
            messagebox.showinfo(APP_NAME, "Adding files is only supported for zip/tar archives.")
            return
        files = filedialog.askopenfilenames(title="Select files to add")
        if not files:
            return

        def worker():
            try:
                ext = self.current_archive.ext
                prefix = self.current_folder
                if ext == ".zip":
                    with zipfile.ZipFile(self.current_archive.path, "a", zipfile.ZIP_DEFLATED) as z:
                        for i, f in enumerate(files):
                            arcname = f"{prefix}/{os.path.basename(f)}" if prefix else os.path.basename(f)
                            z.write(f, arcname)
                            self.run_progress(i + 1, len(files), arcname)
                else:
                   
                    tmpdir = tempfile.mkdtemp()
                    self.current_archive.extract_all(tmpdir)
                    target_dir = os.path.join(tmpdir, prefix) if prefix else tmpdir
                    os.makedirs(target_dir, exist_ok=True)
                    for f in files:
                        shutil.copy(f, target_dir)
                    Archive.create(self.current_archive.path,
                                    [os.path.join(tmpdir, p) for p in os.listdir(tmpdir)],
                                    progress_cb=self.run_progress)
                    shutil.rmtree(tmpdir, ignore_errors=True)
                self.set_status("Files added")
                self.refresh_listing()
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Failed to add files:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def action_extract_all(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return
        dest = filedialog.askdirectory(title="Extract To")
        if not dest:
            return

        def worker():
            try:
                self.current_archive.extract_all(dest, progress_cb=self.run_progress)
                self.set_status(f"Extracted to {dest}")
                messagebox.showinfo(APP_NAME, f"Extraction complete:\n{dest}")
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Extraction failed:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def action_extract_selected(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Select one or more items first.")
            return
        entries = [self.row_data[i] for i in sel]
        names = self.expand_to_full_names(entries)
        dest = filedialog.askdirectory(title="Extract Selected To")
        if not dest:
            return

        def worker():
            try:
                self.current_archive.extract_names(names, dest, progress_cb=self.run_progress)
                self.set_status(f"Extracted {len(names)} item(s) to {dest}")
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Extraction failed:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def action_delete_selected(self):
        if not self.current_archive:
            return
        sel = self.tree.selection()
        if not sel:
            return
        ext = self.current_archive.ext
        if ext not in (".zip", *TAR_MODES_WRITE):
            messagebox.showinfo(APP_NAME, "Deleting entries is only supported for zip/tar archives.")
            return
        entries = [self.row_data[i] for i in sel]
        names = set(self.expand_to_full_names(entries))
        if not messagebox.askyesno(APP_NAME, f"Remove {len(names)} item(s) from the archive?"):
            return

        def worker():
            try:
                path = self.current_archive.path
                tmp = path + ".tmp"
                if ext == ".zip":
                    with zipfile.ZipFile(path) as zin, \
                         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                        for item in zin.infolist():
                            if item.filename.rstrip("/") not in names:
                                zout.writestr(item, zin.read(item.filename))
                else:
                    mode_r = TAR_MODES_READ[ext]
                    mode_w = TAR_MODES_WRITE[ext]
                    with tarfile.open(path, mode_r) as tin, \
                         tarfile.open(tmp, mode_w) as tout:
                        for m in tin.getmembers():
                            if m.name.rstrip("/") not in names:
                                f = tin.extractfile(m)
                                tout.addfile(m, f)
                os.replace(tmp, path)
                self.set_status(f"Removed {len(names)} item(s)")
                self.refresh_listing()
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Failed to delete entries:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    
    def action_test(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return

        def worker():
            self.set_status("Testing archive...")
            ok, msg = self.current_archive.test()
            self.set_status("Ready")
            if ok:
                messagebox.showinfo(APP_NAME, f"Archive test passed.\n\n{msg}")
            else:
                messagebox.showerror(APP_NAME, f"Archive test failed.\n\n{msg}")

        threading.Thread(target=worker, daemon=True).start()

    def action_view(self):
        if not self.current_archive:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Select a file to view first.")
            return
        entry = self.row_data[sel[0]]
        if entry["is_dir"]:
            self.current_folder = self.full_path_of(entry["name"])
            self.render_current_folder()
            return
        full_name = self.full_path_of(entry["name"])

        def worker():
            try:
                tmp = tempfile.mkdtemp()
                self.current_archive.extract_names([full_name], tmp)
                target = os.path.join(tmp, full_name)
                opener = which_any("xdg-open")
                if opener:
                    subprocess.Popen([opener, target])
                    self.set_status(f"Opened {full_name}")
                else:
                    messagebox.showinfo(APP_NAME, f"Extracted to:\n{target}\n\n"
                                         f"(install xdg-utils to open it automatically)")
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Could not view file:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def action_info(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return
        path = self.current_archive.path
        try:
            disk_size = os.path.getsize(path)
        except OSError:
            disk_size = 0
        total_uncompressed = sum(e.get("size", 0) for e in self.entries_cache if not e["is_dir"])
        n_files = sum(1 for e in self.entries_cache if not e["is_dir"])
        n_dirs = sum(1 for e in self.entries_cache if e["is_dir"])
        msg = (
            f"Archive: {os.path.basename(path)}\n"
            f"Location: {os.path.dirname(os.path.abspath(path))}\n"
            f"Format: {self.current_archive.ext}\n"
            f"Archive size on disk: {human_size(disk_size)}\n"
            f"Total uncompressed size: {human_size(total_uncompressed)}\n"
            f"Files: {n_files}   Folders: {n_dirs}"
        )
        messagebox.showinfo(f"{APP_NAME} - Archive Info", msg)

    def action_repair(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return
        ext = self.current_archive.ext
        if ext != ".zip":
            messagebox.showinfo(APP_NAME,
                                 "Automatic repair is only implemented for .zip archives "
                                 "in this build. For other formats, try re-downloading "
                                 "the file or using the archive's original source.")
            return

        def worker():
            self.set_status("Repairing archive...")
            path = self.current_archive.path
            fixed_path = os.path.splitext(path)[0] + "_fixed.zip"
            saved, skipped = 0, 0
            try:
                with zipfile.ZipFile(path) as zin, \
                     zipfile.ZipFile(fixed_path, "w", zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        try:
                            data = zin.read(item.filename)
                            zout.writestr(item, data)
                            saved += 1
                        except Exception:
                            skipped += 1
                self.set_status("Ready")
                messagebox.showinfo(
                    APP_NAME,
                    f"Repair complete.\nRecovered {saved} entrie(s), skipped {skipped} "
                    f"corrupted entrie(s).\nSaved as:\n{fixed_path}"
                )
            except Exception as e:
                self.set_status("Ready")
                messagebox.showerror(APP_NAME, f"Repair failed:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def action_find(self):
        if not self.current_archive:
            messagebox.showinfo(APP_NAME, "Open an archive first.")
            return
        query = simpledialog.askstring(f"{APP_NAME} - Find", "Find text in file names:")
        if not query:
            return
        query_l = query.lower()
        matches = [e for e in self.entries_cache if query_l in e["name"].lower()]
        if not matches:
            messagebox.showinfo(APP_NAME, f"No matches found for '{query}'.")
            return

        win = tk.Toplevel(self)
        win.title(f"Find results for '{query}' ({len(matches)})")
        win.geometry("560x360")
        lb = tk.Listbox(win, font=("Monospace", 10))
        lb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        for m in matches:
            kind = "[DIR] " if m["is_dir"] else "      "
            lb.insert(tk.END, f"{kind}{m['name']}")

        def go_to_selected(event=None):
            sel = lb.curselection()
            if not sel:
                return
            entry = matches[sel[0]]
            folder = "/".join(entry["name"].split("/")[:-1])
            self.current_folder = folder
            self.render_current_folder()
            for iid, e in self.row_data.items():
                if e["name"] == entry["name"].split("/")[-1]:
                    self.tree.selection_set(iid)
                    self.tree.see(iid)
                    break
            win.destroy()

        lb.bind("<Double-1>", go_to_selected)
        tk.Button(win, text="Go to selected", command=go_to_selected).pack(pady=(0, 6))

    def action_wizard(self):
        win = tk.Toplevel(self)
        win.title(f"{APP_NAME} Wizard")
        win.geometry("380x160")
        tk.Label(win, text="What would you like to do?", font=("Sans", 11)).pack(pady=(16, 10))

        def do_extract():
            win.destroy()
            self.action_open()

        def do_create():
            win.destroy()
            self.action_new()

        tk.Button(win, text="Create a new archive", width=30, command=do_create).pack(pady=4)
        tk.Button(win, text="Open / extract an existing archive", width=30,
                  command=do_extract).pack(pady=4)

    def action_favorites_stub(self):
        messagebox.showinfo(APP_NAME, "Favorites are not implemented in this build.")

    def action_options_stub(self):
        messagebox.showinfo(APP_NAME, "No configurable preferences yet — "
                             "LinRAR works out of the box.")

    def action_about(self):
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} {APP_VERSION}\n\n"
            "A WinRAR-style archive manager for Linux.\n"
            "Built with Python 3 and Tkinter.\n\n"
            "Supports: zip, tar, tar.gz, tar.bz2, tar.xz natively;\n"
            "rar and 7z extraction via unrar / p7zip if installed.\n\n"
            "LinRAR is free and open source, with no locked features\n"
            "and no trial period — now or ever."
        )

    
    def action_donate(self):
        try:
            webbrowser.open(DONATE_URL)
        except Exception:
            pass
        messagebox.showinfo(
            f"{ICON_HEART} Thank you",
            "Thanks for considering supporting LinRAR.\n\n"
            "A page should have opened in your browser. LinRAR stays fully "
            "functional either way — this is never required."
        )

    def show_support_popup(self):
        """A one-time-per-launch, easily dismissed note about supporting
        the project — not a locked trial screen, not a countdown, and it
        never blocks you from using the app."""
        win = tk.Toplevel(self)
        win.title("Support LinRAR")
        win.geometry("380x230")
        win.resizable(False, False)
        win.transient(self)

      
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 230) // 2
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        tk.Label(win, text=ICON_HEART, font=("Sans", 28), fg="#a83246").pack(pady=(18, 4))
        tk.Label(win, text="LinRAR is free, and always will be.",
                 font=("Sans", 11, "bold")).pack()
        tk.Label(
            win,
            text="If it's useful to you, a small donation helps keep it\n"
                 "going. No pressure — the app works exactly the same\n"
                 "either way, today and always.",
            font=("Sans", 9), justify="center"
        ).pack(pady=(6, 14))

        dont_show_var = tk.IntVar(value=0)
        tk.Checkbutton(win, text="Don't show this again", variable=dont_show_var,
                        font=("Sans", 8)).pack()

        def dismiss(went_to_donate=False):
            if dont_show_var.get() or went_to_donate:
                self.prefs["hide_support_popup"] = True
                save_prefs(self.prefs)
            win.destroy()

        btn_row = tk.Frame(win)
        btn_row.pack(pady=(12, 0))
        tk.Button(btn_row, text=f"{ICON_HEART} Support LinRAR",
                  command=lambda: (self.action_donate(), dismiss(went_to_donate=True))
                  ).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="Maybe later", command=lambda: dismiss()
                  ).pack(side=tk.LEFT, padx=6)

        win.protocol("WM_DELETE_WINDOW", lambda: dismiss())


def main():
    open_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = LinRARApp(open_path=open_path)
    app.mainloop()


if __name__ == "__main__":
    main()
