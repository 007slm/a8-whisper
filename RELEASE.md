# Release 发布指南

## 📦 创建 Release 的步骤

### 1. 准备构建环境
```powershell
# 确保所有依赖已安装
uv sync

# 构建前端
cd gui_web
npm run build
cd ..
```

### 2. 构建可执行文件
```powershell
# 使用构建脚本创建 EXE
.\build.ps1

# 检查构建结果
ls dist/A8轻语/
```

### 3. 测试构建版本
```powershell
# 运行构建的 EXE 确保正常工作
.\dist\A8轻语\A8轻语.exe
```

### 4. 打包 Release
```powershell
# 创建发布包
$version = "v1.0.0"  # 更新版本号
$releaseName = "A8轻语-$version"

# 压缩发布文件
Compress-Archive -Path "dist/A8轻语/*" -DestinationPath "$releaseName.zip"
```

### 5. 创建 GitHub Release

1. 前往 GitHub 仓库页面
2. 点击 "Releases" → "Create a new release"
3. 填写以下信息：

**Tag version**: `v1.0.0`
**Release title**: `A8轻语 v1.0.0 - 首个稳定版本`

**Release notes 模板**:
```markdown
## 🎉 A8轻语 v1.0.0

### ✨ 新功能
- 🎤 全局快捷键语音输入 (Ctrl + Win)
- ⚡ GPU 加速的 Faster-Whisper 语音识别
- 🧠 本地 LLM 智能文本润色
- 🎨 现代化混合 UI (PySide6 + React)
- 🔒 完全本地处理，保护隐私

### 📋 系统要求
- Windows 10/11 (64-bit)
- NVIDIA GPU (GTX 1060 或更高)
- 8GB RAM (推荐 16GB+)
- 10GB+ 可用存储空间

### 📥 安装说明
1. 下载 `A8轻语-v1.0.0.zip`
2. 解压到任意目录
3. 双击 `A8轻语.exe` 启动
4. 首次运行需点击界面上的“下载模型”按钮手动下载 AI 模型

### 🐛 已知问题
- 首次启动需要下载约 3GB 的 AI 模型
- 需要稳定的网络连接下载模型

### 🙏 致谢
感谢所有测试用户的反馈和建议！

---
**完整更新日志**: https://github.com/007slm/a8-whisper/compare/v0.9.0...v1.0.0
```

4. 上传 `A8轻语-v1.0.0.zip` 文件
5. 勾选 "Set as the latest release"
6. 点击 "Publish release"

## 🔄 版本号规则

使用语义化版本控制 (Semantic Versioning):
- **主版本号 (Major)**: 不兼容的 API 修改
- **次版本号 (Minor)**: 向下兼容的功能性新增
- **修订号 (Patch)**: 向下兼容的问题修正

示例:
- `v1.0.0` - 首个稳定版本
- `v1.1.0` - 新增功能
- `v1.1.1` - 修复 bug
- `v2.0.0` - 重大更新

## 📝 发布检查清单 (Release Checklist)

发布前请检查以下项目:

- [ ] 代码已合并到 main 分支
- [ ] 所有自动化测试通过
- [ ] 版本号已更新 (VERSION & pyproject.toml)
- [ ] 构建成功且 EXE 可正常运行
- [ ] 已准备 Release Notes (更新日志)
- [ ] 文件大小合理 (< 500MB)
- [ ] 包含必要的依赖文件 (如 jaraco/backports)
- [ ] 在干净的 Windows 系统上测试了安装和运行

## 🚀 自动化构建 (未来)

可以考虑使用 GitHub Actions 自动化构建和发布流程。