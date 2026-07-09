# Changelog

## v0.10.0 - Redaction / Secret Masking

- Added best-effort redaction layer for trace events
- Masks Authorization headers, bearer tokens, API keys, passwords, cookies, private keys, and common token patterns
- Applies redaction before Hermes Citta Skill and runtime hook trace writes
- Added tests for nested metadata redaction
- Updated docs with safety guidance

## v0.9.0 - Hermes Runtime Trace Hook

- Added opt-in Hermes runtime trace hook
- Added environment-based hook config helper
- Added vipaka_check and command_result event mapping
- Added runtime hook demo
- Added tests and docs for controlled Hermes trace capture

## v0.8.1 - Hermes Citta Metadata Signals

- Added metadata support to Hermes Citta Skill trace writer methods
- Preserved confidence, goal_alignment, reason, inspected_error, and source_state in trace metadata
- Added tests for metadata-backed goal drift detection
- Improved Hermes skill docs for signal quality

## v0.8.0 - Installable Hermes Citta Skill

- Moved Hermes Citta Skill into the installable package
- Added citta-console hermes observe
- Added package import support for citta_console.skills.hermes_citta_skill
- Added CLI and packaging tests
- Kept skill experimental and non-executing

## v0.7.0 - GitHub Pages Demo

- Added static demo landing page
- Added GitHub Pages-ready docs site
- Added visual Body -> Trace -> Citta -> Action explanation
- Added live demo links and setup instructions

## v0.6.0 - Real Demo / Visual Proof

- Realistic UI refactor demo scenario
- Sample trace with test failure and risky continued edits
- Sample action history
- Generated static dashboard fixture
- Demo walkthrough and screenshot instructions
- README "See it in action" section
- 50 tests

## v0.4.0 - MCP Foundation

- Local MCP-style tools package
- CLI tool dispatcher
- stdio JSON-lines skeleton
- 50 tests

## v0.3.0 - Adapter Foundation

- Adapter base contract
- adapter registry
- generic/Hermes/Codex/Claude/OpenClaw local adapters
- 36 tests

## v0.2.0 - Live Console

- config system
- auto-refresh dashboard
- task detail page
- action history
- confirmation flow
- 28 tests

## v0.1.0 - MVP

- JSONL trace reader
- analyzer
- risk detector
- recommender
- HTML dashboard
- dispatcher
- 15 tests
