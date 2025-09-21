#!/usr/bin/env python3
"""
视频静音片段过滤工具 - GUI版本

提供图形界面的视频静音片段过滤工具，让操作更加直观。

依赖：
pip install tkinter numpy

作者：Taoge Media Edit Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import threading
from pathlib import Path

# 导入主脚本
try:
    from video_silence_filter import VideoSilenceFilter
except ImportError:
    print("错误: 无法导入 video_silence_filter 模块")
    sys.exit(1)


class VideoSilenceFilterGUI:
    """视频静音片段过滤工具GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("视频静音片段过滤工具")
        self.root.geometry("800x600")

        # 初始化过滤器
        self.filter_tool = VideoSilenceFilter()

        # 加载配置
        self.config = self.load_config()

        # 界面变量
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.preset_var = tk.StringVar(value=self.config.get('default_preset', 'medium'))
        self.custom_mode = tk.BooleanVar()
        self.threshold_var = tk.DoubleVar(value=-35.0)
        self.before_var = tk.DoubleVar(value=0.3)
        self.after_var = tk.DoubleVar(value=0.5)
        self.min_duration_var = tk.DoubleVar(value=0.8)
        self.ffmpeg_path_var = tk.StringVar(value=self.config.get('ffmpeg_path', 'ffmpeg'))

        self.setup_ui()

    def load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent / "config.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")

        return {
            "ffmpeg_path": "ffmpeg",
            "default_preset": "medium",
            "presets": {
                "slow": {"silence_threshold": -40, "before_padding": 0.5, "after_padding": 0.8, "min_silence_duration": 1.0},
                "medium": {"silence_threshold": -35, "before_padding": 0.3, "after_padding": 0.5, "min_silence_duration": 0.8},
                "fast": {"silence_threshold": -30, "before_padding": 0.1, "after_padding": 0.2, "min_silence_duration": 0.5}
            }
        }

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # 输入文件
        ttk.Label(file_frame, text="输入视频:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        input_frame = ttk.Frame(file_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        ttk.Entry(input_frame, textvariable=self.input_file, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_frame, text="浏览", command=self.browse_input_file).grid(row=0, column=1)

        # 输出文件
        ttk.Label(file_frame, text="输出视频:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        output_frame = ttk.Frame(file_frame)
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        output_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_frame, textvariable=self.output_file, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_file).grid(row=0, column=1)

        file_frame.columnconfigure(0, weight=1)

        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置参数", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # 预设选择
        preset_frame = ttk.Frame(config_frame)
        preset_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(preset_frame, text="节奏档位:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        preset_slow = ttk.Radiobutton(preset_frame, text="慢速", variable=self.preset_var, value="slow", command=self.on_preset_change)
        preset_slow.grid(row=0, column=1, padx=(0, 10))

        preset_medium = ttk.Radiobutton(preset_frame, text="中等", variable=self.preset_var, value="medium", command=self.on_preset_change)
        preset_medium.grid(row=0, column=2, padx=(0, 10))

        preset_fast = ttk.Radiobutton(preset_frame, text="快速", variable=self.preset_var, value="fast", command=self.on_preset_change)
        preset_fast.grid(row=0, column=3, padx=(0, 10))

        ttk.Checkbutton(preset_frame, text="自定义参数", variable=self.custom_mode, command=self.on_custom_mode_change).grid(row=0, column=4, padx=(20, 0))

        # 自定义参数
        self.custom_frame = ttk.LabelFrame(config_frame, text="自定义参数", padding="10")
        self.custom_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # 参数控件
        ttk.Label(self.custom_frame, text="静音阈值 (dB):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        threshold_frame = ttk.Frame(self.custom_frame)
        threshold_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Scale(threshold_frame, from_=-60, to=-10, variable=self.threshold_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=0)
        ttk.Label(threshold_frame, textvariable=self.threshold_var).grid(row=0, column=1, padx=(10, 0))

        ttk.Label(self.custom_frame, text="前置保留 (秒):").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        before_frame = ttk.Frame(self.custom_frame)
        before_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Scale(before_frame, from_=0, to=2, variable=self.before_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=0)
        ttk.Label(before_frame, textvariable=self.before_var).grid(row=0, column=1, padx=(10, 0))

        ttk.Label(self.custom_frame, text="后置保留 (秒):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        after_frame = ttk.Frame(self.custom_frame)
        after_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Scale(after_frame, from_=0, to=2, variable=self.after_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=0)
        ttk.Label(after_frame, textvariable=self.after_var).grid(row=0, column=1, padx=(10, 0))

        ttk.Label(self.custom_frame, text="最小静音时长 (秒):").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        min_duration_frame = ttk.Frame(self.custom_frame)
        min_duration_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Scale(min_duration_frame, from_=0.1, to=3, variable=self.min_duration_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=0)
        ttk.Label(min_duration_frame, textvariable=self.min_duration_var).grid(row=0, column=1, padx=(10, 0))

        self.custom_frame.columnconfigure(1, weight=1)

        # FFmpeg路径设置
        ffmpeg_frame = ttk.LabelFrame(main_frame, text="FFmpeg设置", padding="10")
        ffmpeg_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(ffmpeg_frame, text="FFmpeg路径:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ffmpeg_path_frame = ttk.Frame(ffmpeg_frame)
        ffmpeg_path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        ffmpeg_path_frame.columnconfigure(0, weight=1)

        ttk.Entry(ffmpeg_path_frame, textvariable=self.ffmpeg_path_var, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(ffmpeg_path_frame, text="浏览", command=self.browse_ffmpeg_path).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(ffmpeg_path_frame, text="测试", command=self.test_ffmpeg).grid(row=0, column=2)

        ffmpeg_frame.columnconfigure(0, weight=1)

        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="音频采样", command=self.sample_audio).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="开始处理", command=self.process_video).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="重置", command=self.reset_form).grid(row=0, column=2)

        # 进度和日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        # 进度条
        self.progress = ttk.Progressbar(log_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 日志文本框
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_text_frame, height=10, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        # 配置窗口网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 初始化界面状态
        self.on_custom_mode_change()
        self.on_preset_change()

    def browse_input_file(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择输入视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            # 自动设置输出文件名
            if not self.output_file.get():
                input_path = Path(filename)
                output_path = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"
                self.output_file.set(str(output_path))

    def browse_output_file(self):
        """浏览输出文件"""
        filename = filedialog.asksaveasfilename(
            title="选择输出视频文件",
            filetypes=[
                ("MP4视频", "*.mp4"),
                ("AVI视频", "*.avi"),
                ("所有文件", "*.*")
            ],
            defaultextension=".mp4"
        )
        if filename:
            self.output_file.set(filename)

    def browse_ffmpeg_path(self):
        """浏览FFmpeg路径"""
        filename = filedialog.askopenfilename(
            title="选择FFmpeg可执行文件",
            filetypes=[
                ("可执行文件", "*.exe"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.ffmpeg_path_var.set(filename)

    def test_ffmpeg(self):
        """测试FFmpeg"""
        self.filter_tool.ffmpeg_path = self.ffmpeg_path_var.get()
        if self.filter_tool.check_ffmpeg():
            messagebox.showinfo("测试成功", "FFmpeg测试成功！")
            self.log("FFmpeg测试成功")
        else:
            messagebox.showerror("测试失败", "FFmpeg测试失败，请检查路径设置！")
            self.log("FFmpeg测试失败")

    def on_preset_change(self):
        """预设档位改变"""
        if not self.custom_mode.get():
            preset = self.preset_var.get()
            if preset in self.config.get('presets', {}):
                preset_config = self.config['presets'][preset]
                self.threshold_var.set(preset_config['silence_threshold'])
                self.before_var.set(preset_config['before_padding'])
                self.after_var.set(preset_config['after_padding'])
                self.min_duration_var.set(preset_config['min_silence_duration'])

    def on_custom_mode_change(self):
        """自定义模式改变"""
        if self.custom_mode.get():
            # 启用自定义参数
            for child in self.custom_frame.winfo_children():
                child.configure(state='normal')
                if hasattr(child, 'winfo_children'):
                    for grandchild in child.winfo_children():
                        grandchild.configure(state='normal')
        else:
            # 禁用自定义参数，使用预设
            for child in self.custom_frame.winfo_children():
                if isinstance(child, (ttk.Scale, ttk.Entry)):
                    child.configure(state='disabled')
                elif hasattr(child, 'winfo_children'):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, (ttk.Scale, ttk.Entry)):
                            grandchild.configure(state='disabled')
            self.on_preset_change()

    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def sample_audio(self):
        """音频采样"""
        if not self.input_file.get():
            messagebox.showerror("错误", "请先选择输入视频文件！")
            return

        # 简单的采样对话框
        dialog = SampleDialog(self.root)
        if dialog.result:
            start_time, duration = dialog.result
            self.log(f"开始采样音频: 从{start_time}秒开始，持续{duration}秒")

            def sample_thread():
                try:
                    self.filter_tool.ffmpeg_path = self.ffmpeg_path_var.get()
                    volume = self.filter_tool.sample_audio_volume(self.input_file.get(), start_time, duration)
                    suggested_threshold = volume - 10

                    self.root.after(0, lambda: self.log(f"采样片段音量: {volume:.2f} dB"))
                    self.root.after(0, lambda: self.log(f"建议静音阈值: {suggested_threshold:.2f} dB"))
                    self.root.after(0, lambda: self.threshold_var.set(suggested_threshold))

                except Exception as e:
                    self.root.after(0, lambda: self.log(f"采样失败: {str(e)}"))
                    self.root.after(0, lambda: messagebox.showerror("采样失败", str(e)))

            threading.Thread(target=sample_thread, daemon=True).start()

    def process_video(self):
        """处理视频"""
        if not self.input_file.get():
            messagebox.showerror("错误", "请选择输入视频文件！")
            return

        if not self.output_file.get():
            messagebox.showerror("错误", "请选择输出视频文件！")
            return

        # 构建配置
        config = {
            "silence_threshold": self.threshold_var.get(),
            "before_padding": self.before_var.get(),
            "after_padding": self.after_var.get(),
            "min_silence_duration": self.min_duration_var.get()
        }

        self.log("开始处理视频...")
        self.log(f"配置参数: {config}")
        self.progress.start()

        def process_thread():
            try:
                self.filter_tool.ffmpeg_path = self.ffmpeg_path_var.get()
                success = self.filter_tool.process_video(
                    self.input_file.get(),
                    self.output_file.get(),
                    config
                )

                self.root.after(0, lambda: self.progress.stop())

                if success:
                    self.root.after(0, lambda: self.log("视频处理完成！"))
                    self.root.after(0, lambda: messagebox.showinfo("成功", "视频处理完成！"))
                else:
                    self.root.after(0, lambda: self.log("视频处理失败"))
                    self.root.after(0, lambda: messagebox.showerror("失败", "视频处理失败"))

            except Exception as e:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.log(f"处理错误: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))

        threading.Thread(target=process_thread, daemon=True).start()

    def reset_form(self):
        """重置表单"""
        self.input_file.set("")
        self.output_file.set("")
        self.custom_mode.set(False)
        self.preset_var.set(self.config.get('default_preset', 'medium'))
        self.ffmpeg_path_var.set(self.config.get('ffmpeg_path', 'ffmpeg'))
        self.log_text.delete(1.0, tk.END)
        self.on_custom_mode_change()
        self.on_preset_change()


class SampleDialog:
    """音频采样对话框"""

    def __init__(self, parent):
        self.result = None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("音频采样设置")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        # 变量
        self.start_time = tk.DoubleVar(value=10.0)
        self.duration = tk.DoubleVar(value=5.0)

        # 界面
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="开始时间 (秒):").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(frame, textvariable=self.start_time, width=20).grid(row=0, column=1, pady=(0, 10))

        ttk.Label(frame, text="持续时间 (秒):").grid(row=1, column=0, sticky=tk.W, pady=(0, 20))
        ttk.Entry(frame, textvariable=self.duration, width=20).grid(row=1, column=1, pady=(0, 20))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2)

        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)

        # 等待对话框关闭
        self.dialog.wait_window()

    def ok_clicked(self):
        """确定按钮"""
        self.result = (self.start_time.get(), self.duration.get())
        self.dialog.destroy()

    def cancel_clicked(self):
        """取消按钮"""
        self.dialog.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = VideoSilenceFilterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()