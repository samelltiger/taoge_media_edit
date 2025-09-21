#!/usr/bin/env python3
"""
视频静音片段过滤工具

功能：
1. 自动检测和过滤视频中的静音片段
2. 支持三种预设节奏档位（慢、中等、快）
3. 支持自定义参数设置
4. 支持音轨编辑和采样功能
5. 使用ffmpeg进行视频处理

作者：Taoge Media Edit Tool
"""

import os
import sys
import json
import subprocess
import numpy as np
from typing import List, Tuple, Dict, Optional
import argparse
import tempfile
from pathlib import Path

# 可选依赖
try:
    from scipy import ndimage
    HAS_SCIPY = True
except (ImportError, Exception):
    # 处理所有可能的导入错误，包括numpy兼容性问题
    HAS_SCIPY = False


class VideoSilenceFilter:
    """视频静音片段过滤器"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        初始化过滤器

        Args:
            ffmpeg_path: ffmpeg可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path

        # 预设节奏档位配置
        self.preset_configs = {
            "slow": {
                "silence_threshold": -40,  # dB
                "before_padding": 0.5,     # 秒
                "after_padding": 0.8,      # 秒
                "min_silence_duration": 1.0  # 最小静音持续时间
            },
            "medium": {
                "silence_threshold": -35,
                "before_padding": 0.3,
                "after_padding": 0.5,
                "min_silence_duration": 0.8
            },
            "fast": {
                "silence_threshold": -30,
                "before_padding": 0.1,
                "after_padding": 0.2,
                "min_silence_duration": 0.5
            }
        }

    def check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_video_info(self, video_path: str) -> Dict:
        """获取视频信息"""
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # 从stderr中解析视频信息
            stderr_output = result.stderr
            info = {}

            for line in stderr_output.split('\n'):
                if "Duration:" in line:
                    duration_str = line.split("Duration:")[1].split(",")[0].strip()
                    info['duration'] = duration_str
                elif "Video:" in line:
                    info['video_codec'] = line
                elif "Audio:" in line:
                    info['audio_codec'] = line
                    # 提取采样率
                    if "Hz" in line:
                        sample_rate = line.split("Hz")[0].split()[-1]
                        info['sample_rate'] = int(sample_rate)

            return info

        except subprocess.TimeoutExpired:
            raise Exception("获取视频信息超时")
        except Exception as e:
            raise Exception(f"获取视频信息失败: {str(e)}")

    def extract_audio_data(self, video_path: str, start_time: float = 0, duration: float = None) -> Tuple[np.ndarray, int]:
        """
        提取音频数据用于分析

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒），None表示到结尾

        Returns:
            音频数据数组和采样率
        """
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

        try:
            cmd = [self.ffmpeg_path, "-i", video_path]

            if start_time > 0:
                cmd.extend(["-ss", str(start_time)])

            if duration is not None:
                cmd.extend(["-t", str(duration)])

            cmd.extend([
                "-vn",  # 不要视频
                "-acodec", "pcm_s16le",  # PCM 16位
                "-ar", "22050",  # 采样率
                "-ac", "1",  # 单声道
                "-y",  # 覆盖输出文件
                temp_audio_path
            ])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"音频提取失败: {result.stderr}")

            # 需要wave模块来读取WAV文件
            import wave
            with wave.open(temp_audio_path, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                audio_data = np.frombuffer(frames, dtype=np.int16)

            return audio_data.astype(np.float32) / 32768.0, sample_rate

        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    def calculate_volume_db(self, audio_data: np.ndarray) -> np.ndarray:
        """计算音频音量（dB）"""
        # 避免log(0)的情况
        audio_data_abs = np.abs(audio_data)
        audio_data_abs = np.maximum(audio_data_abs, 1e-10)

        # 计算dB
        db_values = 20 * np.log10(audio_data_abs)
        return db_values

    def detect_silence_segments(self,
                              video_path: str,
                              silence_threshold: float = -35,
                              min_silence_duration: float = 0.8) -> List[Tuple[float, float]]:
        """
        检测静音片段

        Args:
            video_path: 视频文件路径
            silence_threshold: 静音阈值（dB）
            min_silence_duration: 最小静音持续时间（秒）

        Returns:
            静音片段列表 [(开始时间, 结束时间), ...]
        """
        print(f"正在分析音频，检测静音片段...")
        print(f"静音阈值: {silence_threshold} dB, 最小时长: {min_silence_duration} 秒")

        # 提取音频数据
        audio_data, sample_rate = self.extract_audio_data(video_path)
        print(f"音频采样率: {sample_rate} Hz, 数据长度: {len(audio_data)} 个采样点")

        # 使用滑动窗口计算RMS音量
        window_size = int(sample_rate * 0.1)  # 100ms窗口
        hop_size = int(sample_rate * 0.05)    # 50ms步长

        rms_values = []
        time_stamps = []

        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i + window_size]
            rms = np.sqrt(np.mean(window ** 2))
            # 转换为dB，避免log(0)
            db_value = 20 * np.log10(max(rms, 1e-10))
            rms_values.append(db_value)
            time_stamps.append(i / sample_rate)

        rms_values = np.array(rms_values)
        time_stamps = np.array(time_stamps)

        print(f"音量统计: 最大 {rms_values.max():.2f} dB, 最小 {rms_values.min():.2f} dB, 平均 {rms_values.mean():.2f} dB")

        # 检测静音
        is_silence = rms_values < silence_threshold

        # 使用形态学操作清理噪声
        if HAS_SCIPY:
            # 移除孤立的噪声点
            is_silence = ndimage.binary_opening(is_silence, iterations=2)
            # 填充小空隙
            is_silence = ndimage.binary_closing(is_silence, iterations=3)
        else:
            print("警告: scipy不可用，使用简单过滤")
            # 简单的平滑过滤
            kernel_size = 5
            is_silence_smooth = np.zeros_like(is_silence)
            for i in range(kernel_size//2, len(is_silence) - kernel_size//2):
                window = is_silence[i-kernel_size//2:i+kernel_size//2+1]
                is_silence_smooth[i] = np.sum(window) > kernel_size // 2
            is_silence = is_silence_smooth

        # 查找静音片段
        silence_segments = []
        in_silence = False
        silence_start = 0

        for i, silent in enumerate(is_silence):
            time_pos = time_stamps[i]

            if silent and not in_silence:
                # 开始静音
                in_silence = True
                silence_start = time_pos
            elif not silent and in_silence:
                # 结束静音
                in_silence = False
                silence_duration = time_pos - silence_start

                if silence_duration >= min_silence_duration:
                    silence_segments.append((silence_start, time_pos))

        # 处理最后一个静音片段
        if in_silence:
            final_time = len(audio_data) / sample_rate
            silence_duration = final_time - silence_start
            if silence_duration >= min_silence_duration:
                silence_segments.append((silence_start, final_time))

        print(f"检测到 {len(silence_segments)} 个静音片段")
        for i, (start, end) in enumerate(silence_segments):
            print(f"  片段 {i+1}: {start:.2f}s - {end:.2f}s (时长: {end-start:.2f}s)")

        return silence_segments

    def calculate_keep_segments(self,
                               video_path: str,
                               silence_segments: List[Tuple[float, float]],
                               before_padding: float = 0.3,
                               after_padding: float = 0.5) -> List[Tuple[float, float]]:
        """
        计算需要保留的片段

        Args:
            video_path: 视频文件路径
            silence_segments: 静音片段列表
            before_padding: 有用片段前保留时间（秒）
            after_padding: 有用片段后保留时间（秒）

        Returns:
            保留片段列表 [(开始时间, 结束时间), ...]
        """
        video_info = self.get_video_info(video_path)
        duration_str = video_info.get('duration', '00:00:00.00')

        # 解析视频总时长
        time_parts = duration_str.split(':')
        total_duration = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])

        if not silence_segments:
            # 没有静音片段，保留整个视频
            return [(0, total_duration)]

        keep_segments = []
        current_pos = 0

        for silence_start, silence_end in silence_segments:
            # 添加静音前的有用片段
            segment_end = max(0, silence_start + after_padding)
            if current_pos < segment_end:
                keep_segments.append((current_pos, segment_end))

            # 下一个片段从静音后开始
            current_pos = max(0, silence_end - before_padding)

        # 添加最后一个片段
        if current_pos < total_duration:
            keep_segments.append((current_pos, total_duration))

        # 合并重叠的片段
        merged_segments = []
        for start, end in keep_segments:
            if not merged_segments or merged_segments[-1][1] < start:
                merged_segments.append((start, end))
            else:
                # 合并重叠片段
                merged_segments[-1] = (merged_segments[-1][0], max(merged_segments[-1][1], end))

        return merged_segments

    def process_video(self,
                     input_path: str,
                     output_path: str,
                     config: Dict) -> bool:
        """
        处理视频，移除静音片段

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            config: 配置参数

        Returns:
            处理是否成功
        """
        try:
            print(f"开始处理视频: {input_path}")

            # 检测静音片段
            silence_segments = self.detect_silence_segments(
                input_path,
                config['silence_threshold'],
                config['min_silence_duration']
            )

            # 计算保留片段
            keep_segments = self.calculate_keep_segments(
                input_path,
                silence_segments,
                config['before_padding'],
                config['after_padding']
            )

            print(f"将保留 {len(keep_segments)} 个片段")

            # 生成ffmpeg命令
            if len(keep_segments) == 1:
                # 单个片段处理
                start_time, end_time = keep_segments[0]
                video_info = self.get_video_info(input_path)
                duration_str = video_info.get('duration', '00:00:00.00')
                time_parts = duration_str.split(':')
                total_duration = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])

                # 检查是否为完整视频（误差在1秒内）
                is_full_video = (abs(start_time) < 0.1 and abs(end_time - total_duration) < 1.0)

                if is_full_video:
                    # 几乎是完整视频，直接复制
                    print("检测到完整视频，直接复制...")
                    cmd = [
                        self.ffmpeg_path, "-i", input_path,
                        "-c", "copy", "-y", output_path
                    ]
                else:
                    # 需要裁剪，使用重编码确保稳定性
                    print(f"裁剪单个片段: {start_time:.2f}s - {end_time:.2f}s")
                    duration = end_time - start_time
                    cmd = [
                        self.ffmpeg_path, "-i", input_path,
                        "-ss", str(start_time),
                        "-t", str(duration),
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-preset", "fast",
                        "-crf", "23",
                        "-avoid_negative_ts", "make_zero",
                        "-y", output_path
                    ]
            else:
                # 需要拼接多个片段
                return self._concat_segments(input_path, output_path, keep_segments)

            print("正在生成输出视频...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )

            if result.returncode != 0:
                print(f"ffmpeg错误: {result.stderr}")
                return False

            print(f"视频处理完成: {output_path}")
            return True

        except Exception as e:
            print(f"处理视频时发生错误: {str(e)}")
            return False

    def _concat_segments(self, input_path: str, output_path: str, segments: List[Tuple[float, float]]) -> bool:
        """拼接多个视频片段"""
        print(f"需要拼接 {len(segments)} 个片段")

        # 使用filter_complex方法进行无损拼接
        return self._concat_with_filter_complex(input_path, output_path, segments)

    def _concat_with_filter_complex(self, input_path: str, output_path: str, segments: List[Tuple[float, float]]) -> bool:
        """使用filter_complex进行视频拼接"""
        try:
            # 构建filter_complex表达式
            filter_parts = []
            input_specs = []

            for i, (start, end) in enumerate(segments):
                duration = end - start

                # 添加输入规范
                input_specs.extend([
                    "-ss", str(start),
                    "-t", str(duration),
                    "-i", input_path
                ])

                # 构建过滤器部分
                filter_parts.append(f"[{i}:v][{i}:a]")

            # 构建完整的filter_complex
            filter_expression = "".join(filter_parts) + f"concat=n={len(segments)}:v=1:a=1[outv][outa]"

            # 构建完整的FFmpeg命令
            cmd = [self.ffmpeg_path]
            cmd.extend(input_specs)  # 添加所有输入
            cmd.extend([
                "-filter_complex", filter_expression,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                "-crf", "23",
                "-avoid_negative_ts", "make_zero",
                "-y", output_path
            ])

            print("正在使用filter_complex拼接视频片段...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

            if result.returncode != 0:
                print(f"filter_complex拼接失败，尝试备用方法")
                print(f"错误信息: {result.stderr}")
                # 尝试备用方法
                return self._concat_segments_fallback(input_path, output_path, segments)

            return True

        except Exception as e:
            print(f"filter_complex拼接出错: {str(e)}")
            # 尝试备用方法
            return self._concat_segments_fallback(input_path, output_path, segments)

    def _concat_segments_fallback(self, input_path: str, output_path: str, segments: List[Tuple[float, float]]) -> bool:
        """备用的片段拼接方法"""
        temp_dir = tempfile.mkdtemp()
        segment_files = []

        try:
            print("使用备用拼接方法...")
            # 提取每个片段并重新编码
            for i, (start, end) in enumerate(segments):
                segment_file = os.path.join(temp_dir, f"segment_{i:04d}.mp4")
                segment_files.append(segment_file)

                duration = end - start
                print(f"提取片段 {i+1}/{len(segments)}: {start:.2f}s-{end:.2f}s (时长: {duration:.2f}s)")

                cmd = [
                    self.ffmpeg_path, "-i", input_path,
                    "-ss", str(start),
                    "-t", str(duration),
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    "-crf", "23",
                    "-avoid_negative_ts", "make_zero",
                    "-y", segment_file
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    print(f"提取片段 {i+1} 失败: {result.stderr}")
                    raise Exception(f"提取片段失败: {result.stderr}")

            # 创建拼接列表文件
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for segment_file in segment_files:
                    # 使用绝对路径避免路径问题
                    abs_path = os.path.abspath(segment_file).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")

            print("正在拼接所有片段...")
            # 拼接视频
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-y", output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            if result.returncode != 0:
                print(f"拼接失败: {result.stderr}")
                raise Exception(f"拼接视频失败: {result.stderr}")

            return True

        except Exception as e:
            print(f"备用拼接方法失败: {str(e)}")
            return False
        finally:
            # 清理临时文件
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def sample_audio_volume(self, video_path: str, start_time: float, duration: float = 5.0) -> float:
        """
        采样音频片段的音量，用于设置阈值参考

        Args:
            video_path: 视频文件路径
            start_time: 采样开始时间（秒）
            duration: 采样持续时间（秒）

        Returns:
            平均音量（dB）
        """
        try:
            audio_data, sample_rate = self.extract_audio_data(video_path, start_time, duration)
            db_values = self.calculate_volume_db(audio_data)

            # 计算RMS音量
            rms_db = np.sqrt(np.mean(db_values ** 2))
            return float(rms_db)

        except Exception as e:
            print(f"采样音频音量失败: {str(e)}")
            return -40.0  # 返回默认值


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频静音片段过滤工具")
    parser.add_argument("input", help="输入视频文件路径")
    parser.add_argument("output", help="输出视频文件路径")
    parser.add_argument("--preset", choices=["slow", "medium", "fast"],
                       default="fast", help="预设节奏档位")
    parser.add_argument("--custom", action="store_true", help="使用自定义参数")
    parser.add_argument("--threshold", type=float, default=-35, help="静音阈值（dB）")
    parser.add_argument("--before", type=float, default=0.3, help="有用片段前保留时间（秒）")
    parser.add_argument("--after", type=float, default=0.5, help="有用片段后保留时间（秒）")
    parser.add_argument("--min-duration", type=float, default=0.8, help="最小静音持续时间（秒）")
    parser.add_argument("--ffmpeg-path", default="ffmpeg", help="ffmpeg可执行文件路径")
    parser.add_argument("--sample", help="采样音频片段 格式: start_time,duration")

    args = parser.parse_args()

    # 初始化过滤器
    filter_tool = VideoSilenceFilter(args.ffmpeg_path)

    # 检查ffmpeg
    if not filter_tool.check_ffmpeg():
        print(f"错误: 无法找到ffmpeg，请检查路径: {args.ffmpeg_path}")
        sys.exit(1)

    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    # 音频采样功能
    if args.sample:
        try:
            start_time, duration = map(float, args.sample.split(','))
            volume = filter_tool.sample_audio_volume(args.input, start_time, duration)
            print(f"采样片段音量: {volume:.2f} dB")
            print(f"建议静音阈值: {volume - 10:.2f} dB")
            sys.exit(0)
        except ValueError:
            print("错误: 采样参数格式应为 'start_time,duration'")
            sys.exit(1)

    # 确定配置参数
    if args.custom:
        config = {
            "silence_threshold": args.threshold,
            "before_padding": args.before,
            "after_padding": args.after,
            "min_silence_duration": args.min_duration
        }
        print(f"使用自定义配置: {config}")
    else:
        config = filter_tool.preset_configs[args.preset]
        print(f"使用预设配置 '{args.preset}': {config}")

    # 处理视频
    success = filter_tool.process_video(args.input, args.output, config)

    if success:
        print("处理完成！")
        sys.exit(0)
    else:
        print("处理失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()