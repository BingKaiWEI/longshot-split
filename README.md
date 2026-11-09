# longshot-split

Adaptive splitter for long phone screenshots (WeChat chat logs, web long captures, ...).
Cuts fall only on **safe blank rows** — never across text. Ships as a **CLI** and a
zero-dependency **MCP server** (stdio) that any MCP-capable agent can mount
(Claude Code / ZCode / Cursor / OpenCode / ...).

长图（手机长截图）自适应分割工具：切线自动落在空白/低内容能量的“安全行”，绝不横穿文字。
提供 CLI 与 MCP server（stdio）两种形态，可挂载到任何支持 MCP 的 agent。

---

## How it works / 算法说明

1. **Row energy** 每行内容能量：numpy 向量化计算每行“非背景像素比”与“水平梯度能量”的较大者（0~1），无逐像素 Python 循环。
2. **Candidate cut lines** 候选切线：在目标段高 `--max-height`（默认 4096）±`--tolerance` 窗口内取能量最低的连续低能量带，取带中心作为切线。
3. **Hard constraints** 硬约束：能量超过 `--threshold`（即文字行）的行禁止落刀；找不到安全行时向下顺延搜索，直到找到空白带或图尾。
4. **Overlap** 段间重叠：每段默认向两端各扩 `--overlap`（默认 24px），保证上下文不丢。
5. **Output** 输出：段图片文件 + `manifest.json`（原图尺寸、每段 y 区间、切线能量值）；`--dry-run` 只输出切线可视化图（红线标出落刀位置）。

Supports PNG / JPEG / WebP, with EXIF orientation correction.

## Install / 安装

```bash
pip install -e .
# or from a clone:
git clone https://github.com/BingKaiWEI/longshot-split.git
cd longshot-split && pip install -e .
```

Runtime dependencies: Pillow + numpy only.

## CLI usage / 命令行用法

```bash
# split into out/ directory
longshot-split chat.png -o out/

# only preview where cuts will fall (writes cutlines.png)
longshot-split chat.png --dry-run

# custom params
longshot-split chat.png -o out/ --max-height 3000 --overlap 40
```

### Parameters / 参数表

| Parameter | Default | Meaning / 说明 |
|---|---|---|
| `image` (positional) | required | 输入图片路径 PNG/JPEG/WebP |
| `-o, --out-dir` | `<name>_parts` | 输出目录 |
| `--max-height` | 4096 | 目标段高（像素）/ target segment height |
| `--overlap` | 24 | 段间重叠像素 / overlap between segments |
| `--tolerance` | 400 | 切线搜索窗口半径 / search window around max-height |
| `--threshold` | 0.02 | 切线能量上限（超过视为文字行，禁止落刀）/ max allowed cut-row energy |
| `--dry-run` | off | 只输出切线可视化图，不写段文件 / only write cut-line preview |
| `--format` | same as input | 输出格式 png/jpeg/webp |

## Use as MCP server / MCP 配置

Zero extra dependencies — the protocol layer is hand-written JSON-RPC 2.0 over stdio
(no `mcp` SDK needed). Add to your agent config (Claude Code, ZCode, Cursor, ...):

```json
{
  "mcpServers": {
    "longshot-split": {
      "command": "longshot-split-mcp"
    }
  }
}
```

or with an explicit interpreter:

```json
{
  "mcpServers": {
    "longshot-split": {
      "command": "python",
      "args": ["-m", "longshot_split.mcp_server"]
    }
  }
}
```

### Tool: `split_long_image`

| Arg | Type | Default | Meaning |
|---|---|---|---|
| `path` | string | required | 长图路径 / path to the long image |
| `max_height` | integer | 4096 | 目标段高 / target segment height |
| `overlap` | integer | 24 | 段间重叠 / segment overlap |

Returns segment file paths + manifest summary (dimensions, y-ranges, cut energies).

## Python API

```python
from longshot_split.core import split_image
manifest = split_image("chat.png", out_dir="out/")  # returns dict, writes files
```

## FAQ

**Q: 切线会切到文字吗？** A: 不会。切线只允许落在能量低于阈值的安全行上；窗口内找不到安全行会向下顺延，宁可段高超标也不穿文字。

**Q: 为什么最后一段可能比 `max-height` 高？** A: 当剩余高度不足“max-height + tolerance”时不再切割，避免产生过小的尾巴段。

**Q: MCP server 需要额外装 SDK 吗？** A: 不需要，协议层为手写 stdio JSON-RPC 2.0，零额外依赖。

**Q: 支持哪些格式？EXIF 旋转图？** A: PNG/JPEG/WebP；读取时会按 EXIF 方向自动转正。

## Development / 开发自测

```bash
python -m pytest tests/ -v      # unit tests
python scripts/selftest_mcp.py  # MCP server end-to-end selftest
```

## Push to Gitee / 推送到 Gitee

本仓库 GitHub 地址: https://github.com/BingKaiWEI/longshot-split
Gitee 需要用户自己的凭据，运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/push_gitee.ps1
```

（脚本会添加 remote `gitee` 并推送 master；如无凭据会提示输入。）

## License

MIT — see [LICENSE](LICENSE).
