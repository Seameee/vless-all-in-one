#!/usr/bin/env python3
"""
patch-fake-website.py - 在混淆后的脚本中替换伪装网页为 SpeedTest 主题
用法: python3 patch-fake-website.py <目标脚本>
"""

import re
import sys

# _install_speedtest_html 函数定义（插入到 _pgrep() 之后）
INSTALL_FUNC = '''# 安装 SpeedTest 伪装网页
_install_speedtest_html() {
    local target="${1:-/var/www/html/index.html}"
    local target_dir=$(dirname "$target")
    mkdir -p "$target_dir"

    # 优先从脚本同级目录的 release-assets 复制
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$script_dir/release-assets/speedtest.html" ]]; then
        cp "$script_dir/release-assets/speedtest.html" "$target"
        return 0
    fi

    # 其次尝试从 GitHub raw 下载
    local raw_url="https://raw.githubusercontent.com/${SCRIPT_REPO}/main/release-assets/speedtest.html"
    if command -v curl >/dev/null 2>&1; then
        if curl -fsSL --connect-timeout 10 "$raw_url" -o "$target" 2>/dev/null; then
            return 0
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -qO "$target" "$raw_url" 2>/dev/null; then
            return 0
        fi
    fi

    # 回退：写入极简欢迎页
    cat > "$target" << \'HTMLEOF\'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpeedTest - Network Performance</title>
</head>
<body>
    <h1>SpeedTest</h1>
    <p>Network performance testing service.</p>
</body>
</html>
HTMLEOF
}

'''

def patch_fake_website(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # -------------------------------------------------------------------------
    # 1. 在 _pgrep() 函数后插入 _install_speedtest_html()
    # -------------------------------------------------------------------------
    pgrep_pattern = (
        r'(# Alpine busybox pgrep .*?检测进程\n)'
        r'(_pgrep\(\) \{.*?^\}\n)'
    )
    content = re.sub(pgrep_pattern, r'\1\2\n' + INSTALL_FUNC, content,
                     flags=re.DOTALL | re.MULTILINE)

    # -------------------------------------------------------------------------
    # 2. 替换 naiveproxy (Caddy) 模式中的默认欢迎页
    # -------------------------------------------------------------------------
    content = content.replace(
        'echo "<html><body><h1>Welcome</h1></body></html>" > /var/www/html/index.html',
        '_install_speedtest_html /var/www/html/index.html'
    )

    # -------------------------------------------------------------------------
    # 3. 替换 create_fake_website() 中的内嵌 HTML heredoc
    # -------------------------------------------------------------------------
    fake_pattern = (
        r'    # 创建简单的伪装网页\n'
        r'    cat > "\$web_dir/index\.html" << \'EOF\'\n'
        r'<!DOCTYPE html>.*?</html>\n'
        r'EOF'
    )
    content = re.sub(
        fake_pattern,
        '    # 创建 SpeedTest 伪装网页\n    _install_speedtest_html "$web_dir/index.html"',
        content,
        flags=re.DOTALL
    )

    # -------------------------------------------------------------------------
    # 4. 替换订阅服务中的内嵌 HTML heredoc
    # -------------------------------------------------------------------------
    sub_pattern = (
        r'    # 确保伪装网页存在\n'
        r'    mkdir -p /var/www/html\n'
        r'    if \[\[ ! -f "/var/www/html/index\.html" \]\]; then\n'
        r'        cat > /var/www/html/index\.html << \'HTMLEOF\'\n'
        r'<!DOCTYPE html>.*?</html>\n'
        r'HTMLEOF\n'
        r'    fi'
    )
    content = re.sub(
        sub_pattern,
        '''    # 确保伪装网页存在
    mkdir -p /var/www/html
    if [[ ! -f "/var/www/html/index.html" ]]; then
        _install_speedtest_html /var/www/html/index.html
    fi''',
        content,
        flags=re.DOTALL
    )

    if content == original:
        print("WARNING: 未做任何替换，请检查脚本内容")
        return False

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Done: patched fake website to SpeedTest theme")
    return True


def patch_repo_urls(script_path):
    """将上游仓库地址替换为 fork 地址"""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 替换仓库地址
    content = content.replace(
        'readonly REPO_URL="https://github.com/Zyx0rx/vless-all-in-one"',
        'readonly REPO_URL="https://github.com/Seameee/vless-all-in-one"'
    )
    content = content.replace(
        'readonly SCRIPT_REPO="Zyx0rx/vless-all-in-one"',
        'readonly SCRIPT_REPO="Seameee/vless-all-in-one"'
    )
    content = content.replace(
        'readonly SCRIPT_RAW_URL="https://raw.githubusercontent.com/Zyx0rx/vless-all-in-one/main/vless-server.sh"',
        'readonly SCRIPT_RAW_URL="https://raw.githubusercontent.com/Seameee/vless-all-in-one/main/vless-server.sh"'
    )

    if content != original:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Done: patched repository URLs to fork")
        return True
    return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 patch-fake-website.py <script_path>")
        sys.exit(1)

    script = sys.argv[1]
    patch_fake_website(script)
    patch_repo_urls(script)
