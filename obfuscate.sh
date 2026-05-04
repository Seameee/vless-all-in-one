#!/bin/bash
# obfuscate.sh - 上游脚本混淆脚本
# 用法: ./obfuscate.sh <上游脚本> <输出脚本>
set -e

INPUT="$1"
OUTPUT="$2"

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Usage: $0 <input> <output>"
    exit 1
fi

TMP=$(mktemp)

# 应用混淆替换（精确全词匹配，避免部分替换）
sed -E \
    -e 's|/etc/vless-reality|/etc/netc-core|g' \
    -e 's|/var/log/vless-server\.log|/var/log/netc-agent.log|g' \
    -e 's|/var/log/vless-watchdog\.log|/var/log/netc-watchdog.log|g' \
    -e 's|/var/log/vless/|/var/log/netc/|g' \
    -e 's|/var/log/xray/|/var/log/netx/|g' \
    -e 's|\bxray\b|netx|g' \
    -e 's|\bsing-box\b|sbox|g' \
    -e 's|\bsingbox\b|sbox|g' \
    -e 's|\bvless-reality\b|netc-x|g' \
    -e 's|\bvless-singbox\b|netc-s|g' \
    -e 's|\bvless-snell\b|netc-n|g' \
    -e 's|\bvless-anytls\b|netc-a|g' \
    -e 's|\bvless-naive\b|netc-naive|g' \
    -e 's|\bshadow-tls\b|stls|g' \
    -e 's|\bcheck-expire\b|ncx|g' \
    -e 's|\bsync-traffic\b|ncs|g' \
    -e 's|_pgrep xray|_pgrep netx|g' \
    -e 's|_pgrep sing-box|_pgrep sbox|g' \
    -e 's|_pgrep singbox|_pgrep sbox|g' \
    -e 's|_pgrep naive|_pgrep nproxy|g' \
    -e 's|_pgrep hysteria|_pgrep hys|g' \
    -e 's|_pgrep tuic|_pgrep tuic|g' \
    -e 's|has_xray|has_netx|g' \
    -e 's|has_singbox|has_sbox|g' \
    -e 's|has_naive|has_nproxy|g' \
    -e 's|has_hysteria|has_hys|g' \
    -e 's|has_tuic|has_tuic|g' \
    "$INPUT" > "$TMP"

# 功能完整性验证
for func in generate_xray_config generate_singbox_config install_xray install_singbox; do
    grep -q "$func" "$TMP" || { echo "ERROR: $func missing"; exit 1; }
done

mv "$TMP" "$OUTPUT"
chmod +x "$OUTPUT"
echo "Obfuscated: $INPUT -> $OUTPUT"
