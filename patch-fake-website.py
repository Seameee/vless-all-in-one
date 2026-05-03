#!/usr/bin/env python3
"""
patch-fake-website.py - 在混淆后的脚本中替换伪装网页为 SpeedTest 主题
用法: python3 patch-fake-website.py <目标脚本>
"""

import re
import sys

# _install_speedtest_html 函数定义（插入到 _pgrep() 之后）
INSTALL_FUNC = """# 安装 SpeedTest 伪装网页
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
    cat > "$target" << 'HTMLEOF'
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

"""


def inject_install_func(content):
    """在 _pgrep() 函数后插入 _install_speedtest_html()"""
    pgrep_pattern = (
        r'(# Alpine busybox pgrep .*?检测进程\n)'
        r'(_pgrep\(\) \{.*?^\}\n)'
    )
    new_content = re.sub(pgrep_pattern, r'\1\2\n' + INSTALL_FUNC, content,
                         flags=re.DOTALL | re.MULTILINE)
    if new_content == content:
        print("WARNING: 未能注入 _install_speedtest_html() 函数")
    else:
        print("  OK: _install_speedtest_html() 函数已注入")
    return new_content


def replace_heredoc_blocks(lines):
    """逐行扫描，替换 heredoc 块为函数调用"""
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Pattern 1: naiveproxy (Caddy) 模式的简单 echo
        if 'echo "<html><body><h1>Welcome</h1></body></html>" > /var/www/html/index.html' in line:
            indent = line[:len(line) - len(line.lstrip())]
            result.append(indent + '_install_speedtest_html /var/www/html/index.html')
            i += 1
            continue

        # Pattern 2: create_fake_website() 中的 heredoc
        if stripped == "# 创建简单的伪装网页":
            indent = line[:len(line) - len(line.lstrip())]
            result.append(indent + "# 创建 SpeedTest 伪装网页")
            result.append(indent + '_install_speedtest_html "$web_dir/index.html"')
            # 跳过 heredoc 内容，直到 EOF
            i += 1
            while i < len(lines):
                if lines[i].strip() == 'EOF':
                    i += 1
                    break
                i += 1
            continue

        # Pattern 3: 订阅服务中的 heredoc
        if stripped == "# 确保伪装网页存在":
            result.append(line)
            i += 1
            # 下一行应该是 mkdir -p /var/www/html
            if i < len(lines) and 'mkdir -p /var/www/html' in lines[i]:
                result.append(lines[i])
                i += 1
            # 下一行应该是 if [[ ! -f ...
            if i < len(lines) and 'if [[ ! -f "/var/www/html/index.html" ]]' in lines[i]:
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                result.append(lines[i])  # if 行
                i += 1
                # 跳过 heredoc，直到 HTMLEOF
                while i < len(lines):
                    if lines[i].strip() == 'HTMLEOF':
                        i += 1
                        break
                    i += 1
                # 插入函数调用
                result.append(indent + '    _install_speedtest_html /var/www/html/index.html')
                # 下一行应该是 fi
                if i < len(lines) and lines[i].strip() == 'fi':
                    result.append(lines[i])
                    i += 1
            continue

        result.append(line)
        i += 1

    return result


def patch_fake_website(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. 注入函数定义
    content = inject_install_func(content)

    # 2. 逐行替换 heredoc 块
    lines = content.split('\n')
    lines = replace_heredoc_blocks(lines)
    content = '\n'.join(lines)

    if content == original:
        print("WARNING: 未做任何替换")
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
