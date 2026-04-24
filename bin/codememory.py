#!/usr/bin/env python3
import os
import sys
import json
import yaml
import hashlib
import argparse
from datetime import datetime, date
from pathlib import Path

# ==========================================
# Core Utilities
# ==========================================

def get_root_dir(custom_root=None):
    if custom_root:
        return Path(custom_root).resolve()
    # Assume script is in bin/ and root is one level up
    return Path(__file__).resolve().parent.parent

def compute_body_hash(body: str) -> str:
    """sha256(body)[:7]"""
    return hashlib.sha256(body.encode('utf-8')).hexdigest()[:7]

def estimate_tokens(text: str) -> int:
    """Prototype phase: length of string as token proxy."""
    return len(text)

def parse_frontmatter(filepath: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter and body."""
    try:
        content = filepath.read_text(encoding='utf-8-sig')
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return {}, ""
    
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_str = parts[1]
    body = parts[2].strip()
    
    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {filepath}: {e}", file=sys.stderr)
        metadata = {}
        
    return metadata, body

def get_memory_path(root_dir: Path, memory_id: str) -> Path:
    """Resolve a memory ID to a file path. E.g. 'user/ideas/x' -> root/user/ideas/x.md"""
    # prevent directory traversal
    safe_id = memory_id.replace('..', '')
    return root_dir / f"{safe_id}.md"


# ==========================================
# Index Management
# ==========================================

def get_index_path(root_dir: Path) -> Path:
    return root_dir / '.codememory' / 'index.json'

def load_index(root_dir: Path) -> dict:
    idx_path = get_index_path(root_dir)
    if not idx_path.exists():
        return {"version": 1, "updated": datetime.now().isoformat(), "memories": {}}
    try:
        with open(idx_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load index: {e}", file=sys.stderr)
        return {"version": 1, "updated": datetime.now().isoformat(), "memories": {}}

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def save_index(root_dir: Path, index_data: dict):
    idx_path = get_index_path(root_dir)
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    index_data['updated'] = datetime.now().isoformat()
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False, cls=DateEncoder)


# ==========================================
# Commands
# ==========================================

def cmd_create(args):
    root = get_root_dir(args.root)
    file_path = get_memory_path(root, args.id)
    
    if file_path.exists():
        print(f"Error: Memory {args.id} already exists at {file_path}", file=sys.stderr)
        sys.exit(1)
        
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    frontmatter = {
        "type": args.type,
        "id": args.id,
        "summary": "TODO: fill in summary",
        "status": "active",
        "created": now,
        "updated": now,
        "version": 1,
        "tags": ["untagged"],
        "source": {
            "platform": "manual",
            "created_by": "user"
        },
        "summary_hash": "placeholder"
    }
    
    if args.schema:
        frontmatter["schema"] = args.schema
        
    if args.type in ["composite", "instance"]:
        frontmatter["imports"] = {
            "required": [],
            "recommended": [],
            "related": []
        }
        
    body_template = f"\n# {args.id.split('/')[-1].replace('-', ' ').title()}\n\nWrite content here...\n"
    
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{body_template}"
    
    file_path.write_text(content, encoding='utf-8')
    print(f"Created memory at {file_path}")
    
    # Auto-update index
    # We could just call cmd_reindex but updating a single entry is faster.
    # For phase 1, we'll just run a full reindex for safety, it's fast enough.
    print("Updating index...")
    cmd_reindex(args)


def cmd_reindex(args):
    root = get_root_dir(args.root)
    index_data = {
        "version": 1,
        "updated": datetime.now().isoformat(),
        "memories": {}
    }
    
    search_dirs = ['user', 'self', 'schemas']
    count = 0
    
    for d in search_dirs:
        dir_path = root / d
        if not dir_path.exists():
            continue
            
        for filepath in dir_path.rglob('*.md'):
            try:
                rel_path = filepath.relative_to(root).as_posix()
                memory_id = str(filepath.relative_to(root).with_suffix('')).replace('\\', '/')
                
                meta, _ = parse_frontmatter(filepath)
                
                # Check required base fields to be considered a valid memory
                if 'type' not in meta or 'id' not in meta:
                    continue
                
                # Use ID from frontmatter if present, else derived from path
                actual_id = meta.get('id', memory_id)
                
                entry = {
                    "type": meta.get('type'),
                    "summary": meta.get('summary', ''),
                    "status": meta.get('status', 'active'),
                    "tags": meta.get('tags', []),
                    "created": meta.get('created', ''),
                    "updated": meta.get('updated', ''),
                    "version": meta.get('version', 1),
                    "path": rel_path
                }
                
                if 'schema' in meta:
                    entry['schema'] = meta['schema']
                if 'imports' in meta:
                    entry['imports'] = meta['imports']
                    
                index_data['memories'][actual_id] = entry
                count += 1
            except Exception as e:
                print(f"Error indexing {filepath}: {e}", file=sys.stderr)
                
    save_index(root, index_data)
    print(f"Reindexed {count} memories successfully.")


def _get_imports(meta, depth):
    imports_dict = meta.get('imports', {})
    if not isinstance(imports_dict, dict):
        return []
    
    deps = []
    
    reqs = imports_dict.get('required', [])
    for r in reqs:
        if isinstance(r, str):
             deps.append(r)
        elif isinstance(r, dict) and 'id' in r:
             deps.append(r['id'])
             
    if depth in ("recommended", "full"):
        recs = imports_dict.get('recommended', [])
        for r in recs:
            if isinstance(r, str): deps.append(r)
            elif isinstance(r, dict) and 'id' in r: deps.append(r['id'])
            
    if depth == "full":
        rels = imports_dict.get('related', [])
        for r in rels:
            if isinstance(r, str): deps.append(r)
            elif isinstance(r, dict) and 'id' in r: deps.append(r['id'])
            
    return deps

def build_dag(memory_id, depth, index):
    """Returns {node_id: [dependency_ids]}"""
    graph = {}
    queue = [memory_id]
    
    while queue:
        curr = queue.pop(0)
        if curr in graph:
            continue
            
        if curr not in index['memories']:
            print(f"Warning: Memory '{curr}' not found in index.", file=sys.stderr)
            graph[curr] = []
            continue
            
        entry = index['memories'][curr]
        deps = _get_imports(entry, depth)
        graph[curr] = deps
        queue.extend(deps)
        
    return graph

def find_cycle_participants(graph):
    """DFS with coloring (0=white, 1=gray, 2=black)"""
    color = {u: 0 for u in graph}
    cycle_nodes = set()
    
    def dfs(u, path):
        color[u] = 1
        for v in graph.get(u, []):
            if color.get(v, 0) == 1:
                # Cycle detected
                cycle_start = path.index(v) if v in path else 0
                cycle_nodes.update(path[cycle_start:])
                cycle_nodes.add(v)
            elif color.get(v, 0) == 0:
                dfs(v, path + [v])
        color[u] = 2
        
    for u in graph:
        if color[u] == 0:
            dfs(u, [u])
            
    return list(cycle_nodes)

def topological_sort(graph):
    """Kahn's algorithm"""
    in_degree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] = in_degree.get(v, 0) + 1
            
    queue = [u for u in in_degree if in_degree[u] == 0]
    topo_order = []
    
    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    # Reverse to load dependencies before dependants
    return list(reversed(topo_order))


def cmd_resolve(args):
    root = get_root_dir(args.root)
    index = load_index(root)
    
    if args.id not in index['memories']:
        print(f"Error: Target memory '{args.id}' not found. Did you reindex?", file=sys.stderr)
        sys.exit(1)
        
    # 1. Build DAG
    graph = build_dag(args.id, args.depth, index)
    
    # 2. Cycle Detection
    cycle_ids = find_cycle_participants(graph)
    if cycle_ids:
        print(f"WARNING: Circular dependency detected involving: {cycle_ids}", file=sys.stderr)
        print("Skipping cycle nodes to continue resolution...", file=sys.stderr)
        # Remove incoming edges to cycle nodes to break the cycle.
        # For simplicity in prototype, we just break the graph edges involved in cycle.
        for u in list(graph.keys()):
             graph[u] = [v for v in graph[u] if v not in cycle_ids]
    
    # 3. Topo Sort
    ordered = topological_sort(graph)
    
    # If there were cycles, the topo sort might miss some disconnected components.
    # Add any nodes that didn't make it to the end (ignoring cycle nodes themselves)
    for node in graph:
        if node not in ordered and node not in cycle_ids:
            ordered.insert(0, node) # best effort placement
            
    # Add cycle nodes at the very end just to load them
    for node in cycle_ids:
        if node not in ordered:
            ordered.append(node)
            
    # 4. (No version parsing in MVP, assume latest local file is the version)
    
    # 5. Token Trim & Output
    budget = args.budget if args.budget else float('inf')
    used = 0
    
    print(f"# Resolved Context for '{args.id}'\n")
    print(f"*(Depth: {args.depth}, Budget: {budget} chars)*\n")
    
    # Determine which nodes are 'required' strictly from the target's perspective.
    # For MVP, we'll check if it's in the required graph from the root.
    req_graph = build_dag(args.id, "required", index)
    
    for i, mid in enumerate(ordered):
        if mid not in index['memories']:
            continue
            
        entry = index['memories'][mid]
        file_path = root / entry['path']
        meta, body = parse_frontmatter(file_path)
        
        full_text = f"## [{i+1}/{len(ordered)}] {mid} ({entry['type']})\n\n{body}\n\n"
        summary_text = f"## [{i+1}/{len(ordered)}] {mid} ({entry['type']} - SUMMARY ONLY)\n\n> {entry['summary']}\n\n"
        
        t_full = estimate_tokens(full_text)
        t_sum = estimate_tokens(summary_text)
        
        if used + t_full <= budget:
            print(full_text)
            used += t_full
        elif mid in req_graph:
            # Downgrade to summary
            print(summary_text)
            used += t_sum
        else:
            print(f"## [{i+1}/{len(ordered)}] {mid} (SKIPPED - Out of budget)\n\n")
            
    print(f"---\nTotal Budget Used: {used}/{budget}")


def check_schema_compliance(metadata, schemas):
    schema_id = metadata.get('schema')
    if not schema_id: return []
    schema = schemas.get(schema_id)
    if not schema: return [f"Schema '{schema_id}' not found"]
    return [f"Missing required field: {f['name']}"
            for f in schema.get('fields', [])
            if f.get('required') and f['name'] not in metadata]

def cmd_validate(args):
    root = get_root_dir(args.root)
    index = load_index(root)
    memories = index['memories']
    
    errors = 0
    warnings = 0
    
    # Build full schema dict for lookup
    schemas = {}
    for mid, entry in memories.items():
        if entry['type'] == 'schema':
             file_path = root / entry['path']
             meta, _ = parse_frontmatter(file_path)
             schemas[mid] = meta
             
    print("Running CodeMemory Validation...\n")
             
    for mid, entry in memories.items():
        # 1. Broken link check
        deps = _get_imports(entry, "full")
        for dep in deps:
            if dep not in memories:
                print(f"[ERROR] {mid} imports non-existent memory: {dep}")
                errors += 1
                
        # 2. Schema compliance
        if entry['type'] == 'instance':
            file_path = root / entry['path']
            meta, _ = parse_frontmatter(file_path)
            compliance_errors = check_schema_compliance(meta, schemas)
            for err in compliance_errors:
                print(f"[ERROR] {mid} schema compliance: {err}")
                errors += 1
                
        # 3. Cycle check (building graph from this node)
        graph = build_dag(mid, "required", index)
        cycle_ids = find_cycle_participants(graph)
        if cycle_ids and mid in cycle_ids:
             print(f"[WARNING] {mid} is part of a circular dependency involving: {cycle_ids}")
             print(f"          Fix: Consider merging atoms or placing in a composite as siblings.")
             warnings += 1
             
    print(f"\nValidation complete. {len(memories)} memories checked.")
    print(f"Errors: {errors}, Warnings: {warnings}")
    
    if errors > 0:
        sys.exit(1)


# ==========================================
# Main
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="CodeMemory CLI Prototype")
    parser.add_argument('--root', help="Root directory of CodeMemory (defaults to script parent's parent)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create
    p_create = subparsers.add_parser('create', help="Create a new memory")
    p_create.add_argument('--type', required=True, choices=['atom', 'schema', 'instance', 'composite'])
    p_create.add_argument('--id', required=True)
    p_create.add_argument('--schema', help="Schema ID (required if type=instance)")
    
    # resolve
    p_resolve = subparsers.add_parser('resolve', help="Resolve and print memory context")
    p_resolve.add_argument('id', help="Memory ID to resolve")
    p_resolve.add_argument('--depth', choices=['required', 'recommended', 'full'], default='required')
    p_resolve.add_argument('--budget', type=int, help="Token budget (chars)")
    
    # reindex
    p_reindex = subparsers.add_parser('reindex', help="Rebuild index.json")
    
    # validate
    p_validate = subparsers.add_parser('validate', help="Run integrity checks")
    
    args = parser.parse_args()
    
    if args.command == 'create':
        if args.type == 'instance' and not args.schema:
            parser.error("--schema is required when type is 'instance'")
        cmd_create(args)
    elif args.command == 'reindex':
        cmd_reindex(args)
    elif args.command == 'resolve':
        cmd_resolve(args)
    elif args.command == 'validate':
        cmd_validate(args)

if __name__ == '__main__':
    main()
