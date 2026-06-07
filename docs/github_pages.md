# GitHub Pages Setup

The v0.7 demo site lives in `docs_site/`.

## Option A: GitHub Pages from `docs_site` using GitHub Actions

1. Keep `.github/workflows/pages.yml` on `main`.
2. In GitHub, open repository settings.
3. Go to **Pages**.
4. Set **Source** to **GitHub Actions**.
5. Push or merge changes to `main`.
6. Open:

```text
https://nustanakritwithai.github.io/agent-citta-console/
```

The workflow uploads only static files from `docs_site/`.

## Option B: Manual Pages configuration

If you prefer not to use the workflow:

1. Remove or disable `.github/workflows/pages.yml`.
2. In GitHub, open repository settings.
3. Go to **Pages**.
4. Choose your preferred branch/folder setup.
5. Serve the contents of `docs_site/`.

## Local preview

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/docs_site/
```

## Safety

The Pages demo is static documentation only:

- no backend
- no external API calls
- no shell execution inside runtime
- no deploy/git push/delete runtime execution
- no secrets
- no real consciousness claim
