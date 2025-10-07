import shutil
from pathlib import Path

def export_static_dashboard(output_dir: str = "docs") -> bool:
    output_path = Path(output_dir)
    print(f"📦 Exporting static dashboard to: {output_path}")

    try:
        output_path.mkdir(parents=True, exist_ok=True)

        dashboard_file = Path("dashboard.html")
        if not dashboard_file.exists():
            print(f"❌ Dashboard file not found: {dashboard_file}")
            return False

        shutil.copy2(dashboard_file, output_path / "dashboard.html")

        (output_path / "index.html").write_text(
            '<!DOCTYPE html>\n<html>\n<head>\n'
            '    <meta http-equiv="refresh" content="0; url=dashboard.html">\n'
            '    <title>Redirecting...</title>\n</head>\n<body>\n'
            '    <p>Redirecting to <a href="dashboard.html">dashboard</a>...</p>\n'
            '</body>\n</html>\n',
            encoding="utf-8"
        )

        eval_results_dir = Path("eval_results")
        if eval_results_dir.exists():
            target = output_path / "eval_results"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(eval_results_dir, target)

        issues_dir = Path("issues")
        if issues_dir.exists():
            target = output_path / "issues"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(issues_dir, target)

        file_index = Path("file_index.json")
        if file_index.exists():
            shutil.copy2(file_index, output_path / "file_index.json")

        labels_file = Path("labels_descriptions.json")
        if labels_file.exists():
            shutil.copy2(labels_file, output_path / "labels_descriptions.json")

        (output_path / ".nojekyll").touch()

        print("✓ Static export completed successfully!")
        print(f"📁 Output directory: {output_path.absolute()}")
        return True

    except Exception as exc:
        print(f"❌ Export failed: {exc}")
        return False
