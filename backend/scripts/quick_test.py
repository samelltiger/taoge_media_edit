#!/usr/bin/env python3
"""
视频静音片段过滤工具 - 快速测试脚本

测试修复后的功能是否正常

作者：Taoge Media Edit Tool
"""

import sys
import os
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from video_silence_filter import VideoSilenceFilter


def test_import():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        filter_tool = VideoSilenceFilter()
        print("✓ 模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False


def test_dependencies():
    """测试依赖项"""
    print("测试依赖项...")

    try:
        import numpy as np
        print("✓ numpy 可用")
    except ImportError:
        print("✗ numpy 不可用")
        return False

    try:
        import wave
        print("✓ wave 可用")
    except ImportError:
        print("✗ wave 不可用")
        return False

    try:
        from scipy import ndimage
        print("✓ scipy 可用")
    except ImportError:
        print("⚠ scipy 不可用（可选依赖）")

    return True


def test_ffmpeg():
    """测试FFmpeg"""
    print("测试 FFmpeg...")
    filter_tool = VideoSilenceFilter()

    if filter_tool.check_ffmpeg():
        print("✓ FFmpeg 可用")
        return True
    else:
        print("✗ FFmpeg 不可用")
        return False


def test_audio_processing():
    """测试音频处理功能"""
    print("测试音频处理功能...")

    # 这里只测试函数是否可以调用，不需要实际文件
    try:
        filter_tool = VideoSilenceFilter()

        # 测试音量计算函数
        import numpy as np
        test_audio = np.array([0.1, 0.2, 0.05, 0.3], dtype=np.float32)
        db_values = filter_tool.calculate_volume_db(test_audio)
        print(f"✓ 音量计算功能正常，测试结果: {db_values}")

        return True
    except Exception as e:
        print(f"✗ 音频处理功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=== 视频静音片段过滤工具 - 快速测试 ===\n")

    tests = [
        ("模块导入", test_import),
        ("依赖项检查", test_dependencies),
        ("FFmpeg测试", test_ffmpeg),
        ("音频处理", test_audio_processing)
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}\n")

    print("=== 测试结果汇总 ===")
    print(f"通过: {passed}/{len(tests)} 项测试")

    if passed == len(tests):
        print("🎉 所有测试通过！脚本已准备就绪。")
        print("\n使用方法:")
        print("python video_silence_filter.py input.mp4 output.mp4 --preset medium")
        print("python video_silence_filter_gui.py  # GUI版本")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)