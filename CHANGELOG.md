# Changelog

## 0.1.0 (2026-11-09)

- Initial release.
- Adaptive long-screenshot splitting: row-energy based safe cut lines, never across text.
- CLI (`longshot-split`) and MCP server (`longshot-split-mcp`, stdio JSON-RPC 2.0, zero extra deps).
- PNG/JPEG/WebP support, EXIF orientation fix, `--dry-run` cut-line preview, `manifest.json` output.
