#!/bin/bash
# verify-obfuscation.sh - 验证混淆完整性
# 用法: ./verify-obfuscation.sh <脚本文件>

SCRIPT="${1:-vless-server.sh}"
ERRORS=0

echo "=== 验证混淆完整性: $SCRIPT ==="

# 检查路径暴露
if grep -n -E '/etc/vless|/var/log/vless|/usr/local/bin/xray|/usr/local/bin/sing-box' "$SCRIPT" | grep -v '^.*:#'; then
    echo "FAIL: 路径暴露"
    ((ERRORS++))
fi

# 检查混淆后的路径是否已替换（反向验证）
if grep -n -E '/var/log/netc-agent\.log|/var/log/netc-watchdog\.log|/var/log/netc/|/var/log/netx/' "$SCRIPT" | grep -v '^.*:#' | head -3; then
    echo "  OK: 日志路径已混淆"
fi

# 检查进程名暴露（原始进程名）
# 使用 \b 边界匹配，避免误报已混淆的 _pgrep netx（其中包含 xray 子串）
if grep -n -E 'pgrep[[:space:]]+xray\b|pgrep[[:space:]]+sing-box\b|pgrep[[:space:]]+vless\b|pgrep[[:space:]]+trojan\b' "$SCRIPT" | grep -v '^.*:#'; then
    echo "FAIL: 进程名暴露"
    ((ERRORS++))
fi

# 检查混淆后的进程名是否存在（反向验证）
if grep -n -E '_pgrep netx|_pgrep sbox|_pgrep nproxy|_pgrep hys' "$SCRIPT" | grep -v '^.*:#' | head -3; then
    echo "  OK: 进程检测已混淆"
fi

# 检查服务名暴露
if grep -n -E 'vless-reality\.service|vless-singbox\.service|vless-snell\.service' "$SCRIPT" | grep -v '^.*:#'; then
    echo "FAIL: 服务名暴露"
    ((ERRORS++))
fi

# 检查服务名字符串
if grep -n -E '"vless-reality"|"vless-singbox"|"vless-snell"' "$SCRIPT" | grep -v '^.*:#'; then
    echo "FAIL: 服务名字符串暴露"
    ((ERRORS++))
fi

# 功能完整性检查
for func in generate_xray_config generate_singbox_config install_xray install_singbox rebuild_and_reload; do
    if ! grep -q "$func" "$SCRIPT"; then
        echo "FAIL: 核心函数 $func 丢失"
        ((ERRORS++))
    fi
done

if [[ $ERRORS -eq 0 ]]; then
    echo "PASS: 所有验证通过"
    exit 0
else
    echo "FAIL: 发现 $ERRORS 个错误"
    exit 1
fi
