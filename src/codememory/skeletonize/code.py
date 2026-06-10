"""Code skeletonization using Tree-sitter for multi-language support.

Phase 3: Python, JavaScript/TypeScript via Tree-sitter.
Annotations: ``# @weight:N`` (Python) or ``// @weight:N`` (JS/TS)
on the line immediately before a function/class definition.
"""

from __future__ import annotations


# ── Language registry ──────────────────────────────────────────────────

# (Language, comment_prefix, stub_token, definable_node_types)
_LANG_SPECS: dict[str, tuple] = {}
_DEFINABLE: dict[str, dict[str, str | None]] = {}


def _register() -> None:
    """Lazily register Tree-sitter languages (avoid import-time overhead)."""
    if _LANG_SPECS:
        return

    # Python
    try:
        import tree_sitter_python as tspy
        from tree_sitter import Language
        _LANG_SPECS['.py'] = (Language(tspy.language()), '#', 'pass')
        _DEFINABLE['.py'] = {
            'function_definition': 'body',
            'class_definition': 'body',
            'decorated_definition': None,  # unwrapped below
        }
    except ImportError:
        pass

    # JavaScript
    try:
        import tree_sitter_javascript as tsjs
        from tree_sitter import Language
        js_lang = Language(tsjs.language())
        js_defs = {
            'function_declaration': 'body',
            'class_declaration': 'body',
            'method_definition': 'body',
            'generator_function_declaration': 'body',
        }
        for ext in ('.js', '.mjs', '.cjs'):
            _LANG_SPECS[ext] = (js_lang, '//', '{}')
            _DEFINABLE[ext] = dict(js_defs)
    except ImportError:
        pass

    # TypeScript
    try:
        import tree_sitter_typescript as tsts
        from tree_sitter import Language
        ts_lang = Language(tsts.language_typescript())
        ts_defs = {
            'function_declaration': 'body',
            'class_declaration': 'body',
            'method_definition': 'body',
            'generator_function_declaration': 'body',
        }
        for ext in ('.ts', '.tsx'):
            _LANG_SPECS[ext] = (ts_lang, '//', '{}')
            _DEFINABLE[ext] = dict(ts_defs)
    except ImportError:
        pass

    # Go
    try:
        import tree_sitter_go as tsgo
        from tree_sitter import Language
        go_lang = Language(tsgo.language())
        go_defs = {
            'function_declaration': 'body',
            'method_declaration': 'body',
        }
        _LANG_SPECS['.go'] = (go_lang, '//', '{}')
        _DEFINABLE['.go'] = dict(go_defs)
    except ImportError:
        pass

    # Rust
    try:
        import tree_sitter_rust as tsrust
        from tree_sitter import Language
        rust_lang = Language(tsrust.language())
        rust_defs = {
            'function_item': 'body',
            'impl_item': 'body',
        }
        _LANG_SPECS['.rs'] = (rust_lang, '//', '{}')
        _DEFINABLE['.rs'] = dict(rust_defs)
    except ImportError:
        pass

    # Java
    try:
        import tree_sitter_java as tsjava
        from tree_sitter import Language
        java_lang = Language(tsjava.language())
        java_defs = {
            'method_declaration': 'body',
            'class_declaration': 'body',
        }
        _LANG_SPECS['.java'] = (java_lang, '//', '{}')
        _DEFINABLE['.java'] = dict(java_defs)
    except ImportError:
        pass


def skeletonize_module(text: str, file_ext: str,
                       config_weight: int | None = None) -> str:
    """Skeletonize a source file at module level — zero config, no @weight needed.

    Preserves imports, class/function signatures, decorators, and module-level
    variables. All function and class bodies are replaced with stub tokens
    (``pass`` for Python, ``{}`` for JS/TS).

    This is equivalent to ``skeletonize_code(text, ext, min_weight=11)``.
    """
    return skeletonize_code(text, file_ext, min_weight=11,
                            config_weight=config_weight)


def supports_extension(ext: str) -> bool:
    """Check if the file extension has Tree-sitter support available."""
    _register()
    return ext.lower() in _LANG_SPECS


# ── Public API ─────────────────────────────────────────────────────────


def skeletonize_code(text: str, file_ext: str, min_weight: int = 5,
                     config_weight: int | None = None) -> str:
    """Skeletonize source code by replacing low-weight function bodies.

    Preserves imports, module-level code, and high-weight definitions.
    Low-weight function/class bodies are replaced with stub tokens
    (``pass`` for Python, ``{}`` for JS/TS).

    Annotations are read from the line immediately before the definition:
      # @weight:7        (Python)
      // @weight:7       (JS/TS)

    *config_weight* provides a fallback default (from
    ``.codememory/skeletonize.yaml`` glob matching). ``@weight``
    annotations in source always take precedence.

    If a parse error occurs the original text is returned unchanged.
    """
    _register()

    ext = file_ext.lower()
    if ext not in _LANG_SPECS:
        raise ValueError(f"Unsupported file extension for code skeletonization: {ext}")

    lang, comment_prefix, stub_token = _LANG_SPECS[ext]
    definable = _DEFINABLE.get(ext, {})

    from tree_sitter import Parser
    parser = Parser(lang)

    try:
        tree = parser.parse(text.encode('utf-8'))
    except Exception:
        return text

    replacements: list[tuple[int, int, str]] = []  # (start_byte, end_byte, new_text)

    default_weight = config_weight if config_weight is not None else 5

    _walk(tree.root_node, text, ext, definable, comment_prefix,
          stub_token, min_weight, default_weight, replacements)

    # Apply replacements in reverse byte order
    replacements.sort(key=lambda r: r[0], reverse=True)
    result = text.encode('utf-8')
    for start, end, repl in replacements:
        result = result[:start] + repl.encode('utf-8') + result[end:]

    return result.decode('utf-8')


# ── Internal helpers ───────────────────────────────────────────────────


def _walk(node, text: str, ext: str, definable: dict, comment_prefix: str,
          stub_token: str, min_weight: int, default_weight: int,
          replacements: list[tuple[int, int, str]]) -> None:
    """Recursively walk the AST and collect body replacements."""
    node_type = node.type

    # Unwrap decorated_definition to the inner function/class
    effective = node
    body_field = definable.get(node_type)
    if node_type == 'decorated_definition':
        for child in node.children:
            if child.type in definable:
                effective = child
                body_field = definable[child.type]
                break

    if body_field is not None:
        weight = _get_node_weight(node, text, ext, default_weight)
        if weight < min_weight:
            body_node = effective.child_by_field_name(body_field)
            if body_node is not None:
                indent = _get_indent(text, node.start_byte)
                inner_indent = indent + '    '
                removed = body_node.end_byte - body_node.start_byte

                if ext == '.py':
                    # block starts AFTER ':\n    ' — already indented
                    repl = (
                        f'{stub_token}  {comment_prefix} @weight:{weight}\n'
                        f'{inner_indent}{comment_prefix} <!-- truncated: '
                        f'{removed} chars, ~{removed} tokens -->\n'
                    )
                else:
                    # JS/TS: body is statement_block which includes braces
                    repl = (
                        f'{{\n'
                        f'{inner_indent}{comment_prefix} @weight:{weight}\n'
                        f'{inner_indent}{comment_prefix} <!-- truncated: '
                        f'{removed} chars, ~{removed} tokens -->\n'
                        f'{indent}}}'
                    )

                replacements.append((body_node.start_byte, body_node.end_byte, repl))
                return  # don't recurse into replaced body

    # Recurse into children (for nested definitions inside high-weight containers)
    for child in node.children:
        _walk(child, text, ext, definable, comment_prefix,
              stub_token, min_weight, default_weight, replacements)


def _get_node_weight(node, text: str, ext: str, default_weight: int = 5) -> int:
    """Extract weight from comment line(s) immediately before a node.

    Returns the @weight annotation value if found, otherwise *default_weight*.
    """
    node_start = node.start_byte
    prefix = text[:node_start]
    lines = prefix.split('\n')

    # Walk backwards through non-empty lines looking for annotation
    for line in reversed(lines[-3:]):
        stripped = line.strip()
        if not stripped:
            continue
        from .common import parse_weight
        val = parse_weight(stripped)
        if val is not None:
            return val
        # Stop at first non-comment non-empty line
        if ext == '.py' and not stripped.startswith('#'):
            break
        elif ext in ('.js', '.ts', '.mjs', '.cjs', '.tsx') and not stripped.startswith('//'):
            break

    return default_weight


def _get_indent(text: str, byte_pos: int) -> str:
    """Extract the whitespace indentation at *byte_pos*."""
    line_start = text.rfind('\n', 0, byte_pos)
    line_start = line_start + 1 if line_start >= 0 else 0
    chars: list[str] = []
    for i in range(line_start, byte_pos):
        if text[i] in ' \t':
            chars.append(text[i])
        else:
            break
    return ''.join(chars)
