#!/usr/bin/env bash
# Linux/Mac PATH 卸载脚本
# 将 CLI 所在目录从 PATH 中移除

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_NAME=$(basename "$SHELL")

echo "[INFO] 准备从 PATH 中移除以下目录:"
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

# 检查配置文件是否存在
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[INFO] 配置文件 $CONFIG_FILE 不存在，无需移除"
    exit 0
fi

# 检查是否包含该目录
if ! grep -qF "$CLI_DIR" "$CONFIG_FILE" 2>/dev/null; then
    echo "[INFO] 目录不在 PATH 配置中，无需移除"
    exit 0
fi

# 从配置文件中移除该目录的 PATH 设置
# 使用临时文件进行安全编辑
TEMP_FILE=$(mktemp)

# 读取配置文件并过滤掉相关行（注释行 + 紧跟的 export 行）
awk -v dir="$CLI_DIR" '
    /# dahua-cloud CLI/ { skip=1; next }
    skip && $0 ~ "export PATH=.*" dir { skip=0; next }
    skip && /^$/ { skip=0; next }
    { skip=0; print }
' "$CONFIG_FILE" > "$TEMP_FILE"

# 检查是否有实际更改
if diff -q "$CONFIG_FILE" "$TEMP_FILE" > /dev/null 2>&1; then
    echo "[INFO] 未找到需要移除的配置"
    rm "$TEMP_FILE"
    exit 0
fi

# 备份原配置文件
cp "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"

# 应用更改
mv "$TEMP_FILE" "$CONFIG_FILE"

echo "[SUCCESS] 已成功从 $CONFIG_FILE 中移除"
echo ""
echo "原配置文件已备份"
echo ""
echo "请运行以下命令使更改生效:"
echo "  source $CONFIG_FILE"
echo ""
echo "或者重新打开终端"
