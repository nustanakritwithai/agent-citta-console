# GitHub Pages Demo Site

This folder contains a static GitHub Pages-ready demo for
`agent-citta-console`.

Files:

- `index.html` - landing page and Body -> Trace -> Citta -> Action explanation
- `demo.html` - realistic demo explanation
- `style.css` - dependency-free styling

Preview locally:

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/docs_site/
```

This is a static documentation/demo site only. It does not run a backend, call
external APIs, or execute runtime actions.
