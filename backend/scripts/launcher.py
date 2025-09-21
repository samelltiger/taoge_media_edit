#!/usr/bin/env python3
"""
视频静音片段过滤工具 - 启动器

提供统一的入口来使用各种工具

作者：Taoge Media Edit Tool
"""

import sys
import os
import argparse
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def show_banner():
    """显示工具横幅"""
    print("=" * 60)
    print("          视频静音片段过滤工具")
    print("          Taoge Media Edit Tool")
    print("=" * 60)
    print()


def show_tools_info():
    """显示可用工具信息"""
    tools = [
        {
            "name": "单文件处理",
            "script": "video_silence_filter.py",
            "description": "处理单个视频文件，移除静音片段"
        },
        {
            "name": "GUI界面",
            "script": "video_silence_filter_gui.py",
            "description": "图形界面版本，操作更直观"
        },
        {
            "name": "批量处理",
            "script": "batch_processor.py",
            "description": "批量处理多个视频文件"
        },
        {
            "name": "功能测试",
            "script": "test_filter.py",
            "description": "测试工具功能是否正常"
        }
    ]

    print("可用工具:")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']} ({tool['script']})")
        print(f"   {tool['description']}")
        print()


def check_dependencies():
    """检查依赖项"""
    print("检查依赖项...")

    # 检查Python模块
    required_modules = ['numpy']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"✗ {module} (缺失)")

    if missing_modules:
        print(f"\n请安装缺失的模块:")
        print(f"pip install {' '.join(missing_modules)}")
        return False

    # 检查FFmpeg
    from video_silence_filter import VideoSilenceFilter
    filter_tool = VideoSilenceFilter()
    if filter_tool.check_ffmpeg():
        print("✓ FFmpeg")
    else:
        print("✗ FFmpeg (缺失)")
        print("\n请安装 FFmpeg:")
        print("- Windows: 下载 FFmpeg 并配置环境变量")
        print("- macOS: brew install ffmpeg")
        print("- Linux: sudo apt install ffmpeg 或 sudo yum install ffmpeg")
        return False

    print("\n✓ 所有依赖项已满足")
    return True


def run_tool(tool_name, args):
    """运行指定工具"""
    tools_map = {
        "filter": "video_silence_filter.py",
        "gui": "video_silence_filter_gui.py",
        "batch": "batch_processor.py",
        "test": "test_filter.py"
    }

    if tool_name not in tools_map:
        print(f"错误: 未知工具 '{tool_name}'")
        print(f"可用工具: {', '.join(tools_map.keys())}")
        return False

    script_path = script_dir / tools_map[tool_name]

    if not script_path.exists():
        print(f"错误: 脚本文件不存在: {script_path}")
        return False

    # 构建命令
    cmd = [sys.executable, str(script_path)] + args

    try:
        os.execv(sys.executable, cmd)
    except Exception as e:
        print(f"启动工具失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频静音片段过滤工具启动器",
        add_help=False  # 禁用默认help，我们自定义
    )

    parser.add_argument("tool", nargs="?", choices=["filter", "gui", "batch", "test", "info", "check"],
                       help="要启动的工具")
    parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")

    # 解析已知参数，剩余参数传递给子工具
    args, remaining_args = parser.parse_known_args()

    show_banner()

    # 显示帮助
    if args.help or (not args.tool and not remaining_args):
        show_tools_info()
        print("使用方法:")
        print("  python launcher.py <tool> [参数...]")
        print()
        print("工具选项:")
        print("  filter  - 单文件处理工具")
        print("  gui     - GUI界面工具")
        print("  batch   - 批量处理工具")
        print("  test    - 功能测试工具")
        print("  info    - 显示工具信息")
        print("  check   - 检查依赖项")
        print()
        print("示例:")
        print("  python launcher.py gui")
        print("  python launcher.py filter input.mp4 output.mp4 --preset fast")
        print("  python launcher.py batch input_dir output_dir --recursive")
        print("  python launcher.py test")
        return

    # 检查依赖项
    if args.tool == "check":
        check_dependencies()
        return

    # 显示工具信息
    if args.tool == "info":
        show_tools_info()
        return

    # 检查依赖项（除了info和check命令）
    if not check_dependencies():
        print("\n请先解决依赖项问题")
        sys.exit(1)

    # 运行指定工具
    if args.tool:
        success = run_tool(args.tool, remaining_args)
        if not success:
            sys.exit(1)
    else:
        print("请指定要使用的工具，使用 --help 查看帮助")


if __name__ == "__main__":
    main()