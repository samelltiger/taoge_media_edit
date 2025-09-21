// 全局变量
let uploadedFile = null;
let audioContext = null;
let audioBuffer = null;
let waveformData = null;
let silenceSegments = [];
let voiceSegments = [];

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const configSection = document.getElementById('configSection');
const waveformSection = document.getElementById('waveformSection');
const outputSection = document.getElementById('outputSection');

// 预设参数
const presets = {
    slow: { threshold: -50, leading: 0.5, trailing: 0.8, desc: '适用于访谈、播客等停顿较多的场景' },
    medium: { threshold: -40, leading: 0.3, trailing: 0.5, desc: '适用于大多数标准口播视频' },
    fast: { threshold: -35, leading: 0.2, trailing: 0.3, desc: '适用于信息密集、语速快的短视频' },
    custom: { threshold: -40, leading: 0.3, trailing: 0.5, desc: '自定义参数设置' }
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializePresets();
    initializeParameterSync();
    initializeAdvancedToggle();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 文件上传相关
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);

    // 波形相关
    const samplingBtn = document.getElementById('samplingBtn');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    samplingBtn?.addEventListener('click', toggleSamplingMode);
    playBtn?.addEventListener('click', playAudio);
    pauseBtn?.addEventListener('click', pauseAudio);

    // 处理相关
    const previewBtn = document.getElementById('previewBtn');
    const processBtn = document.getElementById('processBtn');

    previewBtn?.addEventListener('click', generatePreview);
    processBtn?.addEventListener('click', startProcessing);
}

// 初始化预设
function initializePresets() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    const modeDesc = document.getElementById('modeDesc');

    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 移除所有active类
            modeButtons.forEach(b => b.classList.remove('active'));
            // 添加active类到当前按钮
            btn.classList.add('active');

            const mode = btn.dataset.mode;
            const preset = presets[mode];

            if (preset) {
                // 更新描述
                modeDesc.textContent = preset.desc;

                // 更新参数（除非是自定义模式）
                if (mode !== 'custom') {
                    updateParameters(preset);
                }
            }
        });
    });
}

// 更新参数
function updateParameters(preset) {
    const silenceThreshold = document.getElementById('silenceThreshold');
    const silenceThresholdValue = document.getElementById('silenceThresholdValue');
    const leadingPadding = document.getElementById('leadingPadding');
    const leadingPaddingValue = document.getElementById('leadingPaddingValue');
    const trailingPadding = document.getElementById('trailingPadding');
    const trailingPaddingValue = document.getElementById('trailingPaddingValue');

    if (silenceThreshold && silenceThresholdValue) {
        silenceThreshold.value = preset.threshold;
        silenceThresholdValue.value = preset.threshold;
    }
    if (leadingPadding && leadingPaddingValue) {
        leadingPadding.value = preset.leading;
        leadingPaddingValue.value = preset.leading;
    }
    if (trailingPadding && trailingPaddingValue) {
        trailingPadding.value = preset.trailing;
        trailingPaddingValue.value = preset.trailing;
    }

    // 更新阈值线位置
    updateThresholdLine();
}

// 初始化参数同步
function initializeParameterSync() {
    const params = [
        'silenceThreshold',
        'leadingPadding',
        'trailingPadding',
        'minSilenceDuration',
        'minVoiceDuration'
    ];

    params.forEach(param => {
        const slider = document.getElementById(param);
        const input = document.getElementById(param + 'Value');

        if (slider && input) {
            slider.addEventListener('input', (e) => {
                input.value = e.target.value;
                if (param === 'silenceThreshold') {
                    updateThresholdLine();
                }
                // 切换到自定义模式
                switchToCustomMode();
            });

            input.addEventListener('input', (e) => {
                slider.value = e.target.value;
                if (param === 'silenceThreshold') {
                    updateThresholdLine();
                }
                // 切换到自定义模式
                switchToCustomMode();
            });
        }
    });
}

// 切换到自定义模式
function switchToCustomMode() {
    const customBtn = document.querySelector('.mode-btn[data-mode="custom"]');
    const modeButtons = document.querySelectorAll('.mode-btn');
    const modeDesc = document.getElementById('modeDesc');

    if (customBtn) {
        modeButtons.forEach(btn => btn.classList.remove('active'));
        customBtn.classList.add('active');
        modeDesc.textContent = presets.custom.desc;
    }
}

// 初始化高级参数切换
function initializeAdvancedToggle() {
    const toggleBtn = document.getElementById('toggleAdvanced');
    const advancedContent = document.querySelector('.advanced-content');

    if (toggleBtn && advancedContent) {
        toggleBtn.addEventListener('click', () => {
            const isVisible = advancedContent.style.display !== 'none';
            advancedContent.style.display = isVisible ? 'none' : 'grid';
            toggleBtn.textContent = isVisible ? '展开' : '收起';
        });
    }
}

// 拖拽处理
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// 文件选择处理
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    // 验证文件类型
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'video/mp4', 'video/quicktime'];
    const validExtensions = ['.mp3', '.wav', '.m4a', '.mp4', '.mov'];

    const isValidType = validTypes.some(type => file.type.includes(type));
    const isValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValidType && !isValidExtension) {
        showError('不支持的文件格式，请选择 MP4, MOV, MP3, WAV, M4A 格式的文件');
        return;
    }

    uploadedFile = file;
    showFileInfo(file);
    simulateUpload();
}

// 显示文件信息
function showFileInfo(file) {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileDuration = document.getElementById('fileDuration');

    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (fileDuration) fileDuration.textContent = '正在分析...';

    fileInfo.style.display = 'block';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 模拟上传进度
function simulateUpload() {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setTimeout(() => {
                onUploadComplete();
            }, 500);
        }

        if (progressBar) progressBar.style.width = progress + '%';
        if (progressText) progressText.textContent = Math.round(progress) + '%';
    }, 200);
}

// 上传完成
function onUploadComplete() {
    const fileDuration = document.getElementById('fileDuration');
    if (fileDuration) {
        // 模拟音频时长
        const duration = Math.floor(Math.random() * 3600 + 300); // 5-65分钟
        fileDuration.textContent = formatDuration(duration);
    }

    // 显示配置区域
    configSection.style.display = 'block';

    // 模拟音频分析
    setTimeout(() => {
        analyzeAudio();
    }, 1000);
}

// 格式化时长
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// 分析音频
function analyzeAudio() {
    // 模拟音频分析过程
    showSuccess('音频分析完成，正在生成波形图...');

    setTimeout(() => {
        generateWaveform();
        waveformSection.style.display = 'block';
        outputSection.style.display = 'block';
    }, 1500);
}

// 生成波形图
function generateWaveform() {
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = 200;

    // 生成模拟波形数据
    generateMockWaveformData(width);

    // 绘制波形
    drawWaveform(ctx, width, height);

    // 更新统计信息
    updateSegmentStats();

    // 初始化阈值线
    updateThresholdLine();
}

// 生成模拟波形数据
function generateMockWaveformData(width) {
    waveformData = [];
    silenceSegments = [];
    voiceSegments = [];

    const threshold = parseFloat(document.getElementById('silenceThreshold')?.value || -40);

    for (let i = 0; i < width; i++) {
        // 生成带有静音片段的模拟音频数据
        let amplitude;
        if (Math.random() < 0.3) { // 30%概率为静音
            amplitude = Math.random() * 0.1 - 0.8; // -0.8 到 -0.7 (静音)
        } else {
            amplitude = Math.random() * 0.6 - 0.3; // -0.3 到 0.3 (有声)
        }

        waveformData.push(amplitude);
    }

    // 分析片段
    analyzeSegments(threshold);
}

// 分析片段
function analyzeSegments(threshold) {
    if (!waveformData) return;

    silenceSegments = [];
    voiceSegments = [];

    let currentSegmentStart = 0;
    let currentSegmentType = null; // 'silence' or 'voice'

    const thresholdNormalized = (threshold + 60) / 60; // 转换到0-1范围

    for (let i = 0; i < waveformData.length; i++) {
        const amplitude = Math.abs(waveformData[i]);
        const isVoice = amplitude > Math.abs(thresholdNormalized);
        const segmentType = isVoice ? 'voice' : 'silence';

        if (currentSegmentType === null) {
            currentSegmentType = segmentType;
            currentSegmentStart = i;
        } else if (currentSegmentType !== segmentType) {
            // 保存当前片段
            const segment = {
                start: currentSegmentStart,
                end: i - 1,
                type: currentSegmentType
            };

            if (currentSegmentType === 'silence') {
                silenceSegments.push(segment);
            } else {
                voiceSegments.push(segment);
            }

            // 开始新片段
            currentSegmentType = segmentType;
            currentSegmentStart = i;
        }
    }

    // 保存最后一个片段
    if (currentSegmentType) {
        const segment = {
            start: currentSegmentStart,
            end: waveformData.length - 1,
            type: currentSegmentType
        };

        if (currentSegmentType === 'silence') {
            silenceSegments.push(segment);
        } else {
            voiceSegments.push(segment);
        }
    }
}

// 绘制波形
function drawWaveform(ctx, width, height) {
    if (!waveformData) return;

    ctx.clearRect(0, 0, width, height);

    const centerY = height / 2;
    const maxAmplitude = Math.max(...waveformData.map(Math.abs));

    // 绘制背景
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);

    // 绘制中心线
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();

    // 绘制波形
    for (let i = 0; i < waveformData.length; i++) {
        const amplitude = waveformData[i];
        const normalizedAmplitude = (amplitude / maxAmplitude) * (centerY - 10);

        // 根据片段类型选择颜色
        const isInSilenceSegment = silenceSegments.some(seg => i >= seg.start && i <= seg.end);
        ctx.fillStyle = isInSilenceSegment ? '#9ca3af' : '#3b82f6';

        const barHeight = Math.abs(normalizedAmplitude);
        const x = i;
        const y = centerY - barHeight / 2;

        ctx.fillRect(x, y, 1, barHeight);
    }
}

// 更新阈值线
function updateThresholdLine() {
    const thresholdLine = document.getElementById('thresholdLine');
    const canvas = document.getElementById('waveformCanvas');
    const threshold = parseFloat(document.getElementById('silenceThreshold')?.value || -40);

    if (thresholdLine && canvas) {
        // 将dB值转换为画布位置
        const normalizedThreshold = (threshold + 60) / 60; // -60dB 到 0dB 映射到 0-1
        const position = canvas.offsetHeight * (1 - normalizedThreshold);

        thresholdLine.style.top = position + 'px';

        // 重新分析片段
        if (waveformData) {
            analyzeSegments(threshold);
            const ctx = canvas.getContext('2d');
            drawWaveform(ctx, canvas.offsetWidth, canvas.offsetHeight);
            updateSegmentStats();
        }
    }
}

// 更新片段统计
function updateSegmentStats() {
    const validSegmentsEl = document.getElementById('validSegments');
    const silentSegmentsEl = document.getElementById('silentSegments');
    const totalDurationEl = document.getElementById('totalDuration');
    const keepDurationEl = document.getElementById('keepDuration');

    if (validSegmentsEl) validSegmentsEl.textContent = voiceSegments.length;
    if (silentSegmentsEl) silentSegmentsEl.textContent = silenceSegments.length;
    if (totalDurationEl) totalDurationEl.textContent = '45:32'; // 模拟总时长
    if (keepDurationEl) keepDurationEl.textContent = '38:45'; // 模拟保留时长
}

// 采样模式
let samplingMode = false;

function toggleSamplingMode() {
    const samplingBtn = document.getElementById('samplingBtn');
    samplingMode = !samplingMode;

    if (samplingMode) {
        samplingBtn.classList.add('active');
        samplingBtn.textContent = '🎯 点击波形采样';
        // 添加画布点击事件
        const canvas = document.getElementById('waveformCanvas');
        if (canvas) {
            canvas.style.cursor = 'crosshair';
            canvas.addEventListener('click', handleWaveformSampling);
        }
    } else {
        samplingBtn.classList.remove('active');
        samplingBtn.textContent = '🎯 采样工具';
        // 移除画布点击事件
        const canvas = document.getElementById('waveformCanvas');
        if (canvas) {
            canvas.style.cursor = 'default';
            canvas.removeEventListener('click', handleWaveformSampling);
        }
    }
}

// 处理波形采样
function handleWaveformSampling(e) {
    if (!samplingMode || !waveformData) return;

    const canvas = e.target;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 将画布坐标转换为数据索引
    const dataIndex = Math.floor((x / canvas.offsetWidth) * waveformData.length);

    if (dataIndex >= 0 && dataIndex < waveformData.length) {
        const amplitude = Math.abs(waveformData[dataIndex]);
        // 将幅度转换为dB值（模拟）
        const dbValue = Math.round((amplitude * 60) - 60);

        // 更新阈值参数
        const silenceThreshold = document.getElementById('silenceThreshold');
        const silenceThresholdValue = document.getElementById('silenceThresholdValue');

        if (silenceThreshold && silenceThresholdValue) {
            silenceThreshold.value = dbValue;
            silenceThresholdValue.value = dbValue;
        }

        // 切换到自定义模式
        switchToCustomMode();

        // 更新阈值线
        updateThresholdLine();

        // 退出采样模式
        toggleSamplingMode();

        showSuccess(`已设置静音阈值为 ${dbValue} dB`);
    }
}

// 播放控制
function playAudio() {
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    if (playBtn) playBtn.style.display = 'none';
    if (pauseBtn) pauseBtn.style.display = 'inline-block';

    // 模拟播放
    showSuccess('开始播放音频');
}

function pauseAudio() {
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    if (playBtn) playBtn.style.display = 'inline-block';
    if (pauseBtn) pauseBtn.style.display = 'none';

    showSuccess('暂停播放');
}

// 生成预览
function generatePreview() {
    const previewAudio = document.getElementById('previewAudio');
    const previewBtn = document.getElementById('previewBtn');

    if (previewBtn) previewBtn.textContent = '🔄 正在生成预览...';

    setTimeout(() => {
        if (previewBtn) previewBtn.textContent = '🎵 生成预览';
        if (previewAudio) {
            previewAudio.style.display = 'block';
            // 在实际应用中，这里会设置处理后的音频预览
            showSuccess('预览生成完成，请播放查看效果');
        }
    }, 2000);
}

// 开始处理
function startProcessing() {
    const processBtn = document.getElementById('processBtn');
    const processStatus = document.getElementById('processStatus');
    const processBar = document.getElementById('processBar');
    const processText = document.getElementById('processText');

    if (processBtn) {
        processBtn.textContent = '🔄 处理中...';
        processBtn.disabled = true;
    }

    if (processStatus) processStatus.style.display = 'block';

    // 模拟处理进度
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 5;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setTimeout(() => {
                onProcessingComplete();
            }, 500);
        }

        if (processBar) processBar.style.width = progress + '%';
        if (processText) {
            if (progress < 30) {
                processText.textContent = '正在分析音频...';
            } else if (progress < 70) {
                processText.textContent = '正在处理静音片段...';
            } else if (progress < 95) {
                processText.textContent = '正在生成输出文件...';
            } else {
                processText.textContent = '处理完成！';
            }
        }
    }, 300);
}

// 处理完成
function onProcessingComplete() {
    const processBtn = document.getElementById('processBtn');
    const processText = document.getElementById('processText');

    if (processBtn) {
        processBtn.textContent = '📥 下载处理后的文件';
        processBtn.disabled = false;
        processBtn.onclick = downloadFile;
    }

    if (processText) {
        processText.textContent = '处理完成！点击下载文件';
    }

    showSuccess('文件处理完成！');
}

// 下载文件
function downloadFile() {
    const outputFormat = document.getElementById('outputFormat')?.value || 'mp4';
    const outputMethod = document.getElementById('outputMethod')?.value || 'download';

    let fileName = 'processed_audio';
    let fileType = 'video/mp4';

    switch (outputMethod) {
        case 'premiere':
            fileName += '_premiere.xml';
            fileType = 'application/xml';
            break;
        case 'finalcut':
            fileName += '_finalcut.fcpxml';
            fileType = 'application/xml';
            break;
        default:
            fileName += outputFormat === 'mp3' ? '.mp3' : '.mp4';
            fileType = outputFormat === 'mp3' ? 'audio/mpeg' : 'video/mp4';
    }

    // 模拟文件下载
    const blob = new Blob(['模拟文件内容'], { type: fileType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showSuccess(`已下载 ${fileName}`);
}

// 显示错误信息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fef2f2;
        color: #dc2626;
        padding: 16px 24px;
        border-radius: 8px;
        border: 1px solid #fecaca;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        max-width: 400px;
    `;

    document.body.appendChild(errorDiv);

    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

// 显示成功信息
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f0fdf4;
        color: #059669;
        padding: 16px 24px;
        border-radius: 8px;
        border: 1px solid #dcfce7;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        max-width: 400px;
    `;

    document.body.appendChild(successDiv);

    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.parentNode.removeChild(successDiv);
        }
    }, 3000);
}

// 窗口大小调整处理
window.addEventListener('resize', () => {
    setTimeout(() => {
        const canvas = document.getElementById('waveformCanvas');
        if (canvas && waveformData) {
            const ctx = canvas.getContext('2d');
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = 200;
            drawWaveform(ctx, width, height);
            updateThresholdLine();
        }
    }, 100);
});