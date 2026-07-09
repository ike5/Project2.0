"""Generator for a single NeetCode-150 module.

Reads `_meta/<module_name>.py` (e.g. `01_arrays_hashing`), which exposes
`PROBLEMS` — a list of dicts. Emits for each problem:

    problems/NN-name/README.md
    solutions/NN-name/solution.py
    solutions/NN-name/Solution.java
    solutions/NN-name/walkthrough.md

Usage:
    cd neetcode-150-course
    python _meta/gen_module.py 01_arrays_hashing
"""

import importlib
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(COURSE_ROOT))


def module_dir_for(meta_name: str) -> Path:
    """`01_arrays_hashing` -> `01-arrays-hashing`."""
    n, _, rest = meta_name.partition("_")
    return COURSE_ROOT / f"{n}-{rest.replace('_', '-')}"


# ====================================================================
# Helpers (Python and Java)
# ====================================================================

PY_LINKED_LIST_HELPERS = '''
class ListNode:
    """A minimal singly linked list node."""
    def __init__(self, val: int = 0, nxt: "ListNode | None" = None) -> None:
        self.val = val
        self.next = nxt
        self.random = None   # only used by the copy-random-pointer problem


def build_list(values: list[int]) -> "ListNode | None":
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node  # type: ignore
            tail = node
    return head


def to_array_list(head: "ListNode | None") -> list[int]:
    out: list[int] = []
    while head is not None:
        out.append(head.val)
        head = head.next  # type: ignore
    return out
'''

PY_TREE_HELPERS = '''
class TreeNode:
    """A minimal binary tree node."""
    def __init__(self, val: int = 0,
                 left: "TreeNode | None" = None,
                 right: "TreeNode | None" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def from_array(arr: list[int | None]) -> "TreeNode | None":
    if not arr or arr[0] is None:
        return None
    nodes: list[TreeNode | None] = [None if v is None else TreeNode(v) for v in arr]
    kids = nodes[1:]
    for parent in nodes:
        if parent is None:
            continue
        if kids:
            parent.left = kids.pop(0)
        if kids:
            parent.right = kids.pop(0)
    return nodes[0]


def to_array(node: "TreeNode | None") -> list[int | None]:
    if node is None:
        return []
    out: list[int | None] = []
    q: list[TreeNode | None] = [node]
    while q:
        n = q.pop(0)
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out
'''

PY_GRAPH_HELPERS = '''
class GraphNode:
    """A minimal undirected graph node."""
    def __init__(self, val: int = 0,
                 neighbors: "list[GraphNode] | None" = None) -> None:
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def build_graph(adj: list[list[int]]) -> "GraphNode | None":
    """Build an undirected graph from an adjacency list of int neighbor ids.
    Returns the node with id 1, or None for an empty graph.
    Assumes nodes are labeled 1..N."""
    if not adj:
        return None
    n = len(adj)
    nodes = [GraphNode(i + 1) for i in range(n)]
    for i, nbrs in enumerate(adj):
        for j in nbrs:
            nodes[i].neighbors.append(nodes[j - 1])
    return nodes[0]
'''

JAVA_LINKED_LIST_HELPERS = '''
    public static class ListNode {
        int val;
        ListNode next;
        ListNode random;   // only used by the copy-random-pointer problem
        ListNode(int v) { val = v; }
        ListNode(int v, ListNode n) { val = v; next = n; }
    }

    private static ListNode buildList(int[] a) {
        ListNode head = null, tail = null;
        for (int v : a) {
            ListNode n = new ListNode(v);
            if (head == null) { head = n; tail = n; }
            else { tail.next = n; tail = n; }
        }
        return head;
    }

    private static int[] toArrayList(ListNode head) {
        java.util.List<Integer> out = new java.util.ArrayList<>();
        for (ListNode n = head; n != null; n = n.next) out.add(n.val);
        int[] arr = new int[out.size()];
        for (int i = 0; i < out.size(); i++) arr[i] = out.get(i);
        return arr;
    }
'''

JAVA_TREE_HELPERS = '''
    public static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int v) { val = v; }
        TreeNode(int v, TreeNode l, TreeNode r) { val = v; left = l; right = r; }
    }

    private static TreeNode fromArray(Integer[] arr) {
        if (arr == null || arr.length == 0 || arr[0] == null) return null;
        TreeNode[] nodes = new TreeNode[arr.length];
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] != null) nodes[i] = new TreeNode(arr[i]);
        }
        java.util.List<TreeNode> kids = new java.util.ArrayList<>();
        for (int i = 1; i < arr.length; i++) kids.add(nodes[i]);
        for (TreeNode parent : nodes) {
            if (parent == null) continue;
            if (!kids.isEmpty()) parent.left = kids.remove(0);
            if (!kids.isEmpty()) parent.right = kids.remove(0);
        }
        return nodes[0];
    }

    private static Integer[] toArrayTree(TreeNode node) {
        if (node == null) return new Integer[0];
        java.util.List<Integer> out = new java.util.ArrayList<>();
        java.util.List<TreeNode> q = new java.util.ArrayList<>();
        q.add(node);
        while (!q.isEmpty()) {
            TreeNode n = q.remove(0);
            if (n == null) { out.add(null); continue; }
            out.add(n.val);
            q.add(n.left);
            q.add(n.right);
        }
        while (!out.isEmpty() && out.get(out.size() - 1) == null) out.remove(out.size() - 1);
        return out.toArray(new Integer[0]);
    }
'''

JAVA_GRAPH_HELPERS = '''
    public static class GraphNode {
        int val;
        java.util.List<GraphNode> neighbors = new java.util.ArrayList<>();
        GraphNode(int v) { val = v; }
    }
'''

JAVA_TRIE_HELPERS = '''
    public static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        String word;
    }

    public static void trieDfs(char[][] board, int r, int c, TrieNode n, java.util.List<String> out) {
        if (n == null) return;
        char ch = board[r][c];
        if (ch == '#') return;
        TrieNode child = n.children[ch - 'a'];
        if (child == null) return;
        if (child.word != null) {
            out.add(child.word);
            child.word = null;
        }
        board[r][c] = '#';
        if (r > 0)                 trieDfs(board, r - 1, c, child, out);
        if (c > 0)                 trieDfs(board, r, c - 1, child, out);
        if (r < board.length - 1)  trieDfs(board, r + 1, c, child, out);
        if (c < board[0].length - 1) trieDfs(board, r, c + 1, child, out);
        board[r][c] = ch;
    }
'''


# ====================================================================
# Per-file writers
# ====================================================================

def write_problem_readme(out: Path, p: dict) -> None:
    parts = [
        f"# {p['name']}",
        "",
        f"**Difficulty:** {p['difficulty']}",
        "",
        "## Problem",
        "",
        p["brief"],
        "",
        "## Examples",
        "",
    ]
    for inp, outp in p["examples"]:
        parts += ["```", f"Input:  {inp}", f"Output: {outp}", "```", ""]
    parts += ["## Constraints", ""]
    for c in p["constraints"]:
        parts.append(f"- {c}")
    parts += ["", "## Hints", ""]
    for i, h in enumerate(p["hints"], 1):
        parts.append(f"{i}. {h}")
    parts += [
        "",
        "## Solution",
        "",
        f"See [`../../solutions/{p['slug']}/`](../../solutions/{p['slug']}/) "
        f"for the Python and Java 21 solutions and a step-by-step "
        f"walkthrough.",
        "",
    ]
    out.write_text("\n".join(parts))


def _ensure_java_body(body: str) -> str:
    """Add trailing semicolons to return / break / continue / throw lines
    that lack them. The catalog omits them for readability."""
    out_lines = []
    keywords = ("return", "break", "continue", "throw")
    for line in body.split("\n"):
        stripped = line.lstrip()
        if not stripped or stripped in ("{", "}"):
            out_lines.append(line)
            continue
        if stripped.endswith(";"):
            out_lines.append(line)
            continue
        for kw in keywords:
            if stripped.startswith(kw):
                line = line + ";"
                break
        out_lines.append(line)
    return "\n".join(out_lines)


def _prepare_java_body(body: str, sig: str) -> str:
    """Normalize the catalog's body so it can be inserted as a class body.

    The catalog may use one of two styles:
      1. 'body only' style — just the inside of the main method.
         e.g. for `public static int foo(int x)` we have `if (x > 0) return x; return 0;`.
      2. 'full methods' style — multiple complete methods / classes.
         e.g. for `public static int foo(int x)` we have
         `public static int foo(int x) { ... }` plus other helpers.

    The wrapper puts the body at class level, so style 1 needs the
    signature prepended and a closing brace. Style 2 just needs the
    trailing 'extra' brace removed if present.

    Heuristic: if the body's first non-empty, non-comment line starts with
    `public` (i.e. it already declares a method), assume style 2 — the
    body is self-contained. Otherwise prepend the sig's opening.
    """
    body = _ensure_java_body(body)
    # Strip the leading docstring / leading comment lines
    lines = body.split("\n")
    # Find the first non-blank, non-comment line
    first_real = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith("//"):
            continue
        first_real = (i, s)
        break
    if first_real is None:
        return body

    _, first_text = first_real
    # If the first real line already declares `public` (i.e. a method),
    # style 2 — body is self-contained. But we still need to remove a
    # final `}` if the body's last non-empty line is `}` AND the body
    # has a balanced number of braces (so the trailing `}` is the
    # 'extra' one we don't need).
    # If the body has multiple methods (signaled by `private static` or
    # `public static` appearing as a non-first line), use Style 2.
    is_multi_method = (
        "    private " in body
        or "    public " in body
        or "\n    private " in body
        or "\n    public " in body
    )

    if first_text.startswith("public ") or first_text.startswith("private ") \
            or first_text.startswith("static ") or first_text.startswith("class ") \
            or is_multi_method:
        # Style 2: body has multiple methods/classes.
        # already has 2 more `{` than `}` (because of all the method
        # bodies), strip the last `}` so the wrapper's `}}` doesn't
        # produce an unbalanced class.
        opens = body.count("{")
        closes = body.count("}")
        # If the last non-empty line is `}` and there's an imbalance
        # (i.e. we have one more `}` than the natural number of method
        # closings), strip it.
        last_lines = [ln for ln in body.split("\n") if ln.strip()]
        if last_lines and last_lines[-1].strip() == "}" and closes >= opens:
            # The body's own method/class closings are balanced. If
            # the body's LAST `}` is the 'extra' one (because the
            # catalog wrapped the main method's body in `{...}`),
            # we need to remove it.
            # Check: if the last non-blank line is a single `}` and
            # it's at indent 4, and the second-to-last non-blank line
            # is also `}` — likely a closing brace of a nested method.
            # Heuristic: if `closes - opens >= 1` AND the very last `}` is
            # at indent level 4, strip it.
            stripped_lines = [ln for ln in body.split("\n") if ln.strip()]
            if len(stripped_lines) >= 1 and stripped_lines[-1] == "    }":
                body = "\n".join(body.split("\n")[:-1]).rstrip() + "\n"
        return body
    else:
        # Style 1: prepend the sig + `{` and a closing `}` (the wrapper
        # will provide its own class brace, so we just close our method).
        # Indent the body by 4 spaces.
        indented = "\n".join("    " + ln if ln else ln for ln in body.split("\n"))
        return f"    {sig} {{\n{indented}\n    }}"


def _norm_java_sig(java_sig: str) -> str:
    sig = java_sig.strip()
    if not sig.startswith("public "):
        sig = "public static " + sig
    else:
        if "static" not in sig.split("(", 1)[0]:
            sig = sig.replace("public ", "public static ", 1)
    while "static static" in sig:
        sig = sig.replace("static static", "static")
    return sig


def _build_java_main(sig: str, method_name: str, java_tests: list) -> str:
    test_lines = []
    for i, (args, _expected) in enumerate(java_tests, 1):
        call = f"{method_name}({args})"
        if sig.startswith("public static void "):
            test_lines.append(f"        {call};  // void call, no assertion")
            continue
        return_type = sig.split("(", 1)[0].strip().split()[-2]
        is_array_return = return_type.endswith("[]")
        if is_array_return:
            test_lines.append(
                f'        System.out.println("{i}: " + '
                f'Arrays.toString({call}));'
            )
        else:
            test_lines.append(
                f'        System.out.println("{i}: " + {call});'
            )
    if not test_lines:
        return f'        System.out.println("{method_name} ready");'
    return "\n".join(test_lines)


def _py_tests_block(tests, fn_name, is_class):
    test_lines = []
    visible = 0
    for i, (args, expected) in enumerate(tests, 1):
        if is_class:
            continue
        visible += 1
        args_repr = ", ".join(repr(a) for a in args)
        if (isinstance(expected, list) and expected
                and all(isinstance(g, list) for g in expected)):
            expected_repr = (
                "sorted([sorted(g) for g in " + repr(expected) + "])"
            )
            got_repr = (
                f"sorted([sorted(g) for g in {fn_name}({args_repr})])"
            )
        else:
            expected_repr = repr(expected)
            got_repr = f"{fn_name}({args_repr})"
        test_lines.append(
            f"    assert {got_repr} == {expected_repr}, "
            f'f"test {i} failed: got {{ {got_repr}!r }} expected {{ {expected_repr}!r }}"'
        )
    return ("\n".join(test_lines) if test_lines else "    pass  # no tests"), visible


def write_python_solution(out: Path, p: dict, py_sig: str, py_body: str,
                         py_tests: list) -> None:
    """py_sig may be a function signature or a class declaration.
    If it's a class, we wrap the class and use the same tests."""
    is_class = py_sig.lstrip().startswith("class ")
    fn_name = py_sig.split("(", 1)[0].split()[-1].rstrip(":")
    body = py_body
    tests_block, n_tests = _py_tests_block(py_tests, fn_name, is_class)

    # Choose helpers
    needs_ll = "ListNode" in py_sig or "ListNode" in py_body
    needs_tree = (
        "TreeNode" in py_sig or "TreeNode" in py_body
        or "from_array(" in py_body or "to_array(" in py_body
    )
    needs_graph = "GraphNode" in py_sig or "GraphNode" in py_body
    py_helpers = ""
    if needs_ll:
        py_helpers += PY_LINKED_LIST_HELPERS
    if needs_tree and not needs_ll:
        py_helpers += PY_TREE_HELPERS
    if needs_graph:
        py_helpers += PY_GRAPH_HELPERS

    content = f'''"""{p['name']}.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/{p['slug']}/solution.py
"""
{py_helpers}


{py_sig}
{body}


def _self_test() -> None:
{tests_block}
    print(f"all {n_tests} tests passed for {fn_name}")


if __name__ == "__main__":
    _self_test()
'''
    out.write_text(content)


def write_java_solution(out: Path, p: dict, java_sig: str, java_body: str,
                         java_tests: list, module_label: str = "NeetCode 150") -> None:
    sig = _norm_java_sig(java_sig)
    method_name = java_sig.split("(", 1)[0].split()[-1]
    tests_block = _build_java_main(sig, method_name, java_tests)

    # Choose helpers
    needs_ll = "ListNode" in java_sig or "ListNode" in java_body
    needs_tree = (
        "TreeNode" in java_sig or "TreeNode" in java_body
        or "fromArray(" in java_body or "toArrayTree(" in java_body
    )
    needs_graph = "GraphNode" in java_sig or "GraphNode" in java_body
    needs_trie = "TrieNode" in java_sig or "TrieNode" in java_body
    java_helpers = ""
    if needs_ll:
        java_helpers += JAVA_LINKED_LIST_HELPERS
    if needs_tree and not needs_ll:
        java_helpers += JAVA_TREE_HELPERS
    if needs_graph:
        java_helpers += JAVA_GRAPH_HELPERS
    if needs_trie:
        java_helpers += JAVA_TRIE_HELPERS

    # The body can be in one of three styles:
    #  Style 1: just the inside of the main method.
    #    e.g. for `public static int foo(int x)` we have `if (x > 0) return x; return 0;`
    #  Style 2: a complete method with signature.
    #    e.g. for `public static int foo(int x)` we have
    #    `public static int foo(int x) { if (x > 0) return x; return 0; }`
    #  Style 3: the body is the inside of the main method, followed by
    #    helper methods/classes at class level. The first chunk is the
    #    main method body; the rest is helpers.
    body = _ensure_java_body(java_body)
    body_l = body.lstrip()
    if body_l.startswith("public ") or body_l.startswith("private ") \
            or body_l.startswith("static ") or body_l.startswith("class "):
        # Style 2. Body is self-contained.
        pass
    else:
        # Check if there are helper methods in the body.
        has_helpers = (
            "\n    private " in ("\n" + body)
            or "\n    static " in ("\n" + body)
        )
        if has_helpers:
            # Style 3. Find the first helper line.
            lines = body.split("\n")
            split_idx = None
            for i, ln in enumerate(lines):
                if ln.lstrip().startswith("private ") \
                        or ln.lstrip().startswith("static class"):
                    split_idx = i
                    break
            if split_idx is not None:
                main_body = "\n".join(lines[:split_idx]).rstrip()
                # If main_body ends with `}`, drop it (we'll add our own).
                if main_body.rstrip().endswith("}"):
                    main_body = main_body.rstrip()[:-1].rstrip()
                helpers = "\n".join(lines[split_idx:]).rstrip()
                # If helpers are unbalanced (missing closing braces), add them.
                h_opens = helpers.count("{")
                h_closes = helpers.count("}")
                if h_opens > h_closes:
                    helpers = helpers + "\n" + ("    }" * (h_opens - h_closes))
                elif not helpers.rstrip().endswith("}"):
                    helpers = helpers + "\n    }"
                indented_main = "\n".join(
                    "    " + ln if ln.strip() else ln
                    for ln in main_body.split("\n")
                )
                body = f"    {sig} {{\n{indented_main}\n    }}\n\n{helpers}"
            else:
                # No helpers found despite has_helpers=True; fall back.
                indented = "\n".join(
                    "    " + ln if ln.strip() else ln
                    for ln in body.split("\n")
                )
                body = f"    {sig} {{\n{indented.rstrip()}\n    }}"
        else:
            # Style 1. Just the inside of the main method.
            opens = body.count("{")
            closes = body.count("}")
            # If the body has one too many closing `}` (the main method's
            # own closing brace, which the catalog often leaves in), strip
            # the last one.
            last_lines = [ln for ln in body.split("\n") if ln.strip()]
            if (closes > opens
                    and last_lines
                    and last_lines[-1].strip() == "}"
                    and last_lines[-1].startswith("    }")):
                # Remove the last "    }" line
                new_body_lines = body.split("\n")
                # Find and remove the last "    }"
                for j in range(len(new_body_lines) - 1, -1, -1):
                    if new_body_lines[j].strip() == "}" and new_body_lines[j].startswith("    }"):
                        del new_body_lines[j]
                        break
                body = "\n".join(new_body_lines)
                opens = body.count("{")
                closes = body.count("}")
            indented = "\n".join(
                "    " + ln if ln.strip() else ln
                for ln in body.split("\n")
            )
            if opens > closes:
                indented = indented.rstrip() + "\n" + ("    }" * (opens - closes))
            body = f"    {sig} {{\n{indented.rstrip()}\n    }}"
    content = f'''/** {p['name']}.
 *
 *  {module_label} - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/{p['slug']}/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {{
{java_helpers}
{body}

    public static void main(String[] args) {{
{tests_block}
    }}
}}
'''
    out.write_text(content)


def write_walkthrough(out: Path, p: dict, module_label: str) -> None:
    intuition = p['walkthrough'].strip()
    if intuition.startswith("## Intuition"):
        intuition = intuition[len("## Intuition"):].lstrip("\n")
    body = f"""# {p['name']} - walkthrough

**Difficulty:** {p['difficulty']} &middot; **Module:** {module_label}

## Brief

{p['brief']}

## Examples

"""
    body += "\n".join(f"- `{inp}` &rarr; `{outp}`" for inp, outp in p["examples"])
    body += "\n\n## Constraints\n\n"
    body += "\n".join(f"- {c}" for c in p["constraints"])
    body += f"\n\n## Intuition\n\n{intuition}\n\n## Reference solutions\n\n"
    body += "- [`solution.py`](./solution.py) - Python 3.10+\n"
    body += "- [`Solution.java`](./Solution.java) - Java 21\n"
    out.write_text(body)


# ====================================================================
# Main
# ====================================================================

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python _meta/gen_module.py <module_name>")
        sys.exit(1)
    meta_name = sys.argv[1]
    mod = importlib.import_module(f"_meta.{meta_name}")
    module_dir = module_dir_for(meta_name)
    if not module_dir.exists():
        print(f"module dir does not exist: {module_dir}")
        sys.exit(1)
    # module label derived from dir name (e.g. 01-arrays-hashing -> 01 Arrays & Hashing)
    n, rest = module_dir.name.split("-", 1)
    label = f"{n} {rest.replace('-', ' ').title()}"

    for p in mod.PROBLEMS:
        prob_dir = module_dir / "problems" / p["slug"]
        sol_dir = module_dir / "solutions" / p["slug"]
        prob_dir.mkdir(parents=True, exist_ok=True)
        sol_dir.mkdir(parents=True, exist_ok=True)
        write_problem_readme(prob_dir / "README.md", p)
        write_python_solution(
            sol_dir / "solution.py", p,
            p["py_sig"], p["py_body"], p["py_tests"],
        )
        write_java_solution(
            sol_dir / "Solution.java", p,
            p["java_sig"], p["java_body"], p["java_tests"],
            module_label=label,
        )
        write_walkthrough(sol_dir / "walkthrough.md", p, label)
    print(f"wrote {len(mod.PROBLEMS)} problems under {module_dir.name}/")


if __name__ == "__main__":
    main()
