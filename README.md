# Dahua Cloud Open CLI

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

本仓库是基于[大华云开发者平台](https://open.cloud-dahua.com/) API 封装的命令行工具（CLI）集合。旨在提供便捷、高效的命令行交互方式，帮助开发者、运维人员快速将大华云平台能力集成到自动化脚本、运维 pipelines 或智能安防系统中。

## 📂 已收录 CLI 工具

| CLI 目录 | 描述 | 核心能力标签 |
| :--- | :--- | :--- |
| **[dahua-cloud-ai-cli](./dahua-cloud-ai-cli)** | 大华云多模态 AI 命令行工具 | `图片理解` `文本理解` `视频理解` `音频理解` |

### dahua-cloud-ai-cli - 多模态 AI 命令行工具

一个命令行工具即可调用大华云平台的四大 AI 能力：

| 能力类别 | 支持功能 | 典型场景 |
| :--- | :--- | :--- |
| **图片理解** | 单图分析、多图分析、图片摘要、基图比对 | 餐饮连锁巡检、智慧工地安全生产、居家异常看护 |
| **文本理解** | 文本分析、文字转语音 | 安防事件报告自动生成、语音播报警情 |
| **视频理解** | 视频分析 | 异常行为识别（摔倒/打架/聚集）、操作合规检测、长时段监控摘要 |
| **音频理解** | 语音转文字 | 对讲通话记录转写、应急指挥语音指令识别、告警音频关键词提取 |

## 🚀 快速开始

每个子目录均包含独立的 `README.md` 和使用说明，请进入具体 CLI 文件夹查看详细配置。

**通用步骤：**

```bash
# 克隆仓库
git clone https://github.com/DoLynkDeveloper/DahuaCloudOpenCLI.git

# 进入具体 CLI 目录
cd DahuaCloudOpenCLI/dahua-cloud-ai-cli

# 安装依赖
pip install -r requirements.txt

# 配置密钥（大华云 Product ID、AppKey、AppSecret）
# 查看使用帮助
dahua-cloud --help
```

## 📅 更新计划

本仓库将持续增加更多大华云平台的 CLI 工具：

- [ ] 设备管理 CLI（设备增删改查、状态监控、远程配置）
- [ ] 云台控制 CLI（方向控制、变焦、预置位设置）
- [ ] 录像回放 CLI（录像检索、回放、下载）
- [ ] 实时流 CLI（获取 RTMP/FLV 播放地址）
- [ ] 更多 API 的便捷命令封装

欢迎 **Watch** 本仓库获取最新动态。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来建议新的 CLI 工具或改进现有功能。

## 📄 License

本项目基于 MIT License 开源。

---

*本仓库中的 CLI 工具均需配合[大华云开发者平台](https://open.cloud-dahua.com/)账号使用。*
