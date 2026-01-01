# 更新日志

所有重要的项目更改都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- [ ] 支持更多语言模型
- [ ] 添加语音命令功能
- [ ] 优化 GPU 内存使用
- [ ] 支持自定义快捷键组合

## [1.0.0] - 2025-01-01

### 新增
- 🎤 全局快捷键语音输入 (Ctrl + Win)
- ⚡ GPU 加速的 Faster-Whisper 语音识别
- 🧠 本地 LLM (Qwen2.5-Coder-7B) 智能文本润色
- 🎨 现代化混合 UI (PySide6 原生覆盖层 + React 设置界面)
- 🔒 完全本地处理，保护用户隐私
- 🎛️ 可配置的 ASR 模型 (small/medium/large-v3)
- 📝 自定义提示词和用户词典
- 🖥️ 系统托盘集成
- 📦 一键构建脚本 (build.ps1)
- 🚀 开发模式热重载 (run_webview.ps1)

### 技术特性
- 支持中英文混合语音识别
- WebSocket 实时通信架构
- PyInstaller 打包支持
- 自动模型下载和管理
- GPU 内存优化

### 系统要求
- Windows 10/11 (64-bit)
- NVIDIA GPU (GTX 1060 或更高)
- 8GB RAM (推荐 16GB+)
- 10GB+ 可用存储空间

---

## 版本说明

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增  
- **修订号**: 向下兼容的问题修正

[未发布]: https://github.com/007slm/a8-whisper/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/007slm/a8-whisper/releases/tag/v1.0.0