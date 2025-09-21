#!/usr/bin/env python3
"""
视频静音片段过滤工具测试脚本

测试主要功能是否正常工作

作者：Taoge Media Edit Tool
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from video_silence_filter import VideoSilenceFilter


def test_ffmpeg():
    """测试FFmpeg是否可用"""
    print("测试 FFmpeg...")
    filter_tool = VideoSilenceFilter()

    if filter_tool.check_ffmpeg():
        print("✓ FFmpeg 可用")
        return True
    else:
        print("✗ FFmpeg 不可用，请安装 FFmpeg")
        return False


def create_test_video():
    """创建一个测试视频（需要FFmpeg）"""
    print("创建测试视频...")

    test_video_path = script_dir / "test_video.mp4"

    # 如果测试视频已存在，直接返回
    if test_video_path.exists():
        print(f"✓ 测试视频已存在: {test_video_path}")
        return str(test_video_path)

    # 创建一个包含静音片段的测试视频
    # 格式：2秒音频 + 2秒静音 + 2秒音频 + 3秒静音 + 2秒音频
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2",  # 2秒440Hz音调
        "-f", "lavfi",
        "-i", "anullsrc=duration=2",           # 2秒静音
        "-f", "lavfi",
        "-i", "sine=frequency=880:duration=2",  # 2秒880Hz音调
        "-f", "lavfi",
        "-i", "anullsrc=duration=3",           # 3秒静音
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2",  # 2秒440Hz音调
        "-filter_complex", "[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[audio]",
        "-map", "[audio]",
        "-t", "11",  # 总时长11秒
        "-y", str(test_video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ 测试视频创建成功: {test_video_path}")
            return str(test_video_path)
        else:
            print(f"✗ 创建测试视频失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"✗ 创建测试视频异常: {str(e)}")
        return None


def test_audio_analysis(video_path):
    """测试音频分析功能"""
    print("测试音频分析功能...")

    filter_tool = VideoSilenceFilter()

    try:
        # 测试获取视频信息
        video_info = filter_tool.get_video_info(video_path)
        print(f"✓ 获取视频信息成功: {video_info.get('duration', '未知')}")

        # 测试音频数据提取
        audio_data, sample_rate = filter_tool.extract_audio_data(video_path, 0, 5)
        print(f"✓ 音频数据提取成功: 采样率 {sample_rate}Hz, 数据长度 {len(audio_data)}")

        # 测试音量计算
        db_values = filter_tool.calculate_volume_db(audio_data)
        avg_db = float(db_values.mean())
        print(f"✓ 音量计算成功: 平均音量 {avg_db:.2f} dB")

        return True

    except Exception as e:
        print(f"✗ 音频分析测试失败: {str(e)}")
        return False


def test_silence_detection(video_path):
    """测试静音检测功能"""
    print("测试静音检测功能...")

    filter_tool = VideoSilenceFilter()

    try:
        # 使用较低的阈值来检测静音片段
        silence_segments = filter_tool.detect_silence_segments(
            video_path,
            silence_threshold=-50,  # 较低阈值
            min_silence_duration=0.5  # 最小0.5秒
        )

        print(f"✓ 静音检测成功: 检测到 {len(silence_segments)} 个静音片段")
        for i, (start, end) in enumerate(silence_segments):
            print(f"  片段 {i+1}: {start:.2f}s - {end:.2f}s (时长: {end-start:.2f}s)")

        return True

    except Exception as e:
        print(f"✗ 静音检测测试失败: {str(e)}")
        return False


def test_video_processing(video_path):
    """测试视频处理功能"""
    print("测试视频处理功能...")

    filter_tool = VideoSilenceFilter()
    output_path = script_dir / "test_output.mp4"

    # 删除可能存在的输出文件
    if output_path.exists():
        output_path.unlink()

    config = {
        "silence_threshold": -50,
        "before_padding": 0.1,
        "after_padding": 0.1,
        "min_silence_duration": 0.5
    }

    try:
        success = filter_tool.process_video(video_path, str(output_path), config)

        if success and output_path.exists():
            # 检查输出文件大小
            output_size = output_path.stat().st_size
            print(f"✓ 视频处理成功: 输出文件大小 {output_size} 字节")

            # 获取输出视频信息
            output_info = filter_tool.get_video_info(str(output_path))
            print(f"✓ 输出视频时长: {output_info.get('duration', '未知')}")

            return True
        else:
            print("✗ 视频处理失败")
            return False

    except Exception as e:
        print(f"✗ 视频处理测试失败: {str(e)}")
        return False
    finally:
        # 清理输出文件
        if output_path.exists():
            output_path.unlink()


def test_preset_configs():
    """测试预设配置"""
    print("测试预设配置...")

    filter_tool = VideoSilenceFilter()
    presets = ["slow", "medium", "fast"]

    for preset in presets:
        if preset in filter_tool.preset_configs:
            config = filter_tool.preset_configs[preset]
            print(f"✓ 预设 '{preset}': {config}")
        else:
            print(f"✗ 预设 '{preset}' 不存在")
            return False

    return True


def test_audio_sampling(video_path):
    """测试音频采样功能"""
    print("测试音频采样功能...")

    filter_tool = VideoSilenceFilter()

    try:
        volume = filter_tool.sample_audio_volume(video_path, 1.0, 2.0)
        print(f"✓ 音频采样成功: 音量 {volume:.2f} dB")
        return True

    except Exception as e:
        print(f"✗ 音频采样测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=== 视频静音片段过滤工具测试 ===\n")

    test_results = []

    # 测试FFmpeg
    test_results.append(("FFmpeg测试", test_ffmpeg()))

    if not test_results[-1][1]:
        print("\n由于FFmpeg不可用，跳过其他测试")
        return

    # 创建测试视频
    test_video = create_test_video()
    if not test_video:
        print("\n无法创建测试视频，跳过视频相关测试")
        return

    # 运行各项测试
    test_results.append(("预设配置测试", test_preset_configs()))
    test_results.append(("音频分析测试", test_audio_analysis(test_video)))
    test_results.append(("静音检测测试", test_silence_detection(test_video)))
    test_results.append(("音频采样测试", test_audio_sampling(test_video)))
    test_results.append(("视频处理测试", test_video_processing(test_video)))

    # 输出测试结果
    print("\n=== 测试结果汇总 ===")
    passed = 0
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{len(test_results)} 项测试通过")

    if passed == len(test_results):
        print("🎉 所有测试通过！工具已准备就绪。")
    else:
        print("⚠️  部分测试失败，请检查相关功能。")

    # 清理测试文件
    test_video_path = Path(test_video)
    if test_video_path.exists():
        test_video_path.unlink()
        print(f"已清理测试文件: {test_video_path}")


if __name__ == "__main__":
    main()