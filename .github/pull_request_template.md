## Summary

-

## Validation

- [ ] `python3 -m pytest`
- [ ] `python3 examples/generic_jsonl/run_demo.py`
- [ ] `python3 -m compileall -q citta_console examples`

## Safety checklist

- [ ] No shell execution inside runtime
- [ ] No deploy execution
- [ ] No git push execution inside runtime
- [ ] No delete/destructive execution
- [ ] Forbidden actions remain blocked by default
- [ ] Dangerous actions require confirmation
- [ ] No external API calls unless explicitly documented
- [ ] No secret handling added

## Documentation

- [ ] README/docs updated if behavior changed
- [ ] CHANGELOG updated for releases
- [ ] No real consciousness claim added

## Notes
