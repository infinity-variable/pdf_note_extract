from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Tuple

class PDFExtractorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF高亮提取工具")
        self.style = ttk.Style()
        self.style.theme_use('vista')
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 文件选择组件
        self.btn_select = ttk.Button(self.main_frame, text="选择PDF文件", command=self.select_files)
        self.btn_select.grid(row=0, column=0, pady=5)
        
        self.listbox = tk.Listbox(self.main_frame, width=60, height=10)
        self.listbox.grid(row=1, column=0, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=2, column=0, pady=10)
        
        # 开始按钮
        self.btn_start = ttk.Button(self.main_frame, text="开始提取", command=self.start_extraction)
        self.btn_start.grid(row=3, column=0, pady=5)
        
        self.selected_files: List[str] = []

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if files:
            if len(files) > 50:
                messagebox.showwarning("警告", "单次最多选择50个文件")
                return
            
            self.selected_files = list(files)
            self.listbox.delete(0, tk.END)
            for f in self.selected_files:
                self.listbox.insert(tk.END, f)

    def start_extraction(self):
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return
        
        # 进度条配置
        self.progress['maximum'] = len(self.selected_files)
        self.progress['value'] = 0

        try:
            from pdf_processor import PDFProcessor, create_markdown
            processor = PDFProcessor()
            all_data = {}

            # 逐个处理文件
            for i, file_path in enumerate(self.selected_files):
                try:
                    annotations = processor.extract_annotations(file_path)
                    all_data[file_path] = annotations
                except Exception as e:
                    messagebox.showerror("错误", f"处理文件失败：{file_path}\n错误信息：{str(e)}")
                finally:
                    self.progress['value'] = i + 1
                    self.root.update()

            # 保存结果
            if all_data:
                save_path = filedialog.asksaveasfilename(
                    #defaultextension=".md",
                    filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")],
                    initialfile=f"pdf笔记汇总_{datetime.now().strftime('%Y%m%d_%H%M')}"
                )
                if save_path:
                    create_markdown(save_path, all_data)
                    messagebox.showinfo("完成", f"文件已保存至：{save_path}")

        except Exception as e:
            messagebox.showerror("系统错误", f"发生未预期错误：{str(e)}")
        finally:
            self.progress['value'] = 0

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PDFExtractorGUI()
    app.run()
    
# 添加异常捕获和日志模块
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)