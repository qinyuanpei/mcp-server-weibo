## [ERR-20260825-001] git_status_safe_directory

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
Git commands fail because the workspace owner differs from the current execution user.

### Error
```
fatal: detected dubious ownership in repository at 'D:/Projects/mcp-server-weibo'
```

### Context
`git status --short` was used during code review. No Git configuration was changed.

### Suggested Fix
If Git history or status is needed, an authorized user can add this repository as a safe directory.

### Metadata
- Reproducible: yes
- Related Files: .git

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Continued with filesystem-based review and implementation.

---

## [ERR-20260825-004] github_actions_status_cli

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
GitHub CLI is unavailable in the local execution environment.

### Error
```
gh : The term 'gh' is not recognized
```

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Used the repository's public Actions page as the status-check fallback.

---

## [ERR-20260825-003] python310_tomllib_check

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An ad-hoc release version check used `tomllib`, which is not part of Python 3.10.

### Error
```
ModuleNotFoundError: No module named 'tomllib'
```

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Verified the version using the project files; retain Python 3.10 compatibility.

---

## [ERR-20260825-002] converter_refactor_import

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
Moving response converters removed a regular-expression import still required for visitor-cookie parsing.

### Error
```
NameError: name 're' is not defined
```

### Context
The error occurred while running offline tests after extracting converter functions from `weibo.py`.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Restored the import in `weibo.py`; full test suite rerun.

---
