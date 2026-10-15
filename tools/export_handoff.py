"""导出带精确Git版本与远端核对结果的Kimi交接快照，不保存凭证。"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True,
                          encoding='utf-8').stdout.strip()


def main():
    branch = git('branch', '--show-current')
    commit = git('rev-parse', 'HEAD')
    if not branch:
        raise RuntimeError('请在交付分支导出交接文档')
    # 允许用户本来就有的未跟踪手册；已跟踪内容必须与提交一致。
    git('diff', '--exit-code', 'HEAD', '--')
    remote = git('ls-remote', 'origin', 'refs/heads/' + branch).split()
    if not remote or remote[0] != commit:
        raise RuntimeError('GitHub分支尚未与本地提交一致，请先完成push')
    when = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    source = (ROOT / 'docs/KIMICODE_HANDOFF.md').read_text(encoding='utf-8')
    status = f'''<!-- release-status:start -->
| 项目 | 最终交付状态 |
| --- | --- |
| 产品版本 | V1.1（荧光黄主色、双链结构图与公司表内行情修订） |
| Git branch | `{branch}`，未合并main |
| 最终commit SHA | `{commit}` |
| GitHub是否已push | 已push，导出时已核对origin分支SHA与本地HEAD一致 |
| 核对时间 | {when}（北京时间） |
| GitHub提交 | https://github.com/Verlaski/semi-industry-web/commit/{commit} |
| CloudBase在线URL | https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html |
| 数据更新时间 | 2026-10-15；meta.version仍为v1.0 |
<!-- release-status:end -->'''
    content, count = re.subn(r'<!-- release-status:start -->.*?<!-- release-status:end -->',
                             lambda _: status, source, flags=re.S)
    if count != 1:
        raise RuntimeError('交接文档发布状态标记缺失或重复')
    start = content.index('本文件维护交接内容。')
    end = content.index('\n\n', start)
    content = content[:start] + '本文件为最终交接快照，已核对GitHub推送状态。后续维护以仓库docs/KIMICODE_HANDOFF.md及核心文档为准；快照用于本次交付留档。' + content[end:]
    output = ROOT / 'output/handoff/KimiCode_V1.1_交接.md'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content + '\n', encoding='utf-8')
    print(str(output))
    print('Final commit:', commit)


if __name__ == '__main__':
    main()
