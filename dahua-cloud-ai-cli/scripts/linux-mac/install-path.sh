#!/bin/sh
# Linux/Mac PATH 安装脚本 (POSIX sh 兼容)

# 获取脚本所在目录（兼容 POSIX sh）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLI_DIR="$SCRIPT_DIR"
SHELL_NAME=$(basename "$SHELL")

echo "[INFO] 准备将以下目录添加到 PATH:"
echo "$CLI_DIR"
echo ""

# 检测当前 shell 配置文件（使用 POSIX 兼容的单括号 [ ）
if [ "$SHELL_NAME" = "zsh" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    # 检测 macOS
    if [ "$(uname -s)" = "Darwin" ]; then
        CONFIG_FILE="$HOME/.bash_profile"
    else
        CONFIG_FILE="$HOME/.bashrc"
    fi
else
    CONFIG_FILE="$HOME/.profile"
fi

# 检查是否已安装在当前路径（遍历可能的配置文件）
for CFG in "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$CFG" ] && grep -qF "$CLI_DIR" "$CFG" 2>/dev/null; then
        echo "[INFO] dahua-cloud CLI 已安装在此路径，无需重新安装:"
        echo "  $CLI_DIR"
        echo ""
        echo "请运行以下命令使配置生效:"
        echo "  source $CFG"
        echo ""
        echo "或者重新打开终端"
        exit 0
    fi
done

# 检查是否已安装在其他路径
if grep -q "dahua-cloud" "$CONFIG_FILE" 2>/dev/null; then
    echo "[WARNING] 检测到 dahua-cloud CLI 已安装在其他路径"
    echo ""
    printf "是否覆盖安装? (y/N): "
    read -r OVERWRITE
    # POSIX 兼容的字符串匹配（不支持正则，用 case 替代）
    case "$OVERWRITE" in
        [Yy]|[Yy][Ee][Ss]) ;;  # 匹配 Y/y/Yes/yes，继续执行
        *)
            echo "[INFO] 已取消安装"
            exit 0
            ;;
    esac
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
