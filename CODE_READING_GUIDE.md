# `File_merging_and_export_tool.py` 代码阅读指南

这份指南面向已经会一点 C 语言、刚开始学习 Python 的读者。目标不是逐行翻译代码，而是帮你快速看懂：这个程序真正完成“添加文件、合并文件、导出结果”的代码在哪里，以及这些 Python 写法和 C 语言概念有什么对应关系。

## 1. 先回答核心问题：真正实现操作的是哪些部分

这个项目有两个 Python 文件：

- `main.py`：很薄的入口文件，只负责导入并调用 `main()`。
- `File_merging_and_export_tool.py`：真正的程序主体，窗口、按钮、文件列表、导出逻辑都在这里。

如果只想看“真正干活”的代码，优先看这些函数：

| 代码位置 | 作用 | 是否属于核心操作 |
| --- | --- | --- |
| `main()` | 创建窗口，启动 GUI 主循环 | 是，程序入口 |
| `MergeFilesApp.__init__()` | 初始化程序对象、状态、界面和事件绑定 | 是，整体装配 |
| `_add_files()` | 打开文件选择框，让用户选择文件 | 是，添加文件入口 |
| `_add_directory()` | 打开目录选择框，递归加入目录内文件 | 是，添加目录入口 |
| `_add_paths()` | 真正把路径加入 `self.files`，并去重 | 是，文件列表核心 |
| `_collect_directory_files()` | 遍历目录，收集所有文件路径 | 是，目录导入核心 |
| `_remove_selected()` | 删除选中的文件 | 是，列表维护 |
| `_move_up()` / `_move_down()` | 调整文件合并顺序 | 是，列表维护 |
| `_refresh_tree()` | 用 `self.files` 刷新界面列表和状态栏 | 半核心，连接数据和界面 |
| `_export()` | 选择保存位置，写出合并文件 | 是，导出核心 |
| `_write_file_content()` | 读取单个文件，判断文本/二进制并写入输出文件 | 是，内容处理核心 |
| `_decode_text_bytes()` | 尝试用多种编码把字节解码成文本 | 是，文本识别核心 |
| `_looks_like_text()` | 判断解码结果是否像文本 | 是，辅助判断 |
| `_write_binary_preview()` | 对二进制文件写入十六进制预览 | 是，二进制处理 |

而这些函数主要是界面和交互外壳：

| 代码位置 | 作用 |
| --- | --- |
| `_apply_theme()` | 设置颜色、字体、Tkinter 主题 |
| `_build_ui()` | 创建按钮、表格、输入框等界面控件 |
| `_bind_hover()` | 鼠标悬停时改变按钮颜色 |
| `_register_drag_and_drop()` / `_bind_drop_widget()` | 注册拖拽功能 |
| `_on_drag_enter()` / `_on_drag_leave()` | 拖拽进入/离开时改变边框颜色 |
| `_set_drop_zone_active()` | 设置拖拽区域高亮 |
| `_bind_shortcuts()` | 绑定快捷键 |

一句话概括：

> `_build_ui()` 负责让用户“看见并点击”；`_add_paths()` 负责维护待合并文件列表；`_export()` 负责把列表里的文件真正读出来并写成一个合并文件。

## 2. 推荐阅读顺序

不要从第一行一直读到最后一行。GUI 程序的界面代码通常很长，初学者容易迷失。建议按执行流程读：

1. 先看 `main.py`
2. 再看 `File_merging_and_export_tool.py` 末尾的 `main()`
3. 再看 `MergeFilesApp.__init__()`
4. 暂时跳过 `_apply_theme()` 和 `_build_ui()` 的细节，只知道它们负责界面
5. 重点看 `_add_files()`、`_add_directory()`、`_add_paths()`、`_collect_directory_files()`
6. 再看 `_export()`、`_write_file_content()`、`_decode_text_bytes()`
7. 最后回头看 Tkinter 控件、拖拽、快捷键等交互细节

这和阅读 C 程序很像：先找 `main()`，再找主要函数调用链，而不是先研究每个 `printf` 或界面细节。

## 3. 程序启动流程

`main.py` 的内容很短：

```python
from File_merging_and_export_tool import main


if __name__ == "__main__":
    main()
```

这里的意思是：如果直接运行 `main.py`，就调用从 `File_merging_and_export_tool.py` 导入的 `main()`。

真正的入口在 `File_merging_and_export_tool.py`：

```python
def main():
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    MergeFilesApp(root)
    root.mainloop()
```

可以把它类比成 C 语言里的：

```c
int main(void) {
    Window *root = create_window();
    App *app = create_app(root);
    event_loop(root);
}
```

关键点：

- `root` 是主窗口。
- `MergeFilesApp(root)` 创建应用对象，并把窗口交给它管理。
- `root.mainloop()` 是 GUI 程序的事件循环。它会一直等待用户点击按钮、选择文件、拖拽文件等操作。

C 程序通常是顺序执行完就退出；GUI 程序不同，它启动后大部分时间都在 `mainloop()` 里等待事件。

## 4. `MergeFilesApp`：整个程序的主对象

核心类是：

```python
class MergeFilesApp:
    def __init__(self, root: tk.Tk):
```

如果用 C 语言类比，可以把 `MergeFilesApp` 理解成“一个结构体 + 一组操作这个结构体的函数”。

例如 Python 里的：

```python
self.root = root
self.files: list[Path] = []
```

大致可以类比成 C 语言里的：

```c
typedef struct {
    Window *root;
    PathArray files;
} MergeFilesApp;
```

这里的 `self` 很重要。它类似 C 语言里传入函数的“当前对象指针”：

```python
def _add_paths(self, paths):
    self.files.append(normalized)
```

可以类比成：

```c
void add_paths(MergeFilesApp *self, PathArray paths) {
    append(&self->files, normalized);
}
```

所以看到 `self.files`，就理解为“这个应用对象内部保存的待合并文件列表”。

## 5. 初始化时做了什么

`__init__()` 里做了几件事：

```python
self.files: list[Path] = []
self.drag_enabled = TkinterDnD is not None and isinstance(root, TkinterDnD.Tk)

self._init_state()
self._apply_theme()
self._build_ui()
self._register_drag_and_drop()
self._bind_shortcuts()
self._update_action_state()
```

按作用分组：

- `self.files`：真正保存待合并文件路径的列表。
- `_init_state()`：初始化界面变量，例如导出编码、换行风格、分隔符。
- `_apply_theme()`：设置颜色和字体。
- `_build_ui()`：创建按钮、文件列表、导出设置区域。
- `_register_drag_and_drop()`：如果安装了 `tkinterdnd2`，就启用拖拽导入。
- `_bind_shortcuts()`：绑定 `Ctrl+O`、`Ctrl+S`、`Delete`。
- `_update_action_state()`：根据当前有没有文件、有没有选中项，决定按钮能不能点。

真正的数据核心是 `self.files`。界面上的表格只是它的显示结果。

## 6. 添加文件：从按钮到 `self.files`

用户点击“添加文件”按钮时，按钮绑定的是：

```python
command=self._add_files
```

所以点击按钮会调用：

```python
def _add_files(self):
    paths = filedialog.askopenfilenames(title="选择要合并的文件")
    if paths:
        self._add_paths(paths)
```

这个函数本身不负责保存文件列表，它只负责弹出文件选择框。真正把文件加入列表的是 `_add_paths()`。

`_add_paths()` 的核心逻辑是：

```python
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
```

逐步理解：

1. 先把已有文件转成 `existing` 集合，用来去重。
2. 遍历用户传入的路径。
3. 如果不是文件，就跳过。
4. 把路径标准化，避免同一个文件因为写法不同被重复加入。
5. 如果已经存在，就跳过。
6. 否则加入 `self.files`。
7. 如果确实新增了文件，就调用 `_refresh_tree()` 刷新界面。

Python 知识点：

- `list` 类似 C 里的动态数组。
- `set` 类似“只关心是否存在”的集合，查重很快。
- `continue` 和 C 语言里的 `continue` 作用一样：跳过本轮循环。
- `Path` 是 Python 标准库里表示文件路径的对象，比直接用字符串更方便。

## 7. 添加目录：递归收集文件

用户点击“添加目录”按钮时调用：

```python
def _add_directory(self):
    directory = filedialog.askdirectory(title="选择目录（将递归添加所有文件）")
    if directory:
        self._add_paths(self._collect_directory_files(Path(directory)))
```

这里有两步：

1. `_collect_directory_files()` 收集目录下所有文件。
2. `_add_paths()` 把这些文件加入 `self.files`。

目录遍历函数是：

```python
def _collect_directory_files(self, directory: Path) -> list[Path]:
    collected: list[Path] = []
    for root_dir, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for fn in sorted(filenames):
            collected.append(Path(root_dir) / fn)
    return collected
```

`os.walk(directory)` 会递归遍历目录。每次循环会给出：

- `root_dir`：当前正在遍历的目录。
- `dirnames`：当前目录下的子目录名。
- `filenames`：当前目录下的文件名。

`Path(root_dir) / fn` 是 Python `pathlib` 的路径拼接写法。它类似 C 里手动拼接：

```c
sprintf(full_path, "%s/%s", root_dir, filename);
```

但 `Path` 更安全，也更适合跨平台。

## 8. 文件顺序和界面刷新

合并文件时的顺序就是 `self.files` 列表里的顺序。因此移动文件时，代码实际是在交换列表元素。

上移：

```python
self.files[idx], self.files[idx - 1] = self.files[idx - 1], self.files[idx]
```

下移：

```python
self.files[idx], self.files[idx + 1] = self.files[idx + 1], self.files[idx]
```

这是 Python 的“多重赋值”，可以直接交换两个变量。C 语言通常要写临时变量：

```c
tmp = files[idx];
files[idx] = files[idx - 1];
files[idx - 1] = tmp;
```

每次列表变化后，都会调用：

```python
self._refresh_tree()
```

`_refresh_tree()` 的任务是：清空界面表格，然后按 `self.files` 重新插入每一行。

所以要记住一个关系：

> `self.files` 是真实数据；Treeview 表格只是它的可视化显示。

## 9. 导出核心：`_export()`

`_export()` 是整个程序最重要的函数。它真正完成“把多个文件合并导出”的动作。

主要流程：

1. 如果没有文件，弹窗提醒。
2. 弹出保存文件对话框，让用户选择输出路径。
3. 检查输出文件不能和输入文件是同一个路径。
4. 读取导出设置，例如编码、换行符、分隔符。
5. 打开输出文件。
6. 写入导出头部信息。
7. 遍历 `self.files`。
8. 对每个文件调用 `_write_file_content()` 写入内容。
9. 写入结束信息。
10. 成功后弹窗提示。

核心结构大致是：

```python
with open(save_path, "w", encoding=export_settings.encoding,
          newline=export_settings.newline) as out:
    out.write(...)

    for i, fp in enumerate(self.files, 1):
        out.write(...)
        file_type = self._write_file_content(out, fp)
        out.write(...)
```

`with open(...) as out:` 是 Python 推荐的文件打开方式。它的好处是：代码块结束后自动关闭文件，即使中间发生异常也会尽量正确释放资源。

C 语言中你通常要写：

```c
FILE *out = fopen(path, "w");
if (out == NULL) {
    // handle error
}
fprintf(out, ...);
fclose(out);
```

Python 的 `with` 把 `fclose` 这类清理动作自动化了。

## 10. 单个文件如何写入：文本或二进制

`_write_file_content()` 负责处理一个输入文件：

```python
def _write_file_content(self, out, file_path: Path) -> str:
    raw = file_path.read_bytes()
    text, encoding = self._decode_text_bytes(raw)

    if text is not None:
        out.write(f"[文本文件 - 编码: {encoding}]\n")
        if text:
            out.write(text)
            if not text.endswith("\n"):
                out.write("\n")
        else:
            out.write("[空文件]\n")
        return "text"

    out.write(f"[二进制文件 - 大小: {len(raw)} 字节]\n")
    self._write_binary_preview(out, raw)
    return "binary"
```

关键点：

- `read_bytes()` 先按原始字节读取文件。
- `_decode_text_bytes(raw)` 尝试把字节转成字符串。
- 如果能转成合理文本，就写文本内容。
- 如果不能，就认为它是二进制文件，写入十六进制预览。

这里体现了一个重要概念：

> 计算机文件本质上都是字节；文本文件只是“这些字节可以按某种编码解释成字符”的文件。

Python 里：

- `bytes`：原始字节，类似 C 里的 `unsigned char *` 缓冲区。
- `str`：已经解码后的文本字符串，是 Unicode 字符序列。
- `decode()`：把 `bytes` 转成 `str`。
- `encode()`：把 `str` 转成 `bytes`。

## 11. 文本编码识别：`_decode_text_bytes()`

程序支持多种文本编码：

```python
TEXT_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "utf-8", "gb18030", "gbk")
```

`_decode_text_bytes()` 会依次尝试这些编码：

```python
for encoding in candidates:
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        continue

    if self._looks_like_text(text):
        return text, encoding

return None, None
```

可以把它理解成：

1. 用 UTF-8 试试看。
2. 不行就用 GB18030 试试看。
3. 不行再用 GBK 试试看。
4. 如果都失败，返回 `None`，表示“不像文本”。

`try/except` 是 Python 的异常处理。它和 C 语言里的错误码判断不一样。C 常见写法是：

```c
result = decode(raw, encoding);
if (result == ERROR) {
    continue;
}
```

Python 常见写法是：

```python
try:
    text = raw.decode(encoding)
except UnicodeDecodeError:
    continue
```

也就是说：先尝试执行，如果失败，就进入 `except`。

## 12. 判断“像不像文本”

有些二进制文件也可能碰巧被某种编码解码成功，所以程序还会调用：

```python
def _looks_like_text(self, text: str) -> bool:
    if not text:
        return True

    suspicious_chars = sum(
        1 for char in text if ord(char) < 32 and char not in "\n\r\t"
    )
    return suspicious_chars / len(text) < 0.02
```

这里的想法是：真正的文本中，控制字符通常很少。换行 `\n`、回车 `\r`、制表符 `\t` 是正常的；其他 ASCII 码小于 32 的字符比较可疑。

如果可疑字符比例小于 2%，就认为它像文本。

Python 知识点：

- `ord(char)` 返回字符的 Unicode 编号，类似你在 C 里把 `char` 当整数看。
- `sum(1 for char in text if ...)` 是生成器表达式，用来统计满足条件的字符数量。
- `return suspicious_chars / len(text) < 0.02` 返回的是布尔值 `True` 或 `False`。

## 13. 二进制预览：`_write_binary_preview()`

如果文件不像文本，程序不会把完整二进制内容直接写进输出文件，而是写前 512 字节的十六进制预览：

```python
preview = raw[:BINARY_PREVIEW_BYTES]
for offset in range(0, len(preview), 16):
    chunk = preview[offset:offset + 16]
    hex_part = " ".join(f"{byte:02x}" for byte in chunk)
    ascii_part = "".join(
        chr(byte) if 32 <= byte < 127 else "." for byte in chunk
    )
```

这个输出形式和很多十六进制查看器类似：

- 左边是偏移量。
- 中间是每个字节的十六进制。
- 右边是可显示 ASCII 字符，不可显示的用 `.` 替代。

`raw[:512]` 是 Python 的切片语法，意思是取前 512 个字节。C 语言里通常要手动控制长度和指针。

## 14. 导出设置：`ExportSettings`

代码里定义了：

```python
class ExportSettings(NamedTuple):
    encoding: str
    newline: str
    newline_label: str
    separator_length: int
    header_separator: str
    section_separator: str
    block_separator: str
```

`NamedTuple` 可以理解成“带名字字段的只读结构体”。它类似 C 里的：

```c
typedef struct {
    char *encoding;
    char *newline;
    char *newline_label;
    int separator_length;
    char *header_separator;
    char *section_separator;
    char *block_separator;
} ExportSettings;
```

`_current_export_settings()` 会从界面控件里读取当前设置，打包成一个 `ExportSettings` 返回。这样 `_export()` 不需要到处读取界面变量，只要拿到一个配置对象即可。

这是一个值得学习的编程习惯：

> 把一组相关配置打包成一个结构，传递和使用都会更清楚。

## 15. 界面代码应该怎么看

`_build_ui()` 很长，但它主要是在创建 Tkinter 控件。初学者不需要一开始就完全看懂每一行。

常见模式是：

```python
self.btn_add = tk.Button(..., command=self._add_files, ...)
self.btn_add.pack(...)
```

阅读重点不是按钮颜色、边距、字体，而是：

```python
command=self._add_files
```

这表示“用户点击这个按钮时，调用 `_add_files()`”。

类似地，导出按钮里有：

```python
command=self._export
```

这才是从界面跳到业务逻辑的关键连接点。

读 GUI 代码时可以采用这个方法：

1. 找控件名称，例如 `btn_add`、`btn_export`。
2. 找 `command=...`。
3. 跳到对应函数。
4. 暂时忽略颜色、字体、布局参数。

## 16. 拖拽导入和按钮导入的关系

拖拽导入的核心函数是 `_on_drop()`：

```python
dropped_items = self.root.tk.splitlist(event.data)
collected: list[Path] = []
for item in dropped_items:
    path = Path(item)
    if path.is_dir():
        collected.extend(self._collect_directory_files(path))
    else:
        collected.append(path)

added = self._add_paths(collected)
```

可以看到，拖拽导入最终也调用 `_add_paths()`。

所以这个程序设计得比较清楚：

- 按钮添加文件：最终调用 `_add_paths()`。
- 按钮添加目录：最终调用 `_add_paths()`。
- 拖拽文件或目录：最终调用 `_add_paths()`。

这说明 `_add_paths()` 是统一入口。多个用户操作走到同一个核心函数，可以减少重复代码。

## 17. 异常处理在哪里

程序里多处使用了 `try/except`。

例如计算文件大小：

```python
try:
    size = self._format_size(fp.stat().st_size)
except OSError:
    size = "N/A"
```

意思是：如果文件已经被删除、权限不足，读取大小可能失败。失败时不要让程序崩溃，而是显示 `N/A`。

导出时也有：

```python
try:
    file_type = self._write_file_content(out, fp)
except Exception as e:
    out.write(f"[读取错误: {e}]\n")
```

这样即使某个文件读取失败，程序也可以把错误写入输出文件，然后继续处理后面的文件。

这是实用程序常见的设计：单个文件失败，不一定要让整个批处理失败。

## 18. 数据流总结

可以把整个程序的数据流画成这样：

```text
用户选择文件/目录/拖拽
        |
        v
_add_files() / _add_directory() / _on_drop()
        |
        v
_add_paths()
        |
        v
self.files  保存待合并文件路径
        |
        v
_refresh_tree()  把 self.files 显示到界面
        |
        v
用户点击导出
        |
        v
_export()
        |
        v
for fp in self.files
        |
        v
_write_file_content()
        |
        +--> 文本：写入原文本内容
        |
        +--> 二进制：写入十六进制预览
        |
        v
合并输出文件
```

如果你只记住一个核心结构，就是：

```text
self.files 是输入文件列表
_export() 遍历 self.files
_write_file_content() 负责写每一个文件
```

## 19. 初学者可以从这个文件学到什么

这个程序适合练习以下 Python 知识：

- 如何用 `main()` 和 `if __name__ == "__main__"` 组织入口。
- 如何用 `class` 把状态和函数放在一起。
- 如何用 `self` 保存程序状态。
- 如何用 `list` 管理一组数据。
- 如何用 `Path` 处理文件路径。
- 如何用 `os.walk()` 递归遍历目录。
- 如何用 `with open()` 安全读写文件。
- 如何区分 `bytes` 和 `str`。
- 如何处理文本编码。
- 如何用 `try/except` 让程序面对错误时不崩溃。
- 如何让多个界面入口复用同一个业务函数。

## 20. 最短理解版

如果你时间很少，只看下面这几句话：

1. `main.py` 只是入口，真正代码在 `File_merging_and_export_tool.py`。
2. `MergeFilesApp` 是主类，`self.files` 是待合并文件列表。
3. 添加文件、添加目录、拖拽导入，最终都会调用 `_add_paths()`。
4. 文件顺序就是 `self.files` 的顺序。
5. 点击导出会调用 `_export()`。
6. `_export()` 遍历 `self.files`，对每个文件调用 `_write_file_content()`。
7. `_write_file_content()` 先按字节读取文件，再判断是文本还是二进制。
8. 文本文件写入原内容；二进制文件写入前 512 字节的十六进制预览。
9. `_apply_theme()` 和 `_build_ui()` 主要是界面代码，不是文件合并的核心算法。

读懂以上 9 点，就已经掌握了这个程序的主干。
