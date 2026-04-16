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

# 检查是否已安装在当前路径
if grep -qF "$CLI_DIR" "$CONFIG_FILE" 2>/dev/null; then
    echo "[INFO] dahua-cloud CLI 已安装在此路径，无需重新安装:"
    echo "  $CLI_DIR"
    exit 0
fi

# 检查是否已安装在其他路径
if grep -q "dahua-cloud" "$CONFIG_FILE" 2>/dev/null; then
    echo "[WARNING] 检测到 dahua-cloud CLI 已安装在其他路径"
    echo ""
    read -p "是否覆盖安装? (y/N): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "[INFO] 已取消安装"
        exit 0
    fi
    echo "[INFO] 正在移除旧条目..."
    # 从配置文件中移除旧条目（包括注释行和 export 行）
    TEMP_FILE=$(mktemp)
    awk '
        /# dahua-cloud CLI/ { skip=1; next }
        skip && /export PATH=.*dahua-cloud/ { skip=0; next }
        { skip=0; print }
    ' "$CONFIG_FILE" > "$TEMP_FILE"
    cp "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"
    mv "$TEMP_FILE" "$CONFIG_FILE"
    echo "[INFO] 继续安装..."
    echo ""
fi

# 添加到配置文件
echo "" >> "$CONFIG_FILE"
echo "# dahua-cloud CLI" >> "$CONFIG_FILE"
echo "export PATH=\"\$PATH:$CLI_DIR\"" >> "$CONFIG_FILE"
echo "[SUCCESS] 已成功添加到 $CONFIG_FILE"

echo ""
echo "请运行以下命令使配置生效:"
echo "  source $CONFIG_FILE"
echo ""
echo "然后可以直接使用:"
echo "  dahua-cloud image analysis --picture-url \"URL\" --prompt \"描述\""
