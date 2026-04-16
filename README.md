# 大华云大模型推理套件 CLI

大华云大模型推理套件的命令行工具，支持图片、文本、视频、音频等多种 AI 能力。

## 当前文件结构

```
dahua-cloud-ai-cli/
├── src/
│   └── dahua-cloud-ai-cli.py    # 主程序
├── scripts/
│   ├── windows/
│   │   ├── dahua-cloud.cmd      # Windows CMD 入口
│   │   ├── dahua-cloud-ai-cli.ps1  # Windows PowerShell 入口
│   │   ├── install-path.bat     # Windows PATH 安装
│   │   └── uninstall-path.bat   # Windows PATH 卸载
│   └── linux-mac/
│       ├── dahua-cloud.sh       # Linux/Mac 入口
│       ├── install-path.sh      # Linux/Mac PATH 安装
│       └── uninstall-path.sh    # Linux/Mac PATH 卸载
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

## 安装与配置

### 1. 环境准备

- Python 3.8 或更高版本
- 安装依赖：`pip install requests`

### 2. 安装到 PATH（推荐日常使用）
将 `dahua-cloud-ai-cli` 目录添加到系统 PATH，即可在任意位置直接调用 `dahua-cloud`。

**Windows（自动安装）：**
```cmd
scripts\windows\install-path.bat
```

**Linux/Mac（自动安装）：**
```bash
chmod +x scripts/linux-mac/install-path.sh
./scripts/linux-mac/install-path.sh
source ~/.bashrc  # 或 ~/.zshrc
```

**手动添加到 PATH（Windows）：**
1. 复制 `dahua-cloud-ai-cli\scripts\windows` 文件夹的完整路径
2. 打开"系统属性" → "环境变量"
3. 编辑用户变量中的 "Path"，添加上述路径
4. 重新打开终端

**手动添加到 PATH（Linux/Mac）：**
```bash
# 添加以下行到 ~/.bashrc 或 ~/.zshrc（替换为实际路径）
export PATH="$PATH:/path/to/dahua-cloud-ai-cli/scripts/linux-mac"
source ~/.bashrc
```


### 3. 配置环境变量（推荐方式）

使用 `init` 命令进行交互式配置，配置会永久保存到系统环境变量：

```bash
dahua-cloud init
```

> **获取凭据**：登录 [大华云开发者平台](https://open.cloud-dahua.com/)，在产品管理中获取 Product ID、Access Key 和 Secret Key。


### 4. 配置环境变量（备选方式）

如需手动配置环境变量：

**Windows (PowerShell):**
```powershell
$env:DAHUA_CLOUD_PRODUCT_ID='your_app_id'
$env:DAHUA_CLOUD_AK='your_access_key'
$env:DAHUA_CLOUD_SK='your_secret_key'
```

**Windows (CMD):**
```cmd
set DAHUA_CLOUD_PRODUCT_ID=your_app_id
set DAHUA_CLOUD_AK=your_access_key
set DAHUA_CLOUD_SK=your_secret_key
```

**Linux/Mac:**
```bash
export DAHUA_CLOUD_PRODUCT_ID='your_app_id'
export DAHUA_CLOUD_AK='your_access_key'
export DAHUA_CLOUD_SK='your_secret_key'
```

> **获取凭据**：登录 [大华云开发者平台](https://open.cloud-dahua.com/)，在产品管理中获取 Product ID、Access Key 和 Secret Key。

### 5. 验证配置

完成后，在任意终端可直接执行：
```bash
dahua-cloud --help
dahua-cloud doctor
```

### 6. 卸载 CLI

如需从 PATH 中移除 CLI：

**Windows：**
```cmd
scripts\windows\uninstall-path.bat
```

**Linux/Mac：**
```bash
chmod +x scripts/linux-mac/uninstall-path.sh
./scripts/linux-mac/uninstall-path.sh
source ~/.bashrc  # 或 ~/.zshrc
```

卸载脚本会自动备份配置文件（Linux/Mac），并提示重新打开终端使更改生效。

## 使用说明

### 快速开始

```bash
# 查看帮助
dahua-cloud --help

# 查看版本
dahua-cloud --version

# 初始化配置（交互式）
dahua-cloud init

# 诊断环境配置
dahua-cloud doctor

# 图片分析（单图）- 位置参数方式（简洁）
dahua-cloud image analysis "https://xxx.jpg" "描述图片内容"

# 文本分析
dahua-cloud text analysis "待分析文本" "提取关键信息"

# 视频分析
dahua-cloud video analysis "https://xxx.mp4" "分析视频内容"

# 语音转文字
dahua-cloud audio transcribe "https://xxx.mp3"
```

> **PowerShell 用户注意**：如果 URL 包含 `&` 符号，请使用 `--%` 停止解析操作符：
> ```powershell
> dahua-cloud --% image analysis "https://xxx?a=1&b=2" "描述"
> ```

### 未安装到 PATH 时的调用方式

```bash
# 进入 dahua-cloud-ai-cli 目录
cd dahua-cloud-ai-cli

# 直接调用 Python 脚本
python src/dahua-cloud-ai-cli.py image analysis "URL" "描述"

# Windows CMD 入口脚本
scripts\windows\dahua-cloud.cmd image analysis "URL" "描述"

# Windows PowerShell 入口脚本
.\scripts\windows\dahua-cloud-ai-cli.ps1 image analysis "URL" "描述"

# Linux/Mac 入口脚本
./scripts/linux-mac/dahua-cloud.sh image analysis "URL" "描述"
```

## 在 AI IDE 中使用

AI IDE 可通过调用 `dahua-cloud` 命令来使用大华云 AI 能力。

### 方式 1：通过 config.json 配置

在项目 `config.json` 中添加 CLI 工具配置：

```json
{
  "cli_tools": {
    "dahua-cloud-ai-cli": {
      "path": "/path/to/dahua-cloud-ai-cli",
      "entry": "src/dahua-cloud-ai-cli.py",
      "scripts": {
        "windows": "scripts/windows/dahua-cloud.cmd",
        "powershell": "scripts/windows/dahua-cloud-ai-cli.ps1",
        "linux": "scripts/linux-mac/dahua-cloud.sh",
        "mac": "scripts/linux-mac/dahua-cloud.sh"
      },
      "description": "大华云大模型推理套件 CLI，支持图片、文本、视频、音频等多种 AI 能力"
    }
  }
}
```

配置字段说明：
- `path`: CLI 工具根目录路径（使用实际绝对路径）
- `entry`: 主程序入口，相对于 `path` 的路径
- `scripts`: 各平台的入口脚本路径
- `description`: 工具描述，用于 AI IDE 理解工具用途

说明：配置`config.json`后，需要显示告知AI IDE进行加载。

### 方式 2：添加到 PATH

将 CLI 安装到 PATH 后，在 AI IDE 中直接要求以命令行方式调用即可。参考上方[安装到 PATH](#2-安装到-path推荐日常使用)章节。

### 使用示例

配置完成后，在 AI IDE 中可以直接使用：

```
请使用 dahua-cloud 分析这张图片：https://example.com/image.jpg
```

## 命令参考

### 参数传递方式

CLI 支持两种参数传递方式：

#### 方式 1：位置参数（推荐，简洁）

对于参数较少的命令，可以直接按顺序传入参数，无需指定参数名：

```bash
# 图片分析：第一个参数是 URL，第二个参数是提示词
dahua-cloud image analysis "https://xxx.jpg" "描述图片内容"

# 文本分析：第一个参数是文本，第二个参数是提示词
dahua-cloud text analysis "待分析文本" "提取关键信息"

# 语音转文字：第一个参数是音频 URL
dahua-cloud audio transcribe "https://xxx.mp3"
```

#### 方式 2：选项参数（传统）

使用 `--参数名` 或 `-简写` 的方式指定参数：

```bash
dahua-cloud image analysis --picture-url "https://xxx.jpg" --prompt "描述图片内容"
dahua-cloud image analysis -u "https://xxx.jpg" -p "描述图片内容"
```

#### 混合使用

两种方式可以混合使用，选项参数优先级高于位置参数：

```bash
# 第一个参数使用位置参数，第二个使用选项参数
dahua-cloud text analysis "待分析文本" -p "提取关键信息"
```

### 全局标志

| 标志 | 简写 | 说明 |
|------|------|------|
| `--help` | `-h` | 显示帮助信息 |
| `--version` | `-v` | 显示版本信息 |
| `--json` | | 以 JSON 格式输出 |
| `--no-json` | | 以人类可读格式输出（默认） |
| `--output` | `-o` | 输出到文件 |

### 支持的命令

| 类别 | 命令 | 功能 | 支持位置参数 |
|------|------|------|-------------|
| 图片理解 | `dahua-cloud image analysis` | 单图分析 | ✅ URL, 提示词 |
| | `dahua-cloud image multi-analysis` | 多图分析 | ❌ 多 URL + 提示词（需用选项参数） |
| | `dahua-cloud image summary` | 图片摘要 | ✅ URL, 关键词 |
| | `dahua-cloud image compare` | 基图比对（1张基准图 vs N张对比图） | ❌ 基准图 + 多对比图 + 提示词（需用选项参数） |
| 文本理解 | `dahua-cloud text analysis` | 文本分析 | ✅ 文本, 提示词 |
| | `dahua-cloud text tts` | 文字转语音 | ✅ 文本 |
| 视频理解 | `dahua-cloud video analysis` | 视频分析 | ✅ URL, 提示词 |
| 音频理解 | `dahua-cloud audio transcribe` | 语音转文字 | ✅ URL |
| 配置 | `dahua-cloud init` | 初始化配置环境变量 | - |
| 诊断 | `dahua-cloud doctor` | 环境配置诊断 | - |

### 初始化配置

使用 `dahua-cloud init` 命令进行交互式配置：

```bash
# 交互式配置环境变量
dahua-cloud init
```

执行后会提示输入以下信息：
- `DAHUA_CLOUD_PRODUCT_ID`: 产品 ID（从大华云开发者平台获取）
- `DAHUA_CLOUD_AK`: Access Key
- `DAHUA_CLOUD_SK`: Secret Key

配置会**永久保存**到系统环境变量：
- **Windows**: 写入用户环境变量（通过 PowerShell）
- **Linux/Mac**: 写入 `~/.bashrc` 或 `~/.zshrc`

配置完成后，需要重新打开终端或运行 `source ~/.bashrc`（Linux/Mac）使配置生效。

### 环境诊断

使用 `dahua-cloud doctor` 命令检查环境配置：

```bash
# 检查环境变量配置和 API 凭据有效性
dahua-cloud doctor
```

诊断内容包括：
- 环境变量 `DAHUA_CLOUD_PRODUCT_ID` 是否已配置
- 环境变量 `DAHUA_CLOUD_AK` 是否已配置
- 环境变量 `DAHUA_CLOUD_SK` 是否已配置
- 网络连接是否正常
- API 凭据是否有效（通过调用大华云 API 验证）

如果环境变量未配置或凭据无效，会显示详细的配置指南和故障排除建议。

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 130 | 用户中断 (Ctrl+C) |

## 版本历史

- v1.0.0 (2026-04-16): 初始版本，支持 8 个同步接口
