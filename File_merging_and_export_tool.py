"""
通用文件合并工具 - 支持任意类型文件，GUI 操作，一键导出。

使用方法:
    python merge_files_gui.py
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime


class MergeFilesApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("文件合并导出工具")
        self.root.geometry("820x600")
        self.root.minsize(680, 480)

        self.files: list[Path] = []

        self._apply_theme()
        self._build_ui()

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

    # ── UI 构建 ─────────────────────────────────────────────
    def _build_ui(self):
        c = self.colors
        pad = {"padx": 16, "pady": 8}

        # 标题栏
        header = ttk.Frame(self.root)
        header.pack(fill="x", **pad)
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

        # 文件列表（Treeview）
        list_frame = tk.Frame(self.root, bg=c["border"], bd=0)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        inner = tk.Frame(list_frame, bg=c["surface"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        columns = ("index", "name", "type", "size", "path")
        self.tree = ttk.Treeview(inner, columns=columns, show="headings",
                                 selectmode="extended", style="Treeview")

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

        scrollbar = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 拖拽提示
        self.drop_label = tk.Label(inner, text="点击上方按钮添加文件",
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
    def _bind_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{size_bytes / 1024 ** 3:.2f} GB"

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
        self.status_var.set(f"就绪 — 已添加 {count} 个文件")
        self.drop_label.place_forget() if count else self.drop_label.place(
            relx=0.5, rely=0.5, anchor="center")

    def _add_paths(self, paths):
        existing = set(self.files)
        added = 0
        for p in paths:
            pp = Path(p)
            if pp.is_file() and pp not in existing:
                self.files.append(pp)
                existing.add(pp)
                added += 1
        if added:
            self._refresh_tree()

    # ── 按钮事件 ─────────────────────────────────────────────
    def _add_files(self):
        paths = filedialog.askopenfilenames(title="选择要合并的文件")
        if paths:
            self._add_paths(paths)

    def _add_directory(self):
        directory = filedialog.askdirectory(title="选择目录（将递归添加所有文件）")
        if directory:
            collected = []
            for root_dir, _, filenames in os.walk(directory):
                for fn in sorted(filenames):
                    collected.append(Path(root_dir) / fn)
            self._add_paths(collected)

    def _remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        indices = sorted(
            [self.tree.index(s) for s in selected], reverse=True)
        for idx in indices:
            self.files.pop(idx)
        self._refresh_tree()

    def _clear_all(self):
        if self.files and messagebox.askyesno("确认", "确定要清空所有文件吗？"):
            self.files.clear()
            self._refresh_tree()

    def _move_up(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        if idx > 0:
            self.files[idx], self.files[idx - 1] = self.files[idx - 1], self.files[idx]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[idx - 1])

    def _move_down(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        if idx < len(self.files) - 1:
            self.files[idx], self.files[idx + 1] = self.files[idx + 1], self.files[idx]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[idx + 1])

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

        sep = "=" * 80
        thin = "─" * 80
        block = "█" * 80
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(save_path, "w", encoding="utf-8") as out:
                out.write(f"{sep}\n")
                out.write(f"文件合并导出\n")
                out.write(f"导出时间: {now}\n")
                out.write(f"文件数量: {len(self.files)}\n")
                out.write(f"{sep}\n\n")

                text_count = 0
                binary_count = 0

                for i, fp in enumerate(self.files, 1):
                    out.write(f"\n{block}\n")
                    out.write(f"文件 {i}/{len(self.files)}: {fp.name}\n")
                    out.write(f"路径: {fp}\n")
                    out.write(f"{block}\n\n")

                    try:
                        content = fp.read_text(encoding="utf-8")
                        out.write(content)
                        if not content.endswith("\n"):
                            out.write("\n")
                        text_count += 1
                    except UnicodeDecodeError:
                        try:
                            raw = fp.read_bytes()
                            out.write(f"[二进制文件 — 大小: {len(raw)} 字节]\n")
                            # 以十六进制 dump 前 512 字节
                            preview = raw[:512]
                            hex_lines = []
                            for offset in range(0, len(preview), 16):
                                chunk = preview[offset:offset + 16]
                                hex_part = " ".join(f"{b:02x}" for b in chunk)
                                ascii_part = "".join(
                                    chr(b) if 32 <= b < 127 else "." for b in chunk)
                                hex_lines.append(
                                    f"{offset:08x}  {hex_part:<48s}  {ascii_part}")
                            out.write("Hex 预览 (前 512 字节):\n")
                            out.write("\n".join(hex_lines) + "\n")
                            if len(raw) > 512:
                                out.write(f"... 共 {len(raw)} 字节，仅显示前 512 字节\n")
                            binary_count += 1
                        except Exception as e:
                            out.write(f"[读取错误: {e}]\n")
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
    root = tk.Tk()
    MergeFilesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
