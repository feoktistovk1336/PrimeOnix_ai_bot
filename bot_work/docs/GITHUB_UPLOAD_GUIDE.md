# GitHub Upload Guide

## Before upload
Make sure these files are NOT in the repository:

- `.env`
- `data.db`
- `*.sqlite`
- `bot_errors.log`
- `generated_posts/*` except `.gitkeep`
- `venv/`, `.venv/`
- `__pycache__/`

## Upload steps

```bash
git init
git add .
git commit -m "Initial stable PrimeOnix AI bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## Check syntax before commit

```bash
python -m compileall .
```
