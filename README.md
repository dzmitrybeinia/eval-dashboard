# Localization Quality Evaluation Tool

A pluggable, orchestrator-based system for evaluating localization quality using AI. Supports multiple evaluation flows with different converters and orchestrators.

## Architecture

### Core Components

1. **Converters** - Transform JSON lessons into markdown format
   - `FullContentConverter` - Converts full lesson (content + questions)
   - `ContentOnlyConverter` - Converts only lesson content (intro + slides)
   - `YesNoConverter` - Converts only questions and feedback

2. **Orchestrators** - Configure evaluation pipeline behavior
   - `FullEvaluationOrchestrator` - Full evaluation (content + questions)
   - `ContentOnlyOrchestrator` - Content-only evaluation (linguistic focus)
   - `YesNoEvaluationOrchestrator` - Questions-only evaluation (with pattern analysis)

3. **Evaluator** - Runs AI-powered quality evaluation using Azure OpenAI (gpt-4.1)


### Prompt Files & Examples

#### `combined_expert.md` - Dual-expertise evaluation (linguistic + localization)
- **Used by:** `fullevaluation`
- **Evaluates:** Both language correctness AND cultural appropriateness
- **Categories:** `linguistic` and `localization`
- **Example prompt combination for Polish full evaluation:**
  ```
  [combined_expert.md content]

  ---

  [LANGUAGE-SPECIFIC RULES: Polish]
  [prompts/evaluation/languages/polish.md content]

  ---

  ## CONTENT FOR EVALUATION

  [Full lesson content with questions and feedback]
  ```

#### `linguistic_only.md` - Linguistic accuracy evaluation only
- **Used by:** `contentonly`, `yesnoevaluation`
- **Focuses on:** Grammar, spelling, syntax, word choice ONLY
- **Category:** `linguistic` only (no localization)
- **Example prompt combination for Russian content-only:**
  ```
  [linguistic_only.md content]

  ---

  [LANGUAGE-SPECIFIC RULES: Russian]
  [prompts/evaluation/languages/russian.md content]

  ---

  ## CONTENT FOR EVALUATION

  [Lesson content only - intro and slides, no questions]
  ```

- **Example prompt combination for Polish questions-only:**
  ```
  [linguistic_only.md content]

  ---

  [LANGUAGE-SPECIFIC RULES: Polish]
  [prompts/evaluation/languages/polish.md content]

  ---

  ## CONTENT FOR EVALUATION

  [Questions, statements, answers, and feedback only - no lesson content]
  ```

#### Language-specific rules (`prompts/evaluation/languages/*.md`)
- **Available for:** polish, russian, spanish, french, german, portuguese, japanese, serbian, arabic, hebrew, english
- **Contains:** Language-specific grammar rules, common patterns, morphology, syntax considerations
- **Automatically included** when evaluating respective language

## CLI Commands

### 1. Full Pipeline (`eval`)

Runs complete pipeline: convert → evaluate → aggregate → analyze

```bash
# Full evaluation (content + questions)
python app.py eval \
  --orchestrator fullevaluation \
  --from raw_json_files/polish \
  --to markdown_files/polish_full \
  --language polish \
  --label v1

# Content-only evaluation (linguistic focus)
python app.py eval \
  --orchestrator contentonly \
  --from raw_json_files/russian \
  --to markdown_files/russian_content \
  --language russian \
  --label content_v2

# Questions-only evaluation (with pattern analysis)
python app.py eval \
  --orchestrator yesnoevaluation \
  --from raw_json_files/polish \
  --to markdown_files/polish_questions \
  --language polish \
  --label questions_v1
```

### 2. Convert Only (`convert`)

Convert JSON to markdown without evaluation

```bash
python app.py convert \
  --orchestrator fullevaluation \
  --from raw_json_files/spanish \
  --to markdown_files/spanish_full \
  --language spanish
```

### 3. Evaluate Only (`evaluate`)

Evaluate existing markdown files

```bash
# Evaluate from existing markdown
python app.py evaluate \
  --orchestrator yesnoevaluation \
  --from markdown_files/polish_questions \
  --language polish \
  --label questions_v2

# Note: The evaluator appends language to path, so it looks for:
# markdown_files/polish_questions/polish/*.md
```

### 4. Aggregate Issues (`aggregate-issues`)

Combine individual evaluation results into common issues

```bash
python app.py aggregate-issues \
  --language polish \
  --label v1
```

### 5. Analyze Patterns (`analyze-patterns`)

Run pattern analysis on aggregated issues

```bash
python app.py analyze-patterns \
  --orchestrator yesnoevaluation \
  --language polish \
  --label v1
```

### 6. Dashboard (`dashboard`)

Serve web dashboard for viewing results locally

```bash
python app.py dashboard
# Opens at http://localhost:8084
```

### 7. Export Static (`export-static`)

Export dashboard as static HTML site for GitHub Pages hosting

```bash
# Export to default 'docs' directory
python app.py export-static

# Export to custom directory
python app.py export-static --output my-site

# The exported site includes:
# - dashboard.html (interactive dashboard)
# - index.html (redirects to dashboard)
# - eval_results/ (all evaluation JSON files)
# - issues/ (aggregated issues and patterns)
# - file_index.json (file metadata)
```

**Test locally before deploying:**
```bash
cd docs
python -m http.server 8000
# Open http://localhost:8000/
```

### 8. Clean (`clean`)

Clean generated files and directories

```bash
# Clean specific language
python app.py clean eval_results --language polish
python app.py clean markdown_files --language russian
python app.py clean raw_json_files --language spanish

# Clean all languages
python app.py clean eval_results --all
python app.py clean markdown_files --all

# Clean by label (eval_results only)
# Removes: eval files, combined_issues, common_patterns, and updates all_common_issues.json
python app.py clean eval_results --label v1
python app.py clean eval_results --label questions_v2
```

## Complete Workflow Examples

### Example 1: Full Lesson Evaluation

```bash
# 1. Convert and evaluate Polish lessons (full content + questions)
python app.py eval \
  --orchestrator fullevaluation \
  --from raw_json_files/polish \
  --to markdown_files/polish_v1 \
  --language polish \
  --label v1

# 2. View results in dashboard
python app.py dashboard

# 3. Clean up when done
python app.py clean eval_results --label v1
```

### Example 2: Content-Only Evaluation (Linguistic Focus)

```bash
# 1. Convert only lesson content (no questions)
python app.py convert \
  --orchestrator contentonly \
  --from raw_json_files/russian \
  --to markdown_files/russian_content \
  --language russian

# 2. Evaluate content for linguistic issues
python app.py evaluate \
  --orchestrator contentonly \
  --from markdown_files/russian_content \
  --language russian \
  --label content_v1

# 3. Aggregate issues
python app.py aggregate-issues \
  --language russian \
  --label content_v1

```

### Example 3: Questions-Only Evaluation with Pattern Analysis

```bash
# 1. Full pipeline: convert questions, evaluate, aggregate, analyze patterns
python app.py eval \
  --orchestrator yesnoevaluation \
  --from raw_json_files/polish \
  --to markdown_files/polish_questions \
  --language polish \
  --label questions_v1
```

### Example 4: Multi-Language Evaluation

```bash
# Evaluate multiple languages with same label
for lang in polish russian spanish; do
  python app.py eval \
    --orchestrator fullevaluation \
    --from raw_json_files/$lang \
    --to markdown_files/${lang}_v2 \
    --language $lang \
    --label v2
done

# View all results in dashboard
python app.py dashboard

# Clean all when done
python app.py clean eval_results --label v2
```

### Example 5: Re-evaluate Existing Markdown

```bash
# If you already have markdown files and want to re-run evaluation
python app.py evaluate \
  --orchestrator fullevaluation \
  --from markdown_files/polish_v1 \
  --language polish \
  --label v1_reeval

# Then aggregate and analyze
python app.py aggregate-issues --language polish --label v1_reeval
python app.py analyze-patterns --orchestrator fullevaluation \
  --language polish --label v1_reeval
```

## Directory Structure

```
.
├── raw_json_files/          # Input: JSON lesson files
│   ├── polish/
│   ├── russian/
│   └── spanish/
├── markdown_files/          # Generated: Markdown conversions
│   ├── polish_v1/
│   ├── russian_content/
│   └── polish_questions/
├── eval_results/            # Generated: Evaluation results
│   ├── polish/
│   ├── russian/
│   └── spanish/
├── issues/                  # Generated: Aggregated issues
│   ├── combined_issues/     # Per-label combined issues
│   │   ├── v1/
│   │   └── questions_v1/
│   ├── common_patterns/     # Per-label pattern analysis
│   │   ├── v1/
│   │   └── questions_v1/
│   └── all/                 # Cross-label aggregation
│       └── all_common_issues.json
├── core/                    # Core evaluation package
│   ├── evaluator.py         # Main evaluation logic
│   ├── aggregator.py        # Issue aggregation
│   ├── analyzer.py          # Pattern analysis
│   ├── scoring.py           # Quality scoring
│   └── models.py            # Data models
├── converters/              # Converter implementations
├── orchestrators/           # Orchestrator implementations
├── prompts/                 # AI prompts
└── utils/                   # Utility functions
```

## Configuration

### Azure OpenAI

Configure in `config/azure.py`:
- Model: `gpt-4.1`
- Endpoint and API key via environment variables

### Supported Languages

english, spanish, polish, french, russian, german, portuguese, japanese, serbian, arabic, hebrew

## Output Files

### Evaluation Results (`eval_results/<language>/`)
```json
{
  "issues": [...],
  "metadata": {
    "file": "World_Religions.md",
    "language": "Polish",
    "timestamp": "2025-10-04T22:45:45.289742",
    "model": "gpt-4.1",
    "label": "v1"
  },
  "scores": {...}
}
```

### Combined Issues (`issues/combined_issues/<label>/<language>_issues.json`)
All issues from evaluation aggregated by category and severity

### Common Patterns (`issues/common_patterns/<label>/<language>.json`)
AI-analyzed error patterns and recommendations

### All Common Issues (`issues/all/all_common_issues.json`)
Cross-label aggregation with label tracking

## Tips

1. **Use descriptive labels** - They help organize and track different evaluation runs
2. **Clean regularly** - Use `clean --label` to remove old evaluation data
3. **Separate concerns** - Use different orchestrators for different evaluation goals:
   - `contentonly` for linguistic quality
   - `yesnoevaluation` for question/feedback quality
   - `fullevaluation` for complete evaluation
4. **Check dashboard** - Visual overview of all evaluation results
5. **Pattern analysis** - Only runs with `yesnoevaluation` and `fullevaluation` orchestrators

## Troubleshooting

### "No markdown files found"
The evaluator appends language to the path. Ensure your markdown files are in:
`<from_path>/<language>/*.md`

### "Unknown orchestrator"
Check available orchestrators: `python -c "from app import discover_orchestrators; print(list(discover_orchestrators().keys()))"`

### Label not cleaning properly
Ensure the label in evaluation files matches exactly (check `metadata.label` in JSON)
