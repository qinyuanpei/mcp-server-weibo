## [LRN-20260825-001] correction

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
The requested CLI output flags apply to `feeds`, not the similarly named `search` command.

### Details
The initial interpretation targeted content search. User feedback clarified that the feed-list command is the required scope.

### Suggested Action
Confirm the command named by the user before applying CLI-specific changes.

### Metadata
- Source: user_feedback
- Related Files: src/mcp_server_weibo/weibo_cli.py
- Tags: cli, scope

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Implemented the flags only on `weibo-cli feeds`.

---
