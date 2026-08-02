from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"

_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_CODE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = _LINK.sub(
        lambda match: f'<a href="{html.escape(match.group(2))}">{match.group(1)}</a>', escaped
    )
    escaped = _CODE.sub(lambda match: f"<code>{match.group(1)}</code>", escaped)
    escaped = escaped.replace("**", "")
    return escaped


def markdown(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            continue
        if line.startswith("#"):
            flush_paragraph()
            close_list()
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            output.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
            continue
        if line.startswith("- "):
            flush_paragraph()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline(line[2:])}</li>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline(line[2:])}</blockquote>")
            continue
        if line.startswith("|"):
            flush_paragraph()
            close_list()
            output.append(f'<pre class="table-source">{html.escape(line)}</pre>')
            continue
        paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    if code:
        output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(output)


def page(title: str, body: str, navigation: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Temperamento</title><style>
:root{{--ink:#17151b;--muted:#66616e;--paper:#fff;--wash:#f5f3f8;--accent:#5731b2;--line:#ddd7e8}}*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:16px/1.65 system-ui,-apple-system,sans-serif}}header{{background:#21163b;color:white;padding:20px}}header a{{color:white;text-decoration:none;font-weight:700;font-size:22px}}.layout{{max-width:1240px;margin:auto;display:grid;grid-template-columns:250px minmax(0,1fr);gap:24px;padding:28px 18px 64px}}nav{{position:sticky;top:20px;align-self:start;background:white;border:1px solid var(--line);border-radius:14px;padding:16px}}nav a{{display:block;color:var(--accent);padding:5px 0;text-decoration:none}}main{{background:white;border:1px solid var(--line);border-radius:14px;padding:28px;min-width:0}}h1,h2,h3{{line-height:1.22}}h1{{margin-top:0}}code{{background:#eeeaf6;padding:2px 5px;border-radius:4px}}pre{{overflow:auto;background:#17151b;color:#eeeaf6;padding:16px;border-radius:9px}}blockquote{{border-left:4px solid var(--accent);margin-left:0;padding-left:16px;color:var(--muted)}}img{{max-width:100%}}a{{color:var(--accent)}}@media(max-width:800px){{.layout{{display:block}}nav{{position:static;margin-bottom:20px}}}}
</style></head><body><header><a href="index.html">Temperamento</a></header><div class="layout"><nav>{navigation}</nav><main>{body}</main></div></body></html>"""


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    documents = [("README.md", ROOT / "README.md")]
    documents.extend((path.name, path) for path in sorted((ROOT / "docs").glob("*.md")))
    links = []
    for _, path in documents:
        output_name = "index.html" if path == ROOT / "README.md" else path.stem.lower() + ".html"
        links.append((path.stem.replace("_", " ").title(), output_name))
    navigation = "".join(f'<a href="{href}">{html.escape(label)}</a>' for label, href in links)
    for _, path in documents:
        output_name = "index.html" if path == ROOT / "README.md" else path.stem.lower() + ".html"
        source = path.read_text(encoding="utf-8")
        title = next(
            (line[2:].strip() for line in source.splitlines() if line.startswith("# ")), path.stem
        )
        rendered = markdown(source)
        rendered = rendered.replace('href="docs/', 'href="').replace('.md"', '.html"')
        (SITE / output_name).write_text(page(title, rendered, navigation), encoding="utf-8")
    assets = ROOT / "docs" / "assets"
    if assets.exists():
        shutil.copytree(assets, SITE / "assets")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
