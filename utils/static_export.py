"""Export evaluation results as a static site for GitHub Pages."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class StaticExporter:
    """Export evaluation dashboard as static HTML site."""

    def __init__(self, base_dir: Path | str = ".") -> None:
        self.base_dir = Path(base_dir)
        self.eval_results_dir = self.base_dir / "eval_results"
        self.issues_dir = self.base_dir / "issues"
        self.dashboard_file = self.base_dir / "dashboard.html"

    def export(self, output_dir: Path | str) -> bool:
        """
        Export static site to output directory.

        Args:
            output_dir: Target directory for static export

        Returns:
            True if export succeeded
        """
        output_path = Path(output_dir)
        print(f"📦 Exporting static dashboard to: {output_path}")
        print("=" * 60)

        try:
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Copy dashboard HTML
            if not self._copy_dashboard(output_path):
                return False

            # Step 2: Copy evaluation results
            if not self._copy_eval_results(output_path):
                return False

            # Step 3: Copy issues data
            if not self._copy_issues(output_path):
                return False

            # Step 4: Copy file index
            if not self._copy_file_index(output_path):
                return False

            # Step 5: Copy label descriptions
            self._copy_label_descriptions(output_path)

            # Step 6: Create .nojekyll for GitHub Pages
            self._create_nojekyll(output_path)

            # Step 7: Create README for GitHub Pages
            self._create_pages_readme(output_path)

            print("\n" + "=" * 60)
            print("✓ Static export completed successfully!")
            print(f"\n📁 Output directory: {output_path.absolute()}")
            print("\nTo deploy to GitHub Pages:")
            print("   1. Create a new repository or use existing one")
            print("   2. Copy contents of output directory to repository")
            print("   3. Enable GitHub Pages in repository settings")
            print("   4. Select 'Deploy from branch' → 'main' → '/ (root)'")
            print(f"   5. Your dashboard will be at: https://{{username}}.github.io/{{repo}}/")
            print("\nOr test locally:")
            print(f"   cd {output_path}")
            print("   python3 -m http.server 8000")
            print("   Open http://localhost:8000/dashboard.html")

            return True

        except Exception as exc:
            print(f"❌ Export failed: {exc}")
            return False

    def _copy_dashboard(self, output_dir: Path) -> bool:
        """Copy dashboard HTML file."""
        print("\n📄 Step 1: Copying dashboard HTML...")

        if not self.dashboard_file.exists():
            print(f"❌ Dashboard file not found: {self.dashboard_file}")
            return False

        target = output_dir / "dashboard.html"
        shutil.copy2(self.dashboard_file, target)

        # Also create index.html that redirects to dashboard
        index_html = output_dir / "index.html"
        index_html.write_text(
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<head>\n'
            '    <meta http-equiv="refresh" content="0; url=dashboard.html">\n'
            '    <title>Redirecting...</title>\n'
            '</head>\n'
            '<body>\n'
            '    <p>Redirecting to <a href="dashboard.html">dashboard</a>...</p>\n'
            '</body>\n'
            '</html>\n',
            encoding="utf-8"
        )

        print(f"   ✓ Copied dashboard.html")
        print(f"   ✓ Created index.html (redirect)")
        return True

    def _copy_eval_results(self, output_dir: Path) -> bool:
        """Copy evaluation results directory."""
        print("\nStep 2: Copying evaluation results...")

        if not self.eval_results_dir.exists():
            print(f"⚠️  No evaluation results found at {self.eval_results_dir}")
            print("   Creating empty directory...")
            (output_dir / "eval_results").mkdir(exist_ok=True)
            return True

        target = output_dir / "eval_results"
        if target.exists():
            shutil.rmtree(target)

        shutil.copytree(self.eval_results_dir, target)

        # Count files
        file_count = sum(1 for _ in target.rglob("*.json"))
        lang_count = len([d for d in target.iterdir() if d.is_dir()])

        print(f"   ✓ Copied {file_count} evaluation files from {lang_count} languages")
        return True

    def _copy_issues(self, output_dir: Path) -> bool:
        """Copy issues directory."""
        print("\n📋 Step 3: Copying issues data...")

        if not self.issues_dir.exists():
            print(f"⚠️  No issues found at {self.issues_dir}")
            print("   Creating empty directory...")
            (output_dir / "issues").mkdir(exist_ok=True)
            return True

        target = output_dir / "issues"
        if target.exists():
            shutil.rmtree(target)

        shutil.copytree(self.issues_dir, target)

        # Count files
        combined_count = len(list((target / "combined_issues").rglob("*.json"))) if (target / "combined_issues").exists() else 0
        patterns_count = len(list((target / "common_patterns").rglob("*.json"))) if (target / "common_patterns").exists() else 0

        print(f"   ✓ Copied {combined_count} combined issue files")
        print(f"   ✓ Copied {patterns_count} pattern analysis files")
        return True

    def _copy_file_index(self, output_dir: Path) -> bool:
        """Copy file index if it exists."""
        print("\nStep 4: Copying file index...")

        file_index = self.base_dir / "file_index.json"
        if not file_index.exists():
            print("   ⚠️  No file_index.json found, creating empty one...")
            target = output_dir / "file_index.json"
            target.write_text('{"files": []}', encoding="utf-8")
            return True

        target = output_dir / "file_index.json"
        shutil.copy2(file_index, target)
        print("   ✓ Copied file_index.json")
        return True

    def _copy_label_descriptions(self, output_dir: Path) -> None:
        """Copy label descriptions file if it exists."""
        print("\nStep 5: Copying label descriptions...")

        labels_file = self.base_dir / "labels_descriptions.json"
        if not labels_file.exists():
            print("   ⚠️  No labels_descriptions.json found, creating empty one...")
            target = output_dir / "labels_descriptions.json"
            target.write_text('{}', encoding="utf-8")
            return

        target = output_dir / "labels_descriptions.json"
        shutil.copy2(labels_file, target)
        print("   ✓ Copied labels_descriptions.json")

    def _create_nojekyll(self, output_dir: Path) -> None:
        """Create .nojekyll file to prevent Jekyll processing on GitHub Pages."""
        print("\n🔧 Step 6: Creating .nojekyll for GitHub Pages...")
        nojekyll = output_dir / ".nojekyll"
        nojekyll.touch()
        print("   ✓ Created .nojekyll")

    def _create_pages_readme(self, output_dir: Path) -> None:
        """Create README for GitHub Pages repository."""
        print("\nStep 7: Creating README...")

        readme_content = """# Localization Quality Dashboard

This is a static export of the Localization Quality Evaluation Dashboard.

## Viewing the Dashboard

Visit the GitHub Pages URL for this repository to view the interactive dashboard.

Or clone this repository and run locally:

```bash
python3 -m http.server 8000
# Open http://localhost:8000/dashboard.html
```

## What's Included

- **Dashboard** - Interactive HTML dashboard (`dashboard.html`)
- **Evaluation Results** - AI evaluation results from all languages (`eval_results/`)
- **Issues Data** - Aggregated issues and pattern analysis (`issues/`)
- **File Index** - Metadata about evaluated files (`file_index.json`)

## About

This dashboard provides visualization of localization quality evaluation results, including:
- Issue severity and category breakdown
- Cross-language pattern analysis
- Individual file evaluation scores
- Recurring error patterns

Generated with [Localization Quality Evaluation Tool](https://github.com/yourusername/your-repo)
"""

        readme = output_dir / "README.md"
        readme.write_text(readme_content, encoding="utf-8")
        print("   ✓ Created README.md")


__all__ = ["StaticExporter"]
