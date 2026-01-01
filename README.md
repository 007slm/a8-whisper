# A8轻语 (A8Wisper)

<div align="center">

![A8轻语](https://img.shields.io/badge/A8轻语-Windows%20AI%20Voice%20Assistant-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green?style=flat-square&logo=qt)
![React](https://img.shields.io/badge/React-18.3-blue?style=flat-square&logo=react)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**一个模仿 Wispr Flow 体验的 Windows AI 语音助手**

*通过全局快捷键录音，本地 GPU 加速语音转文字，LLM 智能润色，一键输入到任意应用*

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [系统要求](#-系统要求) • [使用说明](#-使用说明) • [开发指南](#-开发指南)

</div>

---

## 🎯 项目简介

A8轻语是一个运行在 Windows 上的 AI 语音助手，旨在提供类似 Wispr Flow 的流畅语音输入体验。通过先进的本地 AI 技术栈，实现从语音到文字的智能转换和优化。

### 🆚 为什么选择 A8轻语？(Wispr Flow 开源替代方案)

如果你正在寻找 [Wispr Flow](https://wisprflow.ai/) 的替代方案，A8轻语提供了以下独特优势：

| 特性对比 | A8轻语 | Wispr Flow |
|---------|--------|------------|
| **隐私保护** | 🔒 **100% 本地处理，零数据上传** | ☁️ 默认云端转录 |
| **使用成本** | 🆓 **完全免费，无限制使用** | 💰 免费版 2000词/周，Pro版 $15/月 |
| **开源程度** | 🛠️ **完全开源，可自定义修改** | 🔒 闭源商业软件 |
| **数据控制** | 🏠 **完全掌控，符合企业合规** | 📡 依赖第三方云服务 |
| **性能优化** | ⚡ **GPU 加速，本地极速处理** | 💻 云端处理，受网络影响 |
| **定制能力** | 🎨 **可修改界面、模型、功能** | ❌ 功能受限于官方更新 |

**适合 A8轻语 的用户：**
- 🔐 对数据隐私有严格要求的个人/企业用户
- 💰 不想支付月费，追求长期免费使用
- 👨‍💻 有技术背景，喜欢开源可控的解决方案
- ⚡ 拥有 NVIDIA GPU，追求本地极致性能
- 🏢 企业环境，需要完全的数据主权控制
- 🛠️ 需要针对特定场景进行功能定制

### 🌟 核心亮点

- **🎤 全局语音输入**: 任意应用中通过 `Ctrl + Win` 快捷键启动录音
- **⚡ GPU 加速**: 利用 NVIDIA GPU 进行 Faster-Whisper 语音识别加速  
- **🧠 智能润色**: 集成本地 LLM 对识别结果进行语法优化和格式化
- **🎨 现代化界面**: 混合架构 - PySide6 原生覆盖层 + React 设置界面
- **🔒 隐私优先**: 完全本地处理，无需联网，保护用户隐私
- **🎛️ 高度可配置**: 支持多种 ASR 模型、自定义提示词、用户词典等
- **🆓 完全免费**: 开源项目，无使用限制，无订阅费用
- **🛠️ 可定制化**: 开放源码，支持功能扩展和界面修改

## ✨ 功能特性

### 🎙️ 语音识别 (ASR)
- **Faster-Whisper 引擎**: 支持 `small`、`medium`、`large-v3` 多种模型
- **GPU 加速**: 自动检测并使用 NVIDIA GPU (CUDA) + Float16 精度
- **智能提示**: 可配置 `initial_prompt` 提升专业术语识别准确率
- **一键下载**: GUI 内置模型下载器，支持断点续传

### 🤖 LLM 文本处理
- **本地 LLM**: 集成 Qwen2.5-Coder-7B-Instruct 模型
- **智能润色**: 自动修正同音字、错别字、标点符号
- **用户词典**: 支持自定义专业术语词典
- **上下文感知**: 保持原意的同时优化表达

### 🖥️ 用户界面
- **原生覆盖层**: PySide6 实现的现代化录音界面
- **React 设置面板**: 基于 Vite + TypeScript 的配置界面
- **系统托盘**: 后台运行，随时调用
- **实时反馈**: 录音状态、处理进度可视化

### ⚙️ 系统集成
- **全局快捷键**: 系统级热键监听
- **智能输入**: 自动模拟键盘输入到当前光标位置
- **多应用兼容**: 支持任意 Windows 应用程序
- **开机自启**: 可选的系统启动项配置

## 🔧 系统要求

### 硬件要求
- **操作系统**: Windows 10/11 (64-bit)
- **内存**: 8GB RAM (推荐 16GB+)
- **显卡**: NVIDIA GPU (支持 CUDA 11.8+) - 推荐 RTX 系列
- **存储**: 10GB+ 可用空间 (用于模型文件)

### 软件依赖
- **Python**: 3.10+ 
- **CUDA**: 11.8+ (用于 GPU 加速)
- **Node.js**: 18+ (开发模式)

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/007slm/a8-whisper.git
cd a8-whisper
```

### 2. 安装 Python 依赖
```bash
# 安装 uv (推荐的包管理器)
pip install uv

# 创建虚拟环境并安装依赖
uv sync
```

### 3. 安装前端依赖
```bash
cd gui_web
npm install
# 或使用 pnpm
pnpm install
```

### 4. 启动应用

#### 开发模式 (推荐)
```powershell
# 使用 PowerShell 脚本启动 (自动处理前端构建和热重载)
.\run_webview.ps1
```

#### 手动启动
```powershell
# 激活虚拟环境并启动
.venv\Scripts\python src/main_webview.py
```

#### 构建发布版本
```powershell
# 构建完整的可执行文件
.\build.ps1

# 快速构建 (跳过前端构建，如果前端未更改)
.\build.ps1 -SkipFrontend

# 完全清理构建 (强制重新构建所有组件)
.\build.ps1 -Clean
```

### 5. 首次配置
1. 应用启动后会显示在系统托盘
2. 右键托盘图标选择 "显示设置"
3. 在设置界面中下载所需的 ASR 模型
4. 配置快捷键和其他选项
5. 开始使用！

## 📖 使用说明

### 基本使用流程
1. **激活录音**: 按住 `Ctrl + Win` (可自定义)
2. **开始说话**: 看到录音界面后开始语音输入
3. **停止录音**: 松开快捷键
4. **自动处理**: 系统自动进行语音识别和文本润色
5. **智能输入**: 处理完成的文本自动输入到当前光标位置

### 高级配置

#### ASR 模型选择
- **small**: 快速响应，适合简单对话
- **medium**: 平衡性能和准确率
- **large-v3**: 最高准确率，适合专业内容

#### 自定义提示词
```
以下是关于软件开发、Python编程、AI模型训练的中英混合技术讨论。
```

#### 用户词典示例
```json
["Python", "PySide6", "LLM", "A8轻语", "Transformer", "CUDA"]
```

## 🏗️ 项目架构

```
a8-whisper/
├── src/                    # Python 后端
│   ├── core/              # 核心功能模块
│   │   ├── asr.py         # 语音识别引擎
│   │   ├── llm.py         # LLM 处理引擎
│   │   └── audio.py       # 音频处理
│   ├── ui/                # 用户界面
│   │   └── native_overlay/ # PySide6 覆盖层
│   ├── main_webview.py    # 主程序入口
│   ├── api_server.py      # WebSocket API 服务
│   └── webview_bridge.py  # 前后端桥接
├── gui_web/               # React 前端
│   ├── src/
│   │   ├── components/    # UI 组件
│   │   ├── lib/          # 工具库
│   │   └── App.tsx       # 主应用
│   └── dist/             # 构建输出
├── models/               # AI 模型文件
└── soc/                 # 设计文档和资源
```

### 技术栈

#### 后端 (Python)
- **PySide6**: 原生 GUI 框架
- **Faster-Whisper**: GPU 加速语音识别
- **llama-cpp-python**: 本地 LLM 推理
- **WebSockets**: 实时通信
- **PyWebView**: 混合应用框架

#### 前端 (React)
- **React 18**: 现代化 UI 框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 原子化 CSS
- **Radix UI**: 无障碍组件库
- **Vite**: 快速构建工具

## 🛠️ 开发指南

### 开发环境设置
```powershell
# 1. 克隆项目
git clone https://github.com/007slm/a8-whisper.git
cd a8-whisper

# 2. 设置 Python 环境
uv sync

# 3. 设置前端环境
cd gui_web
npm install
cd ..

# 4. 启动开发模式 (一键启动)
.\run_webview.ps1
```

### 构建发布版本
```powershell
# 完整构建 (包含前端)
.\build.ps1

# 快速构建 (如果前端未更改)
.\build.ps1 -SkipFrontend

# 清理构建 (强制重新构建)
.\build.ps1 -Clean
```

构建完成后，可执行文件位于 `dist/A8轻语/A8轻语.exe`

### 贡献指南
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 🐛 故障排除

### 常见问题

#### GPU 加速不工作
```bash
# 检查 CUDA 安装
nvidia-smi

# 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"
```

#### 模型下载失败
- 检查网络连接
- 尝试使用 HuggingFace 镜像站
- 确保有足够的磁盘空间

#### 快捷键冲突
- 在设置界面中修改快捷键组合
- 确保没有其他应用占用相同快捷键

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - 高效的语音识别引擎
- [Qwen2.5](https://github.com/QwenLM/Qwen2.5) - 强大的本地 LLM
- [PySide6](https://doc.qt.io/qtforpython/) - 跨平台 GUI 框架
- [Wispr Flow](https://wispr.ai/) - 设计灵感来源

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/007slm/a8-whisper)
- **问题反馈**: [Issues](https://github.com/007slm/a8-whisper/issues)
- **功能建议**: [Discussions](https://github.com/007slm/a8-whisper/discussions)

## 🔗 相关项目

- **[Wispr Flow](https://wisprflow.ai/)** - 商业语音输入软件，本项目的灵感来源
- **[Faster-Whisper](https://github.com/guillaumekln/faster-whisper)** - 高效的语音识别引擎
- **[Qwen2.5](https://github.com/QwenLM/Qwen2.5)** - 强大的本地 LLM

## ❓ 常见问题

### 为什么不直接使用 Wispr Flow？
A8轻语作为开源替代方案，主要解决以下痛点：
- **隐私担忧**: Wispr Flow 默认云端处理，A8轻语完全本地化
- **成本问题**: Wispr Flow 专业版需月费，A8轻语完全免费
- **定制需求**: 闭源软件难以修改，开源项目可自由定制
- **数据主权**: 企业用户需要完全控制敏感数据流

### 性能要求高吗？
- **最低要求**: NVIDIA GPU (GTX 1060 或更高)
- **推荐配置**: RTX 系列显卡 + 16GB RAM
- **存储需求**: 约 10GB (包含 AI 模型)

### 支持哪些语言？
目前主要优化中文识别，同时支持：
- 中英文混合输入
- 100+ 种语言 (基于 Whisper 模型)
- 可自定义专业术语词典

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by [007slm](https://github.com/007slm)

</div>
