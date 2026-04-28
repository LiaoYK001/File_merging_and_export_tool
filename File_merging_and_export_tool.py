"""
通用文件合并工具 - 支持任意类型文件，GUI 操作，一键导出。

使用方法:
    python main.py
    python File_merging_and_export_tool.py
"""

import codecs
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import NamedTuple

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


TEXT_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "utf-8", "gb18030", "gbk")
EXPORT_ENCODINGS: tuple[str, ...] = ("utf-8", "utf-8-sig", "gb18030", "gbk")
NEWLINE_OPTIONS: tuple[str, ...] = ("CRLF", "LF")
NEWLINE_MAP = {"CRLF": "\r\n", "LF": "\n"}
DEFAULT_SEPARATOR_LENGTH = 80
DEFAULT_HEADER_SEPARATOR = "="
DEFAULT_SECTION_SEPARATOR = "─"
DEFAULT_BLOCK_SEPARATOR = "█"
BINARY_PREVIEW_BYTES = 512


class ExportSettings(NamedTuple):
    encoding: str
    newline: str
    newline_label: str
    separator_length: int
    header_separator: str
    section_separator: str
    block_separator: str


class MergeFilesApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("文件合并导出工具")
        self.root.geometry("820x600")
        self.root.minsize(680, 480)

        self.files: list[Path] = []
        self.drag_enabled = TkinterDnD is not None and isinstance(root, TkinterDnD.Tk)

        self._init_state()

        self._apply_theme()
        self._build_ui()
        self._register_drag_and_drop()
        self._bind_shortcuts()
        self._update_action_state()

    # ── 主题 ───────────────────────────────────────────────
    def _apply_theme(self):
        self.colors = {
            "bg":        "#1e1e24",
            "surface":   "#282832",
            "surface2":  "#32323e",
            "accent":    "#6c9cfc",
            "accent_h":  "#8db4ff",
            "danger":    "#fc6c6c",
            "danger_h":  "#ff8e8e",
            "text":      "#e8e8ee",
            "muted":     "#8888a0",
            "border":    "#3e3e50",
        }
        c = self.colors

        self.root.configure(bg=c["bg"])

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame",    background=c["bg"])
        style.configure("Surface.TFrame", background=c["surface"])
        style.configure("TLabel",    background=c["bg"], foreground=c["text"],
                         font=("Microsoft YaHei UI", 10))
        style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"],
                         font=("Microsoft YaHei UI", 9))
        style.configure("Title.TLabel", background=c["bg"], foreground=c["text"],
                         font=("Microsoft YaHei UI", 14, "bold"))
        style.configure("TButton",   font=("Microsoft YaHei UI", 10))
        style.configure("TCombobox", fieldbackground=c["surface2"],
                        background=c["surface2"], foreground=c["text"],
                        arrowcolor=c["text"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", c["surface2"])],
                  selectbackground=[("readonly", c["surface2"])],
                  selectforeground=[("readonly", c["text"])])

    # ── UI 构建 ─────────────────────────────────────────────
    def _build_ui(self):
        c = self.colors

        # 标题栏
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=16, pady=8)
        ttk.Label(header, text="文件合并导出工具", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="添加任意文件 → 一键合并导出", style="Muted.TLabel"
                  ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # 工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=16, pady=(0, 4))

        btn_cfg = {"font": ("Microsoft YaHei UI", 10), "relief": "flat",
                   "cursor": "hand2", "bd": 0, "padx": 14, "pady": 6}

        self.btn_add = tk.Button(toolbar, text="＋ 添加文件", bg=c["accent"],
                                 fg="#fff", activebackground=c["accent_h"],
                                 command=self._add_files, **btn_cfg)
        self.btn_add.pack(side="left", padx=(0, 6))
        self._bind_hover(self.btn_add, c["accent"], c["accent_h"])

        self.btn_add_dir = tk.Button(toolbar, text="📁 添加目录", bg=c["surface2"],
                                     fg=c["text"], activebackground=c["border"],
                                     command=self._add_directory, **btn_cfg)
        self.btn_add_dir.pack(side="left", padx=(0, 6))
        self._bind_hover(self.btn_add_dir, c["surface2"], c["border"])

        self.btn_remove = tk.Button(toolbar, text="✕ 移除选中", bg=c["surface2"],
                                    fg=c["text"], activebackground=c["border"],
                                    command=self._remove_selected, **btn_cfg)
        self.btn_remove.pack(side="left", padx=(0, 6))
        self._bind_hover(self.btn_remove, c["surface2"], c["border"])

        self.btn_clear = tk.Button(toolbar, text="清空列表", bg=c["surface2"],
                                   fg=c["danger"], activebackground=c["border"],
                                   command=self._clear_all, **btn_cfg)
        self.btn_clear.pack(side="left", padx=(0, 6))
        self._bind_hover(self.btn_clear, c["surface2"], c["border"])

        # 上移 / 下移
        self.btn_down = tk.Button(toolbar, text="↓", bg=c["surface2"],
                                  fg=c["text"], activebackground=c["border"],
                                  width=3, command=self._move_down, **btn_cfg)
        self.btn_down.pack(side="right")
        self._bind_hover(self.btn_down, c["surface2"], c["border"])

        self.btn_up = tk.Button(toolbar, text="↑", bg=c["surface2"],
                                fg=c["text"], activebackground=c["border"],
                                width=3, command=self._move_up, **btn_cfg)
        self.btn_up.pack(side="right", padx=(0, 4))
        self._bind_hover(self.btn_up, c["surface2"], c["border"])

        ttk.Label(toolbar, text="排序:", style="Muted.TLabel").pack(side="right", padx=(0, 2))

        # 导出配置
        settings_frame = tk.Frame(self.root, bg=c["border"], bd=0)
        settings_frame.pack(fill="x", padx=16, pady=(0, 8))

        settings_inner = tk.Frame(settings_frame, bg=c["surface"])
        settings_inner.pack(fill="x", padx=1, pady=1)

        settings_inner.grid_columnconfigure(7, weight=1)

        label_cfg = {
            "bg": c["surface"],
            "fg": c["text"],
            "font": ("Microsoft YaHei UI", 9),
        }
        hint_cfg = {
            "bg": c["surface"],
            "fg": c["muted"],
            "font": ("Microsoft YaHei UI", 9),
        }
        input_cfg = {
            "bg": c["surface2"],
            "fg": c["text"],
            "insertbackground": c["text"],
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": c["border"],
            "highlightcolor": c["accent"],
            "bd": 0,
        }

        tk.Label(settings_inner, text="导出设置", bg=c["surface"], fg=c["text"],
                 font=("Microsoft YaHei UI", 10, "bold")
                 ).grid(row=0, column=0, padx=(12, 12), pady=(10, 6), sticky="w")
        tk.Label(settings_inner, text="编码", **label_cfg).grid(
            row=0, column=1, padx=(0, 6), pady=(10, 6), sticky="e")
        ttk.Combobox(settings_inner, textvariable=self.export_encoding_var,
                     values=EXPORT_ENCODINGS, state="readonly", width=11
                     ).grid(row=0, column=2, padx=(0, 12), pady=(10, 6), sticky="w")
        tk.Label(settings_inner, text="换行", **label_cfg).grid(
            row=0, column=3, padx=(0, 6), pady=(10, 6), sticky="e")
        ttk.Combobox(settings_inner, textvariable=self.export_newline_var,
                     values=NEWLINE_OPTIONS, state="readonly", width=8
                     ).grid(row=0, column=4, padx=(0, 12), pady=(10, 6), sticky="w")
        tk.Label(settings_inner, text="长度", **label_cfg).grid(
            row=0, column=5, padx=(0, 6), pady=(10, 6), sticky="e")
        tk.Spinbox(settings_inner, from_=8, to=160, increment=4,
                   textvariable=self.separator_length_var, width=6,
                   buttonbackground=c["surface2"], **input_cfg
                   ).grid(row=0, column=6, padx=(0, 12), pady=(10, 6), sticky="w")

        tk.Label(settings_inner, text="头部分隔", **label_cfg).grid(
            row=1, column=1, padx=(0, 6), pady=(0, 8), sticky="e")
        tk.Entry(settings_inner, textvariable=self.header_separator_var, width=8,
                 **input_cfg).grid(row=1, column=2, padx=(0, 12), pady=(0, 8), sticky="w")
        tk.Label(settings_inner, text="文件分隔", **label_cfg).grid(
            row=1, column=3, padx=(0, 6), pady=(0, 8), sticky="e")
        tk.Entry(settings_inner, textvariable=self.section_separator_var, width=8,
                 **input_cfg).grid(row=1, column=4, padx=(0, 12), pady=(0, 8), sticky="w")
        tk.Label(settings_inner, text="文件块", **label_cfg).grid(
            row=1, column=5, padx=(0, 6), pady=(0, 8), sticky="e")
        tk.Entry(settings_inner, textvariable=self.block_separator_var, width=8,
                 **input_cfg).grid(row=1, column=6, padx=(0, 12), pady=(0, 8), sticky="w")

        tk.Label(settings_inner, textvariable=self.drag_status_var, anchor="e",
                 **hint_cfg).grid(row=2, column=0, columnspan=8,
                                  padx=12, pady=(0, 10), sticky="ew")

        # 文件列表（Treeview）
        self.list_frame = tk.Frame(self.root, bg=c["border"], bd=0)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self.list_inner = tk.Frame(self.list_frame, bg=c["surface"])
        self.list_inner.pack(fill="both", expand=True, padx=1, pady=1)

        columns = ("index", "name", "type", "size", "path")
        self.tree = ttk.Treeview(self.list_inner, columns=columns, show="headings",
                                 selectmode="extended", style="Treeview")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._update_action_state())

        style = ttk.Style()
        style.configure("Treeview", background=c["surface"], foreground=c["text"],
                        fieldbackground=c["surface"], font=("Microsoft YaHei UI", 9),
                        rowheight=28)
        style.configure("Treeview.Heading", background=c["surface2"],
                        foreground=c["muted"], font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Treeview", background=[("selected", c["accent"])],
                  foreground=[("selected", "#fff")])

        self.tree.heading("index", text="#")
        self.tree.heading("name",  text="文件名")
        self.tree.heading("type",  text="类型")
        self.tree.heading("size",  text="大小")
        self.tree.heading("path",  text="路径")

        self.tree.column("index", width=40,  minwidth=36,  stretch=False, anchor="center")
        self.tree.column("name",  width=200, minwidth=120, stretch=True)
        self.tree.column("type",  width=70,  minwidth=50,  stretch=False, anchor="center")
        self.tree.column("size",  width=80,  minwidth=60,  stretch=False, anchor="e")
        self.tree.column("path",  width=300, minwidth=100, stretch=True)

        scrollbar = ttk.Scrollbar(self.list_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 拖拽提示
        self.drop_label = tk.Label(self.list_inner, textvariable=self.drop_hint_var,
                       bg=c["surface"], fg=c["muted"],
                                   font=("Microsoft YaHei UI", 11))
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        # 底部栏
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=16, pady=(0, 12))

        self.status_var = tk.StringVar(value="就绪 — 已添加 0 个文件")
        ttk.Label(bottom, textvariable=self.status_var, style="Muted.TLabel"
                  ).pack(side="left")

        self.btn_export = tk.Button(bottom, text="导出合并文件  ▸", bg=c["accent"],
                                    fg="#fff", activebackground=c["accent_h"],
                                    font=("Microsoft YaHei UI", 11, "bold"),
                                    relief="flat", cursor="hand2",
                                    padx=24, pady=8, command=self._export)
        self.btn_export.pack(side="right")
        self._bind_hover(self.btn_export, c["accent"], c["accent_h"])

    # ── 辅助 ────────────────────────────────────────────────
    def _init_state(self):
        self.export_encoding_var = tk.StringVar(value=EXPORT_ENCODINGS[0])
        self.export_newline_var = tk.StringVar(value=NEWLINE_OPTIONS[0])
        self.separator_length_var = tk.IntVar(value=DEFAULT_SEPARATOR_LENGTH)
        self.header_separator_var = tk.StringVar(value=DEFAULT_HEADER_SEPARATOR)
        self.section_separator_var = tk.StringVar(value=DEFAULT_SECTION_SEPARATOR)
        self.block_separator_var = tk.StringVar(value=DEFAULT_BLOCK_SEPARATOR)
        self.drop_hint_var = tk.StringVar(value=self._drop_hint_text())
        self.drag_status_var = tk.StringVar(value=self._drag_status_text())

    def _bind_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def _drop_hint_text(self) -> str:
        if self.drag_enabled:
            return "拖拽文件或目录到此处，或点击上方按钮添加"
        return "点击上方按钮添加文件"

    def _drag_status_text(self) -> str:
        if self.drag_enabled:
            return "支持拖拽文件和目录到列表区域导入"
        return "当前环境未安装 tkinterdnd2，仍可使用按钮导入"

    def _register_drag_and_drop(self):
        if not self.drag_enabled or DND_FILES is None:
            return

        for widget in (self.list_inner, self.tree, self.drop_label):
            self._bind_drop_widget(widget)

    def _bind_drop_widget(self, widget):
        drop_target_register = getattr(widget, "drop_target_register", None)
        dnd_bind = getattr(widget, "dnd_bind", None)
        if not callable(drop_target_register) or not callable(dnd_bind):
            return

        drop_target_register(DND_FILES)
        dnd_bind("<<DragEnter>>", self._on_drag_enter)
        dnd_bind("<<DragLeave>>", self._on_drag_leave)
        dnd_bind("<<Drop>>", self._on_drop)

    def _on_drag_enter(self, _event):
        self._set_drop_zone_active(True)

    def _on_drag_leave(self, _event):
        self._set_drop_zone_active(False)

    def _on_drop(self, event):
        self._set_drop_zone_active(False)

        dropped_items = self.root.tk.splitlist(event.data)
        collected: list[Path] = []
        for item in dropped_items:
            path = Path(item)
            if path.is_dir():
                collected.extend(self._collect_directory_files(path))
            else:
                collected.append(path)

        added = self._add_paths(collected)
        if not added and dropped_items:
            self.status_var.set("未添加新文件，拖入内容可能已存在或无可用文件")

    def _set_drop_zone_active(self, active: bool):
        self.list_frame.config(bg=self.colors["accent"] if active else self.colors["border"])

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{size_bytes / 1024 ** 3:.2f} GB"

    def _make_file_key(self, path: Path) -> str:
        return os.path.normcase(str(path.resolve(strict=False)))

    def _separator_length(self) -> int:
        try:
            length = int(self.separator_length_var.get())
        except (tk.TclError, ValueError):
            length = DEFAULT_SEPARATOR_LENGTH

        length = max(1, min(160, length))
        self.separator_length_var.set(length)
        return length

    def _build_separator(self, pattern: str, default: str, length: int) -> str:
        normalized = pattern.strip() or default
        repeat_count = (length // len(normalized)) + 1
        return (normalized * repeat_count)[:length]

    def _current_export_settings(self) -> ExportSettings:
        separator_length = self._separator_length()
        return ExportSettings(
            encoding=self.export_encoding_var.get(),
            newline=NEWLINE_MAP.get(self.export_newline_var.get(), "\r\n"),
            newline_label=self.export_newline_var.get(),
            separator_length=separator_length,
            header_separator=self._build_separator(
                self.header_separator_var.get(),
                DEFAULT_HEADER_SEPARATOR,
                separator_length,
            ),
            section_separator=self._build_separator(
                self.section_separator_var.get(),
                DEFAULT_SECTION_SEPARATOR,
                separator_length,
            ),
            block_separator=self._build_separator(
                self.block_separator_var.get(),
                DEFAULT_BLOCK_SEPARATOR,
                separator_length,
            ),
        )

    def _calculate_total_size(self) -> tuple[int, int]:
        total_size = 0
        unavailable = 0
        for path in self.files:
            try:
                total_size += path.stat().st_size
            except OSError:
                unavailable += 1
        return total_size, unavailable

    def _selected_indices(self) -> list[int]:
        return sorted(self.tree.index(item) for item in self.tree.selection())

    def _set_selected_indices(self, indices: list[int]):
        items = self.tree.get_children()
        selected_items = [items[index] for index in indices if 0 <= index < len(items)]
        self.tree.selection_set(selected_items)
        if selected_items:
            self.tree.focus(selected_items[0])
            self.tree.see(selected_items[0])

    def _update_action_state(self):
        has_files = bool(self.files)
        has_selection = bool(self.tree.selection())

        file_state = "normal" if has_files else "disabled"
        selection_state = "normal" if has_selection else "disabled"

        self.btn_clear.config(state=file_state)
        self.btn_export.config(state=file_state)
        self.btn_remove.config(state=selection_state)
        self.btn_up.config(state=selection_state)
        self.btn_down.config(state=selection_state)

    def _bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda _event: self._add_files())
        self.root.bind("<Control-s>", lambda _event: self._export())
        self.root.bind("<Delete>", lambda _event: self._remove_selected())

    def _looks_like_text(self, text: str) -> bool:
        if not text:
            return True

        suspicious_chars = sum(
            1 for char in text if ord(char) < 32 and char not in "\n\r\t"
        )
        return suspicious_chars / len(text) < 0.02

    def _decode_text_bytes(self, raw: bytes) -> tuple[str | None, str | None]:
        if not raw:
            return "", "utf-8"

        candidates = list(TEXT_ENCODINGS)
        if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            candidates.insert(0, "utf-16")
        elif raw.count(0) > len(raw) // 4:
            candidates.extend(("utf-16-le", "utf-16-be"))

        tried = set()
        for encoding in candidates:
            if encoding in tried:
                continue
            tried.add(encoding)
            try:
                text = raw.decode(encoding)
            except UnicodeDecodeError:
                continue

            if self._looks_like_text(text):
                return text, encoding

        return None, None

    def _write_binary_preview(self, out, raw: bytes):
        preview = raw[:BINARY_PREVIEW_BYTES]
        out.write(f"Hex 预览 (前 {len(preview)} 字节):\n")

        hex_lines = []
        for offset in range(0, len(preview), 16):
            chunk = preview[offset:offset + 16]
            hex_part = " ".join(f"{byte:02x}" for byte in chunk)
            ascii_part = "".join(
                chr(byte) if 32 <= byte < 127 else "." for byte in chunk
            )
            hex_lines.append(f"{offset:08x}  {hex_part:<48s}  {ascii_part}")

        out.write("\n".join(hex_lines) + "\n")
        if len(raw) > BINARY_PREVIEW_BYTES:
            out.write(
                f"... 共 {len(raw)} 字节，仅显示前 {BINARY_PREVIEW_BYTES} 字节\n"
            )

    def _write_file_content(self, out, file_path: Path) -> str:
        raw = file_path.read_bytes()
        text, encoding = self._decode_text_bytes(raw)

        if text is not None:
            out.write(f"[文本文件 — 编码: {encoding}]\n")
            if text:
                out.write(text)
                if not text.endswith("\n"):
                    out.write("\n")
            else:
                out.write("[空文件]\n")
            return "text"

        out.write(f"[二进制文件 — 大小: {len(raw)} 字节]\n")
        self._write_binary_preview(out, raw)
        return "binary"

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, fp in enumerate(self.files, 1):
            ext = fp.suffix.lower() or "(无)"
            try:
                size = self._format_size(fp.stat().st_size)
            except OSError:
                size = "N/A"
            self.tree.insert("", "end", values=(i, fp.name, ext, size, str(fp)))

        count = len(self.files)
        total_size, unavailable = self._calculate_total_size()
        status = f"就绪 — 已添加 {count} 个文件"
        if count:
            status += f"，总大小 {self._format_size(total_size)}"
            if unavailable:
                status += f"，{unavailable} 个文件不可访问"

        self.status_var.set(status)
        self.drop_label.place_forget() if count else self.drop_label.place(
            relx=0.5, rely=0.5, anchor="center")
        self._update_action_state()

    def _add_paths(self, paths):
        existing = {self._make_file_key(path) for path in self.files}
        added = 0
        for p in paths:
            pp = Path(p)
            if not pp.is_file():
                continue

            normalized = pp.resolve(strict=False)
            file_key = self._make_file_key(normalized)
            if file_key in existing:
                continue

            self.files.append(normalized)
            existing.add(file_key)
            added += 1

        if added:
            self._refresh_tree()
        return added

    def _collect_directory_files(self, directory: Path) -> list[Path]:
        collected: list[Path] = []
        for root_dir, dirnames, filenames in os.walk(directory):
            dirnames.sort()
            for fn in sorted(filenames):
                collected.append(Path(root_dir) / fn)
        return collected

    # ── 按钮事件 ─────────────────────────────────────────────
    def _add_files(self):
        paths = filedialog.askopenfilenames(title="选择要合并的文件")
        if paths:
            self._add_paths(paths)

    def _add_directory(self):
        directory = filedialog.askdirectory(title="选择目录（将递归添加所有文件）")
        if directory:
            self._add_paths(self._collect_directory_files(Path(directory)))

    def _remove_selected(self):
        indices = self._selected_indices()
        if not indices:
            return

        for idx in reversed(indices):
            self.files.pop(idx)
        self._refresh_tree()

    def _clear_all(self):
        if self.files and messagebox.askyesno("确认", "确定要清空所有文件吗？"):
            self.files.clear()
            self._refresh_tree()

    def _move_up(self):
        indices = self._selected_indices()
        if not indices or indices[0] == 0:
            return

        for idx in indices:
            self.files[idx], self.files[idx - 1] = self.files[idx - 1], self.files[idx]

        self._refresh_tree()
        self._set_selected_indices([idx - 1 for idx in indices])

    def _move_down(self):
        indices = self._selected_indices()
        if not indices or indices[-1] >= len(self.files) - 1:
            return

        for idx in reversed(indices):
            self.files[idx], self.files[idx + 1] = self.files[idx + 1], self.files[idx]

        self._refresh_tree()
        self._set_selected_indices([idx + 1 for idx in indices])

    # ── 导出 ─────────────────────────────────────────────────
    def _export(self):
        if not self.files:
            messagebox.showwarning("提示", "请先添加文件！")
            return

        save_path = filedialog.asksaveasfilename(
            title="保存合并文件",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*"),
            ],
            initialfile="merged_files.txt",
        )
        if not save_path:
            return

        save_target = Path(save_path).resolve(strict=False)
        input_keys = {self._make_file_key(path) for path in self.files}
        if self._make_file_key(save_target) in input_keys:
            messagebox.showerror("导出失败", "输出文件不能与待合并文件是同一路径。")
            return

        export_settings = self._current_export_settings()
        sep = export_settings.header_separator
        thin = export_settings.section_separator
        block = export_settings.block_separator
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_size, _ = self._calculate_total_size()

        try:
            with open(save_path, "w", encoding=export_settings.encoding,
                      newline=export_settings.newline) as out:
                out.write(f"{sep}\n")
                out.write(f"文件合并导出\n")
                out.write(f"导出时间: {now}\n")
                out.write(f"导出编码: {export_settings.encoding}\n")
                out.write(f"换行风格: {export_settings.newline_label}\n")
                out.write(f"分隔长度: {export_settings.separator_length}\n")
                out.write(f"文件数量: {len(self.files)}\n")
                out.write(f"输入总大小: {self._format_size(total_size)}\n")
                out.write(f"{sep}\n\n")

                text_count = 0
                binary_count = 0

                for i, fp in enumerate(self.files, 1):
                    try:
                        display_size = self._format_size(fp.stat().st_size)
                    except OSError:
                        display_size = "N/A"

                    out.write(f"\n{block}\n")
                    out.write(f"文件 {i}/{len(self.files)}: {fp.name}\n")
                    out.write(f"路径: {fp}\n")
                    out.write(f"大小: {display_size}\n")
                    out.write(f"{block}\n\n")

                    try:
                        file_type = self._write_file_content(out, fp)
                        if file_type == "text":
                            text_count += 1
                        else:
                            binary_count += 1
                    except Exception as e:
                        out.write(f"[读取错误: {e}]\n")

                    out.write(f"\n{thin}\n")
                    out.write(f"↑ {fp.name} 结束\n")
                    out.write(f"{thin}\n\n")

                out.write(f"\n{sep}\n")
                out.write(f"合并完成 — 文本文件 {text_count} 个, "
                          f"二进制文件 {binary_count} 个\n")
                out.write(f"{sep}\n")

            file_size = Path(save_path).stat().st_size
            messagebox.showinfo(
                "导出成功",
                f"已成功合并 {len(self.files)} 个文件\n\n"
                f"保存至: {save_path}\n"
                f"文件大小: {self._format_size(file_size)}"
            )
        except Exception as e:
            messagebox.showerror("导出失败", f"写入文件时出错:\n{e}")


def main():
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    MergeFilesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
