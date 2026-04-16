#!/usr/bin/env bash
# Linux/Mac PATH 安装脚本

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_NAME=$(basename "$SHELL")

echo "[INFO] 准备将以下目录添加到 PATH:"
echo "$CLI_DIR"
echo ""

# 检测当前 shell 配置文件
if [[ "$SHELL_NAME" == "zsh" ]]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [[ "$SHELL_NAME" == "bash" ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CONFIG_FILE="$HOME/.bash_profile"
    else
        CONFIG_FILE="$HOME/.bashrc"
    fi
else
    CONFIG_FILE="$HOME/.profile"
fi

# 检查是否已存在
if grep -q "$CLI_DIR" "$CONFIG_FILE" 2>/dev/null; then
    echo "[INFO] 目录已在 PATH 中，无需添加"
else
    # 添加到配置文件
    echo "" >> "$CONFIG_FILE"
    echo "# dahua-cloud CLI" >> "$CONFIG_FILE"
    echo "export PATH=\"\$PATH:$CLI_DIR\"" >> "$CONFIG_FILE"
    echo "[SUCCESS] 已成功添加到 $CONFIG_FILE"
fi

echo ""
echo "请运行以下命令使配置生效:"
echo "  source $CONFIG_FILE"
echo ""
echo "然后可以直接使用:"
echo "  dahua-cloud image analysis --picture-url \"URL\" --prompt \"描述\""
