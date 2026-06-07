# Release Checklist

1. Ensure main is up to date.
2. Run tests.
3. Run demo.
4. Run compileall.
5. Check safety constraints.
6. Update version in `pyproject.toml`.
7. Update `CHANGELOG.md`.
8. Merge PR.
9. Create tag/release.
10. Verify install from GitHub.

Recommended commands:

```bash
python3 -m pytest
python3 examples/generic_jsonl/run_demo.py
python3 -m compileall -q citta_console examples
```

Safety review:

- no external API calls
- no shell execution inside runtime
- no deploy/git push/delete runtime execution
- no secret handling
- no destructive actions by default
- no real consciousness claims
