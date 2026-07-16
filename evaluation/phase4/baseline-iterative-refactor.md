# Baseline: Iterative Refactor (plain prompt, single session, NL control flow)

- Model: sonnet, general-purpose agent, no Libretto VM
- Cost: 105.1K tokens, 18 tool calls, 214s wall time
- Iterations actually performed: **1** (self-verified; first attempt passed)
- Prompt: see baseline-prompts.md, Task 1

## Key observation

The baseline expressed the loop ("if your fix has problems, try a different
approach — up to 2 times") as natural language in ONE session. It found the
same class of smell as the .libretto run (list-redaction gap in secret redaction),
proposed a fix, and **self-verified in a single iteration** — its first fix was
inherently safe (a localized `_redact_list_secrets` helper), so no retry fired.

Contrast with the .libretto run: there the fixer and tester were SEPARATE sessions
with independent context. The .libretto fixer's first approach (delegate logging.py
to security.py's helper) introduced a real regression, which the independent
tester caught, triggering the retry loop. The baseline's single agent verified
its own work — a weaker, non-adversarial check that happened to pass because the
fix was good, but structurally cannot catch a blind spot the author shares.

## Output

### Findings

**Location:** `packages/atp-core/atp/core/security.py`, function `redact_dict_secrets` (lines 1240–1281).

**Worst code smell: a security-control function that silently no-ops on a common data shape.** `redact_dict_secrets()` is the recursive secret-scrubber used by `log_security_event()` to sanitize `additional_data` before it's written to the audit log. Its list-handling branch only recurses into list items that are `dict` or `str`; any list-of-lists (a very ordinary JSON shape) is returned unmodified, so raw secrets nested one level deeper than a top-level list silently bypass redaction. Confirmed with a live repro against the real module:

```python
>>> redact_dict_secrets({'logs': [['api_key=AKIAABCDEFGHIJKLMNOP', 'note']]})
{'logs': [['api_key=AKIAABCDEFGHIJKLMNOP', 'note']]}   # NOT redacted
>>> redact_dict_secrets({'batches': [[{'password': 'hunter2'}]]})
{'batches': [[{'password': 'hunter2'}]]}               # NOT redacted
```

Not covered by any existing test (`TestDictRedaction` only exercises a list of dicts one level deep).

### Proposed minimal fix (diff, not applied — atp-platform is read-only)

```diff
--- a/packages/atp-core/atp/core/security.py
+++ b/packages/atp-core/atp/core/security.py
@@ -1266,17 +1266,29 @@ def redact_dict_secrets(data: dict[str, Any], max_depth: int = 5) -> dict[str,
         elif isinstance(value, dict):
             result[key] = redact_dict_secrets(value, max_depth - 1)
         elif isinstance(value, list):
-            result[key] = [
-                redact_dict_secrets(item, max_depth - 1)
-                if isinstance(item, dict)
-                else redact_secrets(item)
-                if isinstance(item, str)
-                else item
-                for item in value
-            ]
+            result[key] = _redact_list_secrets(value, max_depth - 1)
         else:
             result[key] = value

     return result
+
+
+def _redact_list_secrets(items: list[Any], max_depth: int) -> list[Any]:
+    """Recursively redact secrets from list items, including nested lists."""
+    if max_depth <= 0:
+        return items
+    redacted: list[Any] = []
+    for item in items:
+        if isinstance(item, dict):
+            redacted.append(redact_dict_secrets(item, max_depth - 1))
+        elif isinstance(item, list):
+            redacted.append(_redact_list_secrets(item, max_depth - 1))
+        elif isinstance(item, str):
+            redacted.append(redact_secrets(item))
+        else:
+            redacted.append(item)
+    return redacted
```

### Verification (1 fix/verify iteration — first attempt worked)

- Monkeypatched the real `atp.core.security` module in-process with the patched functions (using the real `redact_secrets`, so the actual `SECRET_PATTERNS` regexes ran).
- Full existing suite against the patch: `test_security.py`, `test_secret_patterns.py`, `test_cors_hardening.py` — **159/159 passed**, all four `TestDictRedaction` cases included.
- 3 new regression cases (nested list-of-lists with a raw secret; nested list-of-lists with a sensitive-key dict; deep nesting with max_depth=2) — all passed.

The fix is minimal, preserves the `max_depth` recursion-bounding contract, and changes no public signature.
