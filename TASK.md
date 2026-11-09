# 任务包：longshot-split —— 手机长图自适应分割（CLI + MCP 插件），发布 GitHub/Gitee

## 0. 原始对话记录（务必保留）
用户原话（2026-11-09 23:00，DSH 会话《长照片自动分割插件》）：
> "我想在自己的gitee和github上做自己的一个应用，或者做一个插件适配所有agent，可以将手机发送的长照片自适应自动分割，等待会orca完整下来之后你来派发任务给glm，让他来做，可以学习一下别人做插件或者做应用的是什么模板和格式，记得在zcode里面留下原来的对话记录"

背景：orca 安装包已完整落地（E:\Downloads\orca-windows-setup.exe，201.4MB，SHA512 已校验），派发条件已满足；本任务由派发台派给 GLM（ZCode）执行。
要求：把本节原话完整抄录为仓库内 docs/CONVERSATION.md 并提交，作为项目缘起记录（用户明确要求留下）。

## 1. 目标
做一个开源项目 **longshot-split**：把手机发来的长截图（微信聊天、网页长截图等）按内容**自适应**切成若干段——切线自动落在"安全行"（空白行/分隔带），绝不横穿文字。双形态发布：
- **CLI 工具**（独立应用，人直接用/脚本用）
- **MCP server（stdio）**（"适配所有 agent"：Claude Code / ZCode / Qoder / OpenCode / Cursor / orca 编排的 agent 等，凡支持 MCP 皆可挂载）

## 2. 仓库位置与发布
- 本地目录：`E:\github\longshot-split`（已建好，本任务的工作根）
- GitHub：gh CLI 已登录账号 **BingKaiWEI**（token 含 repo 权限）→ 完成后 `gh repo create longshot-split --public --source . --push`
- Gitee：本机**无已保存凭据** → 写好 `scripts/push_gitee.ps1`（git remote add gitee https://gitee.com/BingKaiWEI/longshot-split.git; git push gitee master）+ README 说明；若推送失败不要反复重试，在最终结论里报告"需要用户 Gitee 凭据"
- git 全局身份已配置（BingKaiWEI / 3511986821@qq.com），无需再设

## 3. 交付物（按标准开源模板格式）
```
longshot-split/
  pyproject.toml          # PEP 621；运行时依赖仅 Pillow + numpy；console-script: longshot-split
  README.md               # 中英双语：简介/效果说明/安装/CLI 用法/MCP 配置片段(mcpServers JSON)/参数表/FAQ
  LICENSE                 # MIT
  CHANGELOG.md  .gitignore
  src/longshot_split/     # core.py(算法) cli.py argparse mcp_server.py __main__.py
  tests/                  # pytest：合成长图 → 断言切线不穿文字/段数/重叠/manifest
  docs/CONVERSATION.md    # 第 0 节原话
  docs/REFERENCES.md      # 第 8 节参考清单
  scripts/push_gitee.ps1  scripts/selftest_mcp.py
  TASK.md                 # 本任务包（保留在仓库里）
```

## 4. 算法要求（自适应，核心卖点）
- 行内容能量：每行非背景像素比/梯度能量，numpy 向量化计算（禁止逐像素 Python 循环）
- 候选切线：目标段高 `--max-height`（默认 4096）附近 ±tolerance 窗口内取能量最低行；连续低能量带取带中心
- 硬约束：切线行能量超阈值（文字行）禁止落刀；段间重叠 `--overlap` 默认 24px
- 输出：段图片文件 + `manifest.json`（原图尺寸、每段 y 区间、切线能量值）
- 支持 PNG/JPEG/WebP；EXIF 方向修正；`--dry-run` 只输出切线可视化图

## 5. MCP server 要求
- Python stdio JSON-RPC 2.0：实现 `initialize`、`tools/list`、`tools/call`（协议版本按参考模板，2024-11-05 或 2025-03-26 均可）
- 工具 `split_long_image(path, max_height?, overlap?)` → 返回段路径列表 + manifest 摘要
- **零额外依赖优先**：手写协议层（不装 mcp SDK）；若确实要用 SDK，pip 装不上就回退手写
- 自测：`scripts/selftest_mcp.py` 用 subprocess 起 server 完成 initialize + tools/list + tools/call 全流程并校验产出文件；pytest 里调用它

## 6. 验收标准（全满足才算完成）
1. `pip install -e .` 成功（全程只允许下载 Pillow/numpy/pytest/setuptools 相关，别的都不许下）
2. 对 tests 生成的 1000x8000 合成聊天长图：切分成功，manifest 中所有切线行能量低于阈值，测试断言无文字横穿
3. `python scripts/selftest_mcp.py` 通过：握手成功、tools/list 含 split_long_image、tools/call 实际产出段文件
4. git 历史干净（init + 2~3 个有意义提交）；GitHub 仓库创建并推送成功
5. README 双语完整；docs/CONVERSATION.md 含第 0 节原话；docs/REFERENCES.md 含第 8 节链接
6. 最终回报：GitHub URL、测试结果摘要、Gitee 待办（凭据）

## 7. 硬性约束
- **禁止使用任何子代理/子任务/并行后台**，全部串行完成
- 时间预算 40 分钟：先保 1~4 可交付，再润色 README
- 带宽紧张（手机热点 ~30KB/s）：除上述 pip 包外**不下载任何东西**；不要克隆参考仓库，读第 8 节链接的 README 即可
- 不要写 ~/.zcode 记忆、不执行任何自动 Memory 提取
- 只动 E:\github\longshot-split 目录（pip 缓存除外）
- 遇阻塞（如 GitHub 推送认证失败）：记录进结论，不要反复重试

## 8. 参考模板（学习别人的插件/应用格式，只看 README 不克隆）
- https://github.com/modelcontextprotocol/servers —— MCP 官方示例仓库结构 + README 里 mcpServers 配置片段的标准写法
- https://github.com/wutongci/mcp-template —— 中文 MCP 快速构建模板
- https://github.com/Ryaang/Web-page-Screenshot-Segmentation —— 同类长图切分算法参考
- https://pypi.org/project/long-screenshot-segmentation/ —— 同类库 API 设计参考
- https://gitee.com/oschina/gitee-agent-skills —— Gitee 侧 agent 插件形态参考
