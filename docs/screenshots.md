# Screenshot Instructions

The repository does not need binary screenshots for tests. Prefer generating
screenshots manually when preparing documentation or release notes.

## Generate the realistic demo dashboard

```bash
python3 examples/realistic_demo/run_demo.py
```

## Serve the repository locally

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/examples/realistic_demo/dashboard.html
```

Then capture the browser window with your operating system's screenshot tool.

## Optional image location

If a small screenshot is intentionally added later, place it under:

```text
docs/assets/
```

Keep screenshots lightweight and update README/docs links when adding them.

## Safety

The screenshot flow uses local fixture files only. It does not call external
APIs or execute shell, deploy, git push, or delete actions from the Citta
runtime.
