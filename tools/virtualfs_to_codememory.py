#!/usr/bin/env python3
"""Convert virtualfs-style API docs (xxx.CLASS.METHOD.html) to codememory atoms.

Usage:
    python tools/virtualfs_to_codememory.py \\
        --from-json api_data.json \\
        --root examples/quant_operators

The JSON input describes the API structure:
{
  "classes": [
    {
      "name": "QuantExpr",
      "description": "...",
      "methods": [
        {"name": "sharpe", "signature": "([annual_days, compound])", "description": "...", "group": "risk"},
        ...
      ]
    }
  ]
}

Dependencies are inferred naturally:
  - method → parent class: required
  - method → methods that share parameter types: recommended
  - method → methods in same group: related
  - QuantDF → QuantExpr (because DF methods apply Expr operations): recommended
"""

import json
import sys
from pathlib import Path
from textwrap import dedent


def slug(text: str) -> str:
    return text.lower().replace(" ", "-").replace("_", "-")


def method_id(class_name: str, method_name: str) -> str:
    return f"api/{slug(class_name)}/{method_name}"


def generate_method_memory(cls: dict, method: dict, root: Path) -> Path:
    """Generate a single method atom."""
    class_name = cls["name"]
    m_name = method["name"]
    m_id = method_id(class_name, m_name)
    group = method.get("group", "general")

    # Determine imports
    required = [f"api/{slug(class_name)}"]
    recommended = []
    related = []

    # Methods in same group are related (skip self)
    for other in cls.get("methods", []):
        if other is not method and other.get("group") == group:
            related.append(method_id(class_name, other["name"]))

    # If this is a QuantDF method, recommend QuantExpr
    if class_name == "QuantDF":
        recommended.append("api/quantexpr")

    body = dedent(f"""\
    # {class_name}.{m_name}

    ## 签名

    ```
    {class_name}.{m_name}{method.get('signature', '()')}
    ```

    ## 说明

    {method.get('description', 'See API documentation.')}

    ## 所属类

    [{class_name}]({cls.get('description', '')})
    """)

    raw_summary = method.get("summary") or (
        f"{class_name}.{m_name}: {method.get('description', '')[:80]}"
    )
    # Quote summary to handle colons and special YAML chars
    import yaml
    summary = yaml.dump(raw_summary, allow_unicode=True, default_style="'").strip()

    tags = ["api-doc", slug(class_name)]
    if group:
        tags.append(group)

    frontmatter = f"""---
type: atom
id: {m_id}
summary: {summary}
status: active
version: 1
tags: {json.dumps(tags)}
intensity: 5
maturity: draft
imports:
  required: {json.dumps(required)}
  recommended: {json.dumps(recommended) if recommended else '[]'}
  related: {json.dumps(related) if related else '[]'}
---
{body}"""

    out_dir = root / "/".join(m_id.split("/")[:-1])  # api/quantexpr → root/api/quantexpr/
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / f"{m_name}.md"
    filepath.write_text(frontmatter, encoding="utf-8")
    return filepath


def generate_class_memory(cls: dict, root: Path) -> Path:
    """Generate a class overview atom (without methods)."""
    class_name = cls["name"]
    c_id = f"api/{slug(class_name)}"
    group = cls.get("group", "general")

    method_list = "\n".join(
        f"- [{m['name']}]({method_id(class_name, m['name'])}) — {m.get('description', '')[:60]}"
        for m in cls.get("methods", [])
    )

    body = dedent(f"""\
    # {class_name}

    ## 概述

    {cls.get('description', '')}

    ## 方法列表

    {method_list}
    """)

    import yaml
    raw_summary = f"{class_name}: {cls.get('description', '')} ({len(cls.get('methods', []))} 个方法)"
    summary = yaml.dump(raw_summary, allow_unicode=True, default_style="'").strip()

    tags = ["api-doc", slug(class_name), "class-overview"]

    frontmatter = f"""---
type: atom
id: {c_id}
summary: {summary}
status: active
version: 1
tags: {json.dumps(tags)}
intensity: 7
maturity: draft
imports:
  required: []
  recommended: []
  related: []
---
{body}"""

    out_dir = root / c_id  # api/quantexpr → root/api/quantexpr/
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / "_index.md"
    filepath.write_text(frontmatter, encoding="utf-8")
    return filepath


def main():
    data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    if not data:
        print("Usage: cat api_data.json | python tools/virtualfs_to_codememory.py --root <root>")
        sys.exit(1)

    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path("examples/quant_operators")
    root.mkdir(parents=True, exist_ok=True)
    (root / ".codememory").mkdir(exist_ok=True)

    count = 0
    for cls in data.get("classes", []):
        generate_class_memory(cls, root)
        count += 1
        for method in cls.get("methods", []):
            generate_method_memory(cls, method, root)
            count += 1

    print(f"Generated {count} atoms in {root}")

    # Reindex
    from codememory.index import reindex
    reindex(root)
    print("Reindex complete.")


if __name__ == "__main__":
    main()
