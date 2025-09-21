#!/usr/bin/env python3
"""
批量视频静音片段过滤工具

用于批量处理多个视频文件的静音片段过滤

作者：Taoge Media Edit Tool
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import concurrent.futures
import threading

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from video_silence_filter import VideoSilenceFilter


class BatchVideoProcessor:
    """批量视频处理器"""

    def __init__(self, ffmpeg_path: str = "ffmpeg", max_workers: int = 2):
        """
        初始化批处理器

        Args:
            ffmpeg_path: FFmpeg可执行文件路径
            max_workers: 最大并行工作线程数
        """
        self.ffmpeg_path = ffmpeg_path
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()

    def find_video_files(self, directory: str, extensions: List[str] = None) -> List[Path]:
        """
        查找目录中的视频文件

        Args:
            directory: 搜索目录
            extensions: 支持的视频扩展名

        Returns:
            视频文件路径列表
        """
        if extensions is None:
            extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v']

        video_files = []
        directory = Path(directory)

        if not directory.exists():
            print(f"错误: 目录不存在: {directory}")
            return video_files

        for ext in extensions:
            video_files.extend(directory.glob(f"*{ext}"))
            video_files.extend(directory.glob(f"*{ext.upper()}"))

        return sorted(video_files)

    def process_single_video(self, input_path: Path, output_dir: Path, config: Dict) -> Dict:
        """
        处理单个视频文件

        Args:
            input_path: 输入视频路径
            output_dir: 输出目录
            config: 处理配置

        Returns:
            处理结果字典
        """
        result = {
            "input_file": str(input_path),
            "output_file": "",
            "success": False,
            "error": "",
            "processed_time": 0
        }

        try:
            # 创建输出文件路径
            output_file = output_dir / f"{input_path.stem}_filtered{input_path.suffix}"
            result["output_file"] = str(output_file)

            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"正在处理: {input_path.name}")

            # 创建过滤器实例
            filter_tool = VideoSilenceFilter(self.ffmpeg_path)

            # 处理视频
            import time
            start_time = time.time()
            success = filter_tool.process_video(str(input_path), str(output_file), config)
            end_time = time.time()

            result["success"] = success
            result["processed_time"] = end_time - start_time

            if success:
                print(f"✓ 完成: {input_path.name} -> {output_file.name} (耗时: {result['processed_time']:.1f}秒)")
            else:
                result["error"] = "视频处理失败"
                print(f"✗ 失败: {input_path.name}")

        except Exception as e:
            result["error"] = str(e)
            print(f"✗ 异常: {input_path.name} - {str(e)}")

        # 线程安全地添加结果
        with self.lock:
            self.results.append(result)

        return result

    def process_batch(self,
                     input_dir: str,
                     output_dir: str,
                     config: Dict,
                     recursive: bool = False) -> List[Dict]:
        """
        批量处理视频文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            config: 处理配置
            recursive: 是否递归搜索子目录

        Returns:
            处理结果列表
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # 查找视频文件
        if recursive:
            video_files = []
            for root, dirs, files in os.walk(input_path):
                root_path = Path(root)
                video_files.extend(self.find_video_files(root_path))
        else:
            video_files = self.find_video_files(input_path)

        if not video_files:
            print(f"在目录 {input_dir} 中没有找到视频文件")
            return []

        print(f"找到 {len(video_files)} 个视频文件")

        # 清空结果列表
        self.results = []

        # 使用线程池并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 为每个输入文件创建相应的输出目录结构
            futures = []
            for video_file in video_files:
                if recursive:
                    # 保持目录结构
                    rel_path = video_file.relative_to(input_path)
                    file_output_dir = output_path / rel_path.parent
                else:
                    file_output_dir = output_path

                future = executor.submit(self.process_single_video, video_file, file_output_dir, config)
                futures.append(future)

            # 等待所有任务完成
            concurrent.futures.wait(futures)

        return self.results

    def generate_report(self, results: List[Dict], report_path: str = None):
        """
        生成处理报告

        Args:
            results: 处理结果列表
            report_path: 报告文件路径
        """
        total_files = len(results)
        successful_files = sum(1 for r in results if r["success"])
        failed_files = total_files - successful_files
        total_time = sum(r["processed_time"] for r in results)

        report = {
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "total_processing_time": total_time,
                "average_time_per_file": total_time / total_files if total_files > 0 else 0
            },
            "details": results
        }

        # 打印摘要
        print("\n=== 批处理报告 ===")
        print(f"总文件数: {total_files}")
        print(f"成功处理: {successful_files}")
        print(f"处理失败: {failed_files}")
        print(f"总耗时: {total_time:.1f} 秒")
        if total_files > 0:
            print(f"平均耗时: {total_time/total_files:.1f} 秒/文件")

        # 显示失败的文件
        if failed_files > 0:
            print("\n失败的文件:")
            for result in results:
                if not result["success"]:
                    print(f"  {result['input_file']}: {result['error']}")

        # 保存详细报告到文件
        if report_path:
            report_file = Path(report_path)
            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n详细报告已保存到: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量视频静音片段过滤工具")

    parser.add_argument("input_dir", help="输入目录")
    parser.add_argument("output_dir", help="输出目录")

    parser.add_argument("--preset", choices=["slow", "medium", "fast"],
                       default="medium", help="预设节奏档位")
    parser.add_argument("--custom", action="store_true", help="使用自定义参数")
    parser.add_argument("--threshold", type=float, default=-35, help="静音阈值（dB）")
    parser.add_argument("--before", type=float, default=0.3, help="有用片段前保留时间（秒）")
    parser.add_argument("--after", type=float, default=0.5, help="有用片段后保留时间（秒）")
    parser.add_argument("--min-duration", type=float, default=0.8, help="最小静音持续时间（秒）")

    parser.add_argument("--recursive", "-r", action="store_true", help="递归搜索子目录")
    parser.add_argument("--workers", type=int, default=2, help="并行工作线程数")
    parser.add_argument("--ffmpeg-path", default="ffmpeg", help="FFmpeg可执行文件路径")
    parser.add_argument("--report", help="报告文件保存路径")

    args = parser.parse_args()

    # 检查输入目录
    if not os.path.exists(args.input_dir):
        print(f"错误: 输入目录不存在: {args.input_dir}")
        sys.exit(1)

    # 初始化批处理器
    processor = BatchVideoProcessor(args.ffmpeg_path, args.workers)

    # 测试FFmpeg
    filter_tool = VideoSilenceFilter(args.ffmpeg_path)
    if not filter_tool.check_ffmpeg():
        print(f"错误: 无法找到FFmpeg，请检查路径: {args.ffmpeg_path}")
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
        presets = {
            "slow": {"silence_threshold": -40, "before_padding": 0.5, "after_padding": 0.8, "min_silence_duration": 1.0},
            "medium": {"silence_threshold": -35, "before_padding": 0.3, "after_padding": 0.5, "min_silence_duration": 0.8},
            "fast": {"silence_threshold": -30, "before_padding": 0.1, "after_padding": 0.2, "min_silence_duration": 0.5}
        }
        config = presets[args.preset]
        print(f"使用预设配置 '{args.preset}': {config}")

    print(f"并行线程数: {args.workers}")
    print(f"递归搜索: {'是' if args.recursive else '否'}")

    # 开始批处理
    print(f"\n开始批量处理: {args.input_dir} -> {args.output_dir}")
    results = processor.process_batch(args.input_dir, args.output_dir, config, args.recursive)

    # 生成报告
    report_path = args.report or os.path.join(args.output_dir, "batch_report.json")
    processor.generate_report(results, report_path)

    # 返回适当的退出码
    failed_count = sum(1 for r in results if not r["success"])
    if failed_count == 0:
        print("\n🎉 所有文件处理完成！")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed_count} 个文件处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()