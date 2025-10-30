# Developer Guide - Eval Dashboard

## What This System Does

This system evaluates educational quiz content in multiple languages. It helps find errors in translations, quiz questions, and educational materials.

## Architecture Diagram

```
┌─────────────────┐
│  JSONL File     │  (Input)
│  lessons.jsonl  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BaseConverter  │  (Reads all lessons)
│  _load_lessons()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  For each of    │  (Loop: N times)
│  N lessons      │
└────────┬────────┘
         │
         ├──────────────────────┬──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ LZFullContent   │    │ LZLesson        │    │ LZQuiz          │
│ Converter       │    │ Converter       │    │ Converter       │
│ (Content+Quiz)  │    │ (Content only)  │    │ (Quiz only)     │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Lesson_1.md    │    │  Lesson_1.md    │    │  Lesson_1.md    │
│  Lesson_2.md    │    │  Lesson_2.md    │    │  Lesson_2.md    │
│  ... (N files)  │    │  ... (N files)  │    │  ... (N files)  │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Evaluator      │  (For each .md file)
                       │  evaluate_file()│
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Orchestrator   │  (Builds AI prompt)
                       │  get_prompt()   │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      LLM        │  (Finds issues)
                       │  N API calls    │  (One per lesson)
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Save Results   │  (N JSON files)
                       │ evaluation*.json│
                       └─────────────────┘
```

### Simple Overview

1. **Input**: JSON files with quiz lessons (in different languages)
2. **Process**: Convert to markdown → Send to AI → Get quality reports
3. **Output**: Lists of issues and quality scores

---

## How The System Works

### Step 1: Convert (JSON → Markdown)

**What happens:**
- Reads JSONL files
- Each lesson becomes its own markdown file
- Markdown files are easier for AI to read

**Example:**
```
spanish/lessons.jsonl (1 file, 15 lessons)
    ↓
spanish/Lesson_1.md
spanish/Lesson_2.md
spanish/Lesson_3.md
... (15 separate files)
```

### Step 2: Evaluate (Markdown → AI → Issues)

**What happens:**
- Reads each markdown file (one lesson)
- Sends it to LLM
- AI finds translation errors, grammar mistakes, quiz problems
- Saves results as JSON

**Example:**
```
Lesson_1.md
    ↓
Send to LLM → "Find translation errors in this Spanish quiz"
    ↓
evaluation_Lesson_1.json (list of issues found)
```

### Step 3: Analyze (Issues → Patterns)

**What happens:**
- Combines all issue reports
- Finds common problems
- Creates summary statistics

---

## Three Types of Evaluations

### 1. Full Evaluation (`lzfull`)
- **What it checks:** Lesson content + all quiz questions
- **Use when:** You want to check everything
- **Example:** Check if Spanish lesson about animals has good content AND good quiz questions

### 2. Lesson Only (`lzlesson`)
- **What it checks:** Only the lesson content (no quizzes)
- **Use when:** You only care about the educational text, not the questions
- **Example:** Check if the science explanations are accurate

### 3. Quiz Only (`lzquiz`)
- **What it checks:** Only the quiz questions (no lesson content)
- **Use when:** You only care about question quality
- **Example:** Check if quiz questions are clear and have correct answers

---

## Supported Quiz Types

The system understands 8 different quiz formats:

1. **YesNo** - True/False questions
2. **DynamicQuiz** - Multiple choice questions
3. **FillInTheBlanks** - Fill-in-the-blank questions
4. **KahootQuiz** - Multiple choice with images
5. **OpenEnded** - Free text answer questions
6. **Match** - Match pairs together
7. **Sort** - Put items in order
8. **Group** - Group items into categories

---

## Installation

### 1. Install Python
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Setup API Keys

Create a file named `.env` in the project folder:

```
ENDPOINT_URL=https://your-azure-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
API_VERSION=2025-01-01-preview
```

**How to get these:**
- You need an Azure OpenAI account
- Get endpoint URL and API key from Azure portal

---

## Basic Commands

### Convert Files

**Convert with full content (lessons + quizzes):**
```bash
python app.py convert spanish
```

**Convert only lessons:**
```bash
python app.py convert spanish --orchestrator lzlesson
```

**Convert only quizzes:**
```bash
python app.py convert spanish --orchestrator lzquiz
```

### Evaluate Files

**Evaluate everything:**
```bash
python app.py eval spanish --label v1
```

**Evaluate only lessons:**
```bash
python app.py eval spanish --label v1 --orchestrator lzlesson
```

**Evaluate only quizzes:**
```bash
python app.py eval spanish --label v1 --orchestrator lzquiz
```

### Other Commands

**See issues dashboard:**
```bash
python app.py dashboard
```

**Clean up old files:**
```bash
python app.py clean markdown --language spanish
python app.py clean eval_results --language spanish
```

---

## File Organization

```
eval-dashboard/
├── raw_json_files/         # Input: Original quiz files
│   ├── spanish/
│   │   └── lessons.jsonl   
│   ├── french/
│   └── german/
│
├── markdown_files/         # Converted: Easy to read format
│   ├── spanish/
│   │   ├── Lesson_1.md     
│   │   ├── Lesson_2.md
│   │   └── ...
│   └── french/
│
├── eval_results/           # Output: AI evaluation results
│   ├── spanish/
│   │   ├── evaluation_Lesson_1.json
│   │   ├── evaluation_Lesson_2.json
│   │   └── ...
│   └── french/
│
├── issues/                 # Analysis: Common patterns
│   ├── combined_issues/
│   └── common_patterns/
│
├── converters/             # Code: JSON → Markdown
├── orchestrators/          # Code: Controls evaluation type
└── core/                   
```

---

## Supported Languages

- English
- Spanish
- Polish
- French
- Russian
- German
- Portuguese
- Japanese
- Serbian
- Arabic
- Hebrew

---

## How to Add a New Language

1. Create folders:
```bash
mkdir raw_json_files/italian
mkdir markdown_files/italian
mkdir eval_results/italian
```

2. Add language to config:

Edit `config/languages.py`:
```python
SUPPORTED_LANGUAGES = [
    "english", "spanish", "french", "italian"  # Add italian
]
```

3. (Optional) Add language-specific rules:

Create `prompts/evaluation/languages/italian.md` with special rules for Italian

4. Run conversion:
```bash
python app.py convert italian
```

---

## How to Add a New Quiz Type

### Example: Adding "Crossword" quiz type

1. **Update LZ Full Content Converter**

Edit `converters/lz_full_content_converter.py`:

```python
def _slides_to_markdown(self, slides, md_lines, sections):
    for obj in quiz_objects:
        quiz_type = obj.get("type")
        content = obj.get("generatedContent", {})

        if quiz_type == "YesNo":
            self._add_yes_no(md_lines, content)
        # ... other types ...
        elif quiz_type == "Crossword":  # NEW TYPE
            self._add_crossword(md_lines, content)
```

2. **Add the format method**

```python
def _add_crossword(self, md_lines: List[str], content: Dict) -> None:
    clues = content.get("clues", [])

    md_lines.append("## Crossword")
    md_lines.append("")

    if clues:
        md_lines.append("**Clues:**")
        for clue in clues:
            md_lines.append(f"- {clue}")
        md_lines.append("")
    md_lines.append("")
```

3. **Update Quiz Converter**

Do the same in `converters/lz_quiz_converter.py`

4. **Test it**
```bash
python app.py convert spanish --orchestrator lzfull
```

---

## Understanding Orchestrators

Orchestrators control **what gets evaluated** and **how**.

### What they do:
1. Pick which converter to use (full, lesson-only, quiz-only)
2. Choose which AI prompt to use
3. Decide if issues should be combined

### The three orchestrators:

`lzfull`  - Full content: Lesson text + ALL 8 quiz types (DynamicQuiz, FillInTheBlanks, YesNo, KahootQuiz, OpenEnded, Match, Sort, Group)

`lzlesson` - Lesson content only (no quizzes)

`lzquiz` -Quiz questions only (all 8 types, no lesson content)

---

## Understanding the Evaluation Flow

```
1. You run: python app.py eval spanish --label v1

2. System checks: Do markdown files exist?
   - NO → Auto-converts JSON to markdown first
   - YES → Continues

3. For each markdown file (lesson):
   a. Read the lesson content
   b. Load the AI prompt template
   c. Combine: prompt + lesson content
   d. Send to LLM
   e. Get back: list of issues
   f. Save as JSON

4. After all lessons evaluated:
   a. Combine all issues from all lessons
   b. Find common patterns
   c. Generate statistics

5. Done! Results saved in eval_results/spanish/
```

---

## Common Tasks

### Task 1: Check Spanish translations

```bash
# Convert Spanish lessons
python app.py convert spanish

# Evaluate them
python app.py eval spanish --label translation_check

# View results
python app.py dashboard
```

### Task 2: Only check quiz questions in French

```bash
# Convert only quizzes
python app.py convert french --orchestrator lzquiz

# Evaluate only quizzes
python app.py eval french --label quiz_check --orchestrator lzquiz
```

### Task 3: Re-evaluate after fixing issues

```bash
# Clean old results
python app.py clean eval_results --language spanish

# Run new evaluation
python app.py eval spanish --label v2
```

---

## Tips for Developers

### Good Practices

1. **Always use labels** - Helps track different evaluation runs
   ```bash
   python app.py eval spanish --label before_fixes
   python app.py eval spanish --label after_fixes
   ```

2. **Test one language first** - Don't process all languages at once
   ```bash
   python app.py convert spanish  # Test with one language
   ```

3. **Check markdown files** - Before evaluating, look at the markdown to make sure conversion worked
   ```bash
   cat markdown_files/spanish/some_lesson.md
   ```

4. **Use the right orchestrator** - Pick based on what you want to check
   - Full content? Use `lzfull`
   - Just text? Use `lzlesson`
   - Just quizzes? Use `lzquiz`

### Troubleshooting

**Problem: "No markdown files found"**
- Run convert first: `python app.py convert spanish`

**Problem: "API key error"**
- Check your `.env` file exists
- Check the API key is correct

**Problem: "Conversion failed"**
- Check the JSONL file format (one JSON object per line)
- Check the file is in the right folder (raw_json_files/language/)

**Problem: "Unicode errors in console"**
- This is just a display issue
- Files are still created correctly
- Check markdown_files/ folder

---
