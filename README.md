# Localization Quality Evaluation Tool

AI-powered tool for evaluating localization quality using GPT-4. Supports 11 languages with automated analysis, issue aggregation, and pattern detection.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Azure OpenAI
cp .env.example .env
# Edit .env with your credentials:
# ENDPOINT_URL=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-api-key
```

## Quick Start

```bash
# Full evaluation pipeline
python app.py eval spanish --label v1

# View results
python app.py dashboard
```

## Commands

### `eval` - Full Evaluation Pipeline
Auto-converts JSON → markdown, evaluates with AI, aggregates issues, analyzes patterns.

```bash
# Default (full evaluation)
python app.py eval spanish --label v1

# Content only (skip exercises)
python app.py eval spanish --label v1 --orchestrator contentonly

# Yes/no exercises only
python app.py eval spanish --label v1 --orchestrator yesnoevaluation
```

**Paths:** `raw_json_files/{language}/` → `markdown_files/{language}/` → `eval_results/{language}/`

---

### `convert` - Convert JSON to Markdown
```bash
python app.py convert spanish
python app.py convert spanish --orchestrator contentonly
```

**Paths:** `raw_json_files/{language}/` → `markdown_files/{language}/`

---

### `aggregate` - Aggregate Issues
```bash
python app.py aggregate spanish --label v1
```

**Paths:** `eval_results/{language}/` → `issues/combined_issues/{label}/{language}_issues.json`

---

### `analyze` - Analyze Patterns
```bash
python app.py analyze spanish --label v1
```

**Paths:** `issues/combined_issues/{label}/` → `issues/common_patterns/{label}/{language}.json`

---

### `file-index` - Update File Index
```bash
python app.py file-index
```

Scans `eval_results/` and updates `file_index.json` for dashboard.

---

### `dashboard` - View Results
```bash
python app.py dashboard
```

Opens at http://localhost:8083

---

### `export` - Export Static Site
```bash
python app.py export
python app.py export --output my-site
```

Exports to `docs/` for GitHub Pages.

---

### `clean` - Clean Files
```bash
# By language
python app.py clean eval_results --language spanish
python app.py clean markdown_files --language spanish

# All languages
python app.py clean eval_results --all

# By label (removes all data for that label)
python app.py clean eval_results --label v1
```

## Orchestrators

| Type | Evaluates | Use Case |
|------|-----------|----------|
| `fullevaluation` *(default)* | Lessons + all exercises | Full quality audit |
| `contentonly` | Lesson content only | Quick linguistic check |
| `yesnoevaluation` | Lessons + yes/no exercises | Binary question validation |

## Workflows

### Basic Evaluation
```bash
python app.py eval spanish --label v1
python app.py dashboard
```

### Multi-Language
```bash
for lang in spanish hebrew french; do
  python app.py eval $lang --label v2
done
python app.py file-index
python app.py dashboard
```

### Step-by-Step
```bash
python app.py convert spanish
python app.py eval spanish --label v1
python app.py aggregate spanish --label v1
python app.py analyze spanish --label v1
python app.py file-index
python app.py dashboard
```

## Directory Structure

```
raw_json_files/{language}/           # Input JSON files
markdown_files/{language}/           # Converted markdown
eval_results/{language}/             # Evaluation results
issues/
  ├── combined_issues/{label}/       # Aggregated issues
  ├── common_patterns/{label}/       # Pattern analysis
  └── all/all_common_issues.json     # Cross-label data
file_index.json                      # File metadata
```

## Supported Languages

english, spanish, polish, french, russian, german, portuguese, japanese, serbian, arabic, hebrew

## Help

```bash
python app.py -h                # All commands
python app.py <command> -h      # Command help
```

## Troubleshooting

**"No markdown files found"** → `eval` auto-converts, or run `python app.py convert {language}`

**Azure OpenAI errors** → Check `.env` has `ENDPOINT_URL` and `AZURE_OPENAI_API_KEY`

**Dashboard shows old data** → Run `python app.py file-index`

**Clean not working** → Ensure label matches exactly: check `file_index.json`
