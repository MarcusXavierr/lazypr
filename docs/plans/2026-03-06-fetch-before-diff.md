# Fetch Remote Before Diff Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fetch the remote tracking branch before diffing so lazypr always compares against the actual remote HEAD, not a stale local cache.

**Architecture:** Add a `_fetch_remote_branch` helper to `diff.py` that silently runs `git fetch <remote> <branch>`. Call it inside `get_diff_remote` for each candidate ref that contains a `/` (i.e., is a remote ref, not the local fallback). Update existing tests to account for the new subprocess call.

**Tech Stack:** Python stdlib `subprocess`, `pytest`, `unittest.mock`

---

## Root Cause

`_remote_candidates` builds candidate refs from `git branch -r` (local cached tracking refs). These refs are only updated when the user runs `git fetch`. If the user's `upstream/main` (or `origin/main`) tracking ref is stale, `git diff upstream/main...HEAD` includes already-merged commits, making the AI describe work already in main.

---

### Task 1: Write failing tests for fetch behavior

**Files:**
- Modify: `tests/test_diff.py`

**Step 1: Add three new tests inside `TestGetDiffRemote`**

```python
def test_fetches_remote_before_diffing(self):
    """Should fetch from remote before running diff to get up-to-date tracking ref."""
    diff_output = "diff --git a/file.py b/file.py\n"
    branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
    fetch_result = MagicMock(returncode=0, stdout="")
    diff_result = MagicMock(returncode=0, stdout=diff_output)
    with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
        result = get_diff_remote("main")
        # Second call must be the fetch
        fetch_call = mock_run.call_args_list[1]
        assert fetch_call == call(
            ["git", "fetch", "origin", "main"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result == diff_output


def test_fetch_failure_is_ignored(self):
    """Should proceed with cached tracking ref when fetch fails (e.g. offline)."""
    diff_output = "diff --git a/file.py b/file.py\n"
    branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
    diff_result = MagicMock(returncode=0, stdout=diff_output)
    with patch("lazypr.diff.subprocess.run", side_effect=[
        branch_list,
        subprocess.CalledProcessError(1, "git fetch"),
        diff_result,
    ]):
        result = get_diff_remote("main")
        assert result == diff_output


def test_local_fallback_does_not_fetch(self):
    """Should not attempt a fetch when falling back to local branch ref."""
    diff_output = "diff --git a/file.py b/file.py\n"
    # No remote branches available → falls back to local 'main'
    branch_list = MagicMock(returncode=0, stdout="")
    diff_result = MagicMock(returncode=0, stdout=diff_output)
    with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, diff_result]) as mock_run:
        result = get_diff_remote("main")
        # Only two calls: branch_list + diff (no fetch for local ref)
        assert mock_run.call_count == 2
        assert result == diff_output
```

You also need `call` imported at the top of the test file:
```python
from unittest.mock import patch, MagicMock, call
```

**Step 2: Run new tests to verify they fail**

```bash
pytest tests/test_diff.py::TestGetDiffRemote::test_fetches_remote_before_diffing \
       tests/test_diff.py::TestGetDiffRemote::test_fetch_failure_is_ignored \
       tests/test_diff.py::TestGetDiffRemote::test_local_fallback_does_not_fetch -v
```

Expected: all three FAIL (fetch call doesn't exist yet).

---

### Task 2: Update existing `TestGetDiffRemote` tests to account for the new fetch call

The existing tests mock exactly N `subprocess.run` calls. Adding the fetch call will break them with `StopIteration` or wrong assertions.

**Files:**
- Modify: `tests/test_diff.py` — `TestGetDiffRemote` class

**Step 1: Update `test_returns_diff_from_remote_branch`**

The mock `side_effect` list currently has 2 items (`branch_list`, `diff_result`). Insert a `fetch_result` between them:

```python
def test_returns_diff_from_remote_branch(self):
    """Should return diff output comparing remote branch to HEAD."""
    diff_output = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
 def hello():
-    print("old")
+    print("new")
"""
    branch_list = MagicMock(returncode=0, stdout="  origin/main\n")
    fetch_result = MagicMock(returncode=0, stdout="")
    diff_result = MagicMock(returncode=0, stdout=diff_output)
    with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
        result = get_diff_remote("main")
        # Third call must be the diff
        diff_call = mock_run.call_args_list[2]
        assert diff_call == call(
            ["git", "diff", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result == diff_output
```

**Step 2: Update `test_uses_custom_remote`**

Same pattern — add `fetch_result` between `branch_list` and `diff_result`:

```python
def test_uses_custom_remote(self):
    """Should allow custom remote name."""
    branch_list = MagicMock(returncode=0, stdout="  upstream/main\n")
    fetch_result = MagicMock(returncode=0, stdout="")
    diff_result = MagicMock(returncode=0, stdout="diff output")
    with patch("lazypr.diff.subprocess.run", side_effect=[branch_list, fetch_result, diff_result]) as mock_run:
        result = get_diff_remote("main", remote="upstream")
        diff_call = mock_run.call_args_list[2]
        assert diff_call == call(
            ["git", "diff", "upstream/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result == "diff output"
```

**Step 3: Update `test_raises_error_when_remote_branch_missing`**

This test has `origin/other` (not `origin/main`) in branch list, so `origin/main` is NOT a candidate. It falls through to the local `main` fallback (no `/` → no fetch). But then `git diff main...HEAD` raises `CalledProcessError`. The mock currently has `[branch_list, CalledProcessError]`. Since local fallback has no fetch, call count stays the same:

```python
def test_raises_error_when_remote_branch_missing(self):
    """Should raise DiffError when no remote branch exists for base."""
    branch_list = MagicMock(returncode=0, stdout="  origin/other\n")
    with patch("lazypr.diff.subprocess.run", side_effect=[
        branch_list,
        subprocess.CalledProcessError(128, "git"),
    ]):
        with pytest.raises(DiffError) as exc_info:
            get_diff_remote("nonexistent-branch")
        assert "nonexistent-branch" in str(exc_info.value)
```

This test should not need changes — verify by running it.

**Step 4: Run all `TestGetDiffRemote` tests (they should still fail — fetch not implemented yet)**

```bash
pytest tests/test_diff.py::TestGetDiffRemote -v
```

Expected: the three new tests FAIL, existing tests may pass or fail depending on call count.

---

### Task 3: Implement `_fetch_remote_branch` and wire it into `get_diff_remote`

**Files:**
- Modify: `src/lazypr/diff.py`

**Step 1: Add `_fetch_remote_branch` helper** (insert after the `_remote_candidates` function, around line 86):

```python
def _fetch_remote_branch(remote: str, branch: str) -> None:
    """Fetch a branch from a remote to update the local tracking ref.

    Silently ignores errors so callers proceed with the cached ref when
    offline or when the remote does not have the branch.
    """
    try:
        subprocess.run(
            ["git", "fetch", remote, branch],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        pass
```

**Step 2: Call `_fetch_remote_branch` inside `get_diff_remote`**

In `get_diff_remote`, the loop currently looks like:

```python
for ref in candidates:
    try:
        result = subprocess.run(...)
        return result.stdout
    except subprocess.CalledProcessError:
        continue
```

Change it to:

```python
for ref in candidates:
    if "/" in ref:
        remote_name = ref.split("/")[0]
        _fetch_remote_branch(remote_name, base)
    try:
        result = subprocess.run(
            ["git", "diff", f"{ref}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        continue
```

The `if "/" in ref` check distinguishes remote refs (`upstream/main`) from the local fallback (`main`).

**Step 3: Run all tests**

```bash
pytest tests/test_diff.py -v
```

Expected: all pass.

**Step 4: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/lazypr/diff.py tests/test_diff.py
git commit -m "fix: fetch remote branch before diffing to avoid stale tracking refs"
```
