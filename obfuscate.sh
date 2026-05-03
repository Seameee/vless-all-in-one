#!/bin/bash
# obfuscate.sh - 上游脚本混淆脚本
# 用法: ./obfuscate.sh <上游脚本> <输出脚本>
set -e

INPUT="$1"
OUTPUT="$2"
TMP=$(mktemp)

# 应用混淆替换（精确全词匹配，避免部分替换）
sed -E \
    -e 's|/etc/vless-reality|/etc/netc-core|g' \
    -e 's|/var/log/vless-server\.log|/var/log/netc-agent.log|g' \
    -e 's|/var/log/xray/|/var/log/netx/|g' \
    -e 's|\bxray\b|netx|g' \
    -e 's|\bsing-box\b|sbox|g' \
    -e 's|\bvless-reality\b|netc-x|g' \
    -e 's|\bvless-singbox\b|netc-s|g' \
    -e 's|\bvless-snell\b|netc-n|g' \
    -e 's|\bvless-anytls\b|netc-a|g' \
    -e 's|\bvless-naive\b|netc-naive|g' \
    -e 's|\bshadow-tls\b|stls|g' \
    -e 's|\bcheck-expire\b|ncx|g' \
    -e 's|\bsync-traffic\b|ncs|g' \
    "$INPUT" > "$TMP"

# 功能完整性验证
for func in generate_xray_config generate_singbox_config install_xray install_singbox; do
    grep -q "$func" "$TMP" || { echo "ERROR: $func missing"; exit 1; }
done

mv "$TMP" "$OUTPUT"
chmod +x "$OUTPUT"
echo "Obfuscated: $INPUT -> $OUTPUT"

# 应用 SpeedTest 伪装网页补丁和仓库地址替换
if command -v python3 >/dev/null 2>&1; then
    echo "Applying fake website patch..."
    python3 "$(dirname "$0")/patch-fake-website.py" "$OUTPUT"
else
    echo "WARNING: python3 not found, skipping fake website patch"
fi
