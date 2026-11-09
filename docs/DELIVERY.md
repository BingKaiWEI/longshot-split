# 交付报告 / Delivery Report

任务包：TASK.md（手机长图自适应分割 CLI + MCP 插件）
执行：GLM (ZCode)，2026-11-09，串行执行、无子代理、无记忆写入。

## 交付清单

| 交付物 | 路径 | 状态 |
|---|---|---|
| pyproject.toml (PEP 621, console-script: longshot-split) | `pyproject.toml` | ✅ |
| README 中英双语（简介/算法/安装/CLI/MCP mcpServers 片段/参数表/FAQ） | `README.md` | ✅ |
| LICENSE (MIT) | `LICENSE` | ✅ |
| CHANGELOG / .gitignore | `CHANGELOG.md` `.gitignore` | ✅ |
| core.py（行能量 numpy 向量化 / 自适应切线 / manifest / dry-run / EXIF） | `src/longshot_split/core.py` | ✅ |
| cli.py（argparse） | `src/longshot_split/cli.py` | ✅ |
| mcp_server.py（手写 stdio JSON-RPC 2.0，零额外依赖，protocol 2024-11-05） | `src/longshot_split/mcp_server.py` | ✅ |
| __main__.py | `src/longshot_split/__main__.py` | ✅ |
| pytest（合成 1000x8000 聊天长图 → 切线不穿文字/段数/重叠/manifest） | `tests/` | ✅ 10 passed |
| docs/CONVERSATION.md（第 0 节原话完整抄录） | `docs/CONVERSATION.md` | ✅ |
| docs/REFERENCES.md（第 8 节链接） | `docs/REFERENCES.md` | ✅ |
| scripts/selftest_mcp.py（subprocess 握手 + tools/list + tools/call 全流程） | `scripts/selftest_mcp.py` | ✅ SELFTEST PASS |
| scripts/push_gitee.ps1 | `scripts/push_gitee.ps1` | ✅（待用户 Gitee 凭据） |
| TASK.md 保留在仓库 | `TASK.md` | ✅ |

## 可复跑命令 / 原始输出

```bash
python -m pip install -e .
python -m pytest tests/ -v
python scripts/selftest_mcp.py
longshot-split <长图>.png -o out/          # CLI
longshot-split <长图>.png --dry-run        # 只看切线可视化
```

原始输出（执行当次记录）：

```
$ python -m pytest tests/
============================= 10 passed in 7.22s ==============================

$ python scripts/selftest_mcp.py
[ok] initialize: protocol=2024-11-05 server=longshot-split v0.1.0
[ok] tools/list: ['split_long_image']
[ok] tools/call: 2 segments written, manifest at ...\chat_parts\manifest.json
SELFTEST PASS

$ longshot-split demo.png -o out/demo_parts   # 合成 1000x8000
split into 2 segment(s)
  [     0,   4120) demo_part01.png
  [  4072,   8000) demo_part02.png
manifest: out/demo_parts/manifest.json
```

验收对照：① `pip install -e .` 成功（仅 Pillow/numpy/pytest/setuptools）✅ ② 1000x8000 合成图切分、切线能量低于阈值、断言无文字横穿 ✅ ③ selftest 握手/tools/call 产出段文件 ✅ ④ git 历史干净、GitHub 已推送 ✅ ⑤ README 双语 / CONVERSATION / REFERENCES ✅

## 发布

- GitHub: https://github.com/BingKaiWEI/longshot-split （`gh repo create longshot-split --public --source . --push`）
- Gitee: **待用户凭据**。创建 https://gitee.com/BingKaiWEI/longshot-split 后运行
  `powershell -ExecutionPolicy Bypass -File scripts/push_gitee.ps1`

## 未决问题

1. Gitee 推送需要用户凭据（本机无已保存凭据），由用户执行 push_gitee.ps1。
2. `--threshold` 默认 0.02 针对干净截图调优； JPEG 压缩噪声大的图可适当调大。
3. 未做 PyPI 发布（任务包未要求）。
