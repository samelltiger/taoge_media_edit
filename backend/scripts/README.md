# 视频静音片段过滤工具

这是一个用于自动检测和移除视频中静音片段的Python脚本，专为自媒体从业者的口播视频编辑而设计。

## 功能特性

1. **自动静音检测**: 智能检测视频中的静音片段
2. **三种预设档位**: 慢、中等、快三种节奏配置
3. **自定义参数**: 支持精确的自定义设置
4. **音频采样**: 可以采样特定片段来设置合适的静音阈值
5. **FFmpeg集成**: 高效的视频处理

## 安装依赖

```bash
pip install numpy
```

确保系统已安装FFmpeg：
- Windows: 下载FFmpeg并配置环境变量
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg` 或 `sudo yum install ffmpeg`

## 使用方法

### 基本用法

```bash
# 使用默认中等档位
python video_silence_filter.py input.mp4 output.mp4

# 使用快速档位
python video_silence_filter.py input.mp4 output.mp4 --preset fast

# 使用慢速档位
python video_silence_filter.py input.mp4 output.mp4 --preset slow
```

### 自定义参数

```bash
python video_silence_filter.py input.mp4 output.mp4 --custom \
    --threshold -30 \
    --before 0.2 \
    --after 0.3 \
    --min-duration 0.5
```

### 音频采样

在处理前，你可以先采样音频片段来确定合适的静音阈值：

```bash
# 从第10秒开始采样5秒钟的音频
python video_silence_filter.py input.mp4 output.mp4 --sample 10,5
```

### 指定FFmpeg路径

```bash
python video_silence_filter.py input.mp4 output.mp4 --ffmpeg-path /path/to/ffmpeg
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--preset` | 预设档位（slow/medium/fast） | medium |
| `--custom` | 启用自定义参数模式 | - |
| `--threshold` | 静音阈值（dB），越小越严格 | -35 |
| `--before` | 有用片段前保留时间（秒） | 0.3 |
| `--after` | 有用片段后保留时间（秒） | 0.5 |
| `--min-duration` | 最小静音持续时间（秒） | 0.8 |
| `--ffmpeg-path` | FFmpeg可执行文件路径 | ffmpeg |
| `--sample` | 采样音频片段，格式：开始时间,持续时间 | - |

## 预设档位配置

### 慢速档位 (slow)
- 静音阈值: -40 dB
- 前置保留: 0.5 秒
- 后置保留: 0.8 秒
- 最小静音: 1.0 秒

### 中等档位 (medium)
- 静音阈值: -35 dB
- 前置保留: 0.3 秒
- 后置保留: 0.5 秒
- 最小静音: 0.8 秒

### 快速档位 (fast)
- 静音阈值: -30 dB
- 前置保留: 0.1 秒
- 后置保留: 0.2 秒
- 最小静音: 0.5 秒

## 使用建议

1. **首次使用**: 建议先用 `--sample` 功能采样一段音频，确定合适的静音阈值
2. **口播视频**: 推荐使用中等或快速档位
3. **音质较差**: 可以适当降低静音阈值（使用更负的值）
4. **保持流畅**: 调整前后保留时间，避免过于突兀的剪切

## 示例工作流程

```bash
# 1. 首先采样音频，确定合适的阈值
python video_silence_filter.py my_video.mp4 output.mp4 --sample 60,10

# 输出类似：采样片段音量: -25.4 dB，建议静音阈值: -35.4 dB

# 2. 使用建议的阈值进行处理
python video_silence_filter.py my_video.mp4 output.mp4 --custom \
    --threshold -35 --before 0.2 --after 0.4

# 3. 如果效果不理想，调整参数重新处理
python video_silence_filter.py my_video.mp4 output_v2.mp4 --custom \
    --threshold -32 --before 0.3 --after 0.5
```

## 故障排除

1. **FFmpeg未找到**: 确保FFmpeg已正确安装并添加到系统PATH
2. **处理速度慢**: 对于大文件，处理时间较长是正常的
3. **内存不足**: 处理超长视频时可能需要更多内存
4. **音频问题**: 确保输入视频包含音轨

## 技术细节

- 使用PCM 16位单声道22050Hz采样率进行音频分析
- 采用RMS方法计算音量dB值
- 支持视频片段的无损拼接
- 自动处理时间码和同步问题