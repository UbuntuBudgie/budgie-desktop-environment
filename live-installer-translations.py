#!/usr/bin/env python3
"""
Enhanced translation management script with validation.
Pulls translations, validates HTML structure, and removes incomplete translations.
"""

import subprocess
import json
import os
import glob
from html.parser import HTMLParser
from collections import defaultdict
import html as html_module


# ---------------- CONFIG ----------------
THRESHOLD = 50  # % completion
TX_CMD = "tx"  # path to Transifex CLI
SLIDES_DIR = "live/desktop-provision/slides"
PROJECT_SLUG = "ubuntu-budgie"
RESOURCE_PREFIX = "installer-3.slide-"
TOTAL_SLIDES = 8
BASE_LOCALE = "en_US"
VALIDATION_REPORT = "translation_validation_report.html"
# ----------------------------------------


class HTMLStructureValidator(HTMLParser):
    """Extract HTML structure and validate parsing."""

    def __init__(self, html_content=None):
        super().__init__()
        self.tags = []
        self.errors = []
        self.tag_stack = []
        self.html_lines = html_content.split('\n') if html_content else []

    def handle_starttag(self, tag, attrs):
        line_num, col = self.getpos()
        line_content = self.html_lines[line_num - 1] if line_num <= len(self.html_lines) else ""

        self.tags.append(tag)
        self.tag_stack.append({
            'tag': tag,
            'line': line_num,
            'content': line_content.strip()
        })

    def handle_endtag(self, tag):
        line_num, col = self.getpos()
        line_content = self.html_lines[line_num - 1] if line_num <= len(self.html_lines) else ""

        if self.tag_stack and self.tag_stack[-1]['tag'] == tag:
            self.tag_stack.pop()
        else:
            if self.tag_stack:
                expected = self.tag_stack[-1]
                self.errors.append({
                    'tag': tag,
                    'line': line_num,
                    'line_content': line_content.strip(),
                    'expected': expected['tag'],
                    'expected_line': expected['line'],
                    'expected_content': expected['content']
                })
            else:
                self.errors.append({
                    'tag': tag,
                    'line': line_num,
                    'line_content': line_content.strip(),
                    'unexpected': True
                })

    def get_structure(self):
        unclosed = []
        for item in self.tag_stack:
            unclosed.append({
                'tag': item['tag'],
                'line': item['line'],
                'content': item['content']
            })

        return {
            'tags': self.tags,
            'unclosed_tags': unclosed,
            'errors': self.errors.copy()
        }


def validate_html(html_content):
    """Quick validation of HTML structure."""
    parser = HTMLStructureValidator(html_content)
    try:
        parser.feed(html_content)
    except Exception as e:
        parser.errors.append({
            'tag': 'exception',
            'line': 0,
            'line_content': str(e)
        })

    structure = parser.get_structure()
    has_errors = bool(structure['errors'] or structure['unclosed_tags'])

    return has_errors, structure


def pull_translations():
    """Pull all translations from Transifex"""
    print("Pulling all translations from Transifex...")
    # Uncomment to actually pull:
    subprocess.run([TX_CMD, "pull", "-a", "-f", "--mode=translator"], check=True)
    #print("(Skipped - uncomment in production)")


def get_languages_to_keep():
    """Query each slide via tx api to find languages meeting the threshold"""
    keep_languages = set()
    for i in range(1, TOTAL_SLIDES + 1):
        resource_slug = f"{RESOURCE_PREFIX}{i}"
        print(f"Checking translation percentages for {resource_slug}...")
        try:
            output = subprocess.check_output([TX_CMD, "api",
                                              f"/project/{PROJECT_SLUG}/resource/{resource_slug}/stats/"])
            stats = json.loads(output)
            for lang_code, info in stats.items():
                translated_pct = info.get("translated", 0)
                if translated_pct >= THRESHOLD:
                    keep_languages.add(lang_code)
        except subprocess.CalledProcessError as e:
            print(f"Warning: failed to get stats for {resource_slug}: {e}")
        except json.JSONDecodeError as e:
            print(f"Warning: could not parse JSON for {resource_slug}: {e}")

    print(f"Languages meeting threshold ({THRESHOLD}% on any slide): {sorted(keep_languages)}")
    return keep_languages


def validate_translations():
    """Validate HTML structure of all translations."""
    print("\nValidating HTML structure of translations...")

    validation_issues = {}
    slide_dirs = sorted(glob.glob(os.path.join(SLIDES_DIR, "*")))

    for slide_dir in slide_dirs:
        if not os.path.isdir(slide_dir):
            continue

        slide_num = os.path.basename(slide_dir)
        base_file = os.path.join(slide_dir, f"slide_{BASE_LOCALE}.html")

        if not os.path.exists(base_file):
            continue

        # Read base HTML
        with open(base_file, 'r', encoding='utf-8') as f:
            base_html = f.read()

        # Validate base HTML first
        base_has_errors, base_structure = validate_html(base_html)

        # Check all translations
        translated_files = glob.glob(os.path.join(slide_dir, "slide_*.html"))

        for trans_file in translated_files:
            filename = os.path.basename(trans_file)

            # Skip base locale
            if BASE_LOCALE in filename:
                continue

            locale = filename.replace('slide_', '').replace('.html', '')

            with open(trans_file, 'r', encoding='utf-8') as f:
                trans_html = f.read()

            has_errors, structure = validate_html(trans_html)

            if has_errors:
                key = f"slide_{slide_num}_{locale}"
                validation_issues[key] = {
                    'slide': slide_num,
                    'locale': locale,
                    'file': trans_file,
                    'errors': structure['errors'],
                    'unclosed_tags': structure['unclosed_tags']
                }

                print(f"  ⚠️  Slide {slide_num} / {locale}: HTML validation errors found")

    return validation_issues


def generate_validation_report(issues):
    """Generate HTML report for validation issues."""
    if not issues:
        print("✅ No HTML validation errors found!")
        return

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Translation HTML Validation Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #e95420;
            border-bottom: 3px solid #e95420;
            padding-bottom: 10px;
        }
        .summary {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        .issue {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            background-color: #f8f9fa;
        }
        .issue-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .slide-number {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .locale {
            background-color: #e95420;
            color: white;
            padding: 4px 12px;
            border-radius: 3px;
            font-size: 14px;
        }
        .file-path {
            color: #666;
            font-size: 13px;
            font-family: 'Courier New', monospace;
            margin-bottom: 10px;
        }
        .error-list {
            background-color: white;
            padding: 10px;
            border-left: 3px solid #dc3545;
            margin: 10px 0;
        }
        .error-item {
            background-color: #fff5f5;
            padding: 10px;
            margin: 8px 0;
            border-radius: 3px;
            border: 1px solid #ffcccc;
        }
        .error-detail {
            margin: 5px 0;
            font-size: 13px;
        }
        .error-label {
            font-weight: bold;
            color: #721c24;
            display: inline-block;
            min-width: 140px;
        }
        .error-value {
            font-family: 'Courier New', monospace;
            background-color: #fff;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #ddd;
        }
        .line-highlight {
            background-color: #ffe6e6;
            padding: 8px;
            margin: 5px 0;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .unclosed-list {
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }
        .unclosed-list li {
            padding: 10px;
            margin: 5px 0;
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
            border-radius: 3px;
        }
        .instructions {
            background-color: #d1ecf1;
            border-left: 4px solid #0c5460;
            padding: 15px;
            margin: 20px 0;
        }
        .instructions h2 {
            margin-top: 0;
            color: #0c5460;
        }
        .instructions ol {
            margin: 10px 0;
        }
        .instructions li {
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Translation HTML Validation Report</h1>

        <div class="summary">
            <strong>⚠️ {count} translation file(s) have HTML validation errors</strong>
            <p>These files need to be fixed in Transifex before they can be used.</p>
        </div>

        <div class="instructions">
            <h2>How to Fix These Issues</h2>
            <ol>
                <li><strong>Identify the issue:</strong> Review the errors below - each shows the <strong>exact line number</strong> and <strong>line content</strong></li>
                <li><strong>Go to Transifex:</strong> Navigate to https://www.transifex.com/ubuntu-budgie-dev/ubuntu-budgie/</li>
                <li><strong>Find the resource:</strong> Select "installer-3.slide-X" (where X is the slide number)</li>
                <li><strong>Select the language:</strong> Choose the language code shown below</li>
                <li><strong>Look for the line:</strong> Search for the line content shown in the error details</li>
                <li><strong>Fix HTML errors:</strong> Common issues:
                    <ul>
                        <li>Unclosed tags (e.g., &lt;p&gt; without &lt;/p&gt;)</li>
                        <li>Mismatched tags (e.g., &lt;td&gt;...&lt;/tr&gt; instead of &lt;/td&gt;)</li>
                        <li>Broken quotes or brackets</li>
                    </ul>
                </li>
                <li><strong>Re-run validation:</strong> Pull translations and run this script again</li>
            </ol>
        </div>
""".replace('{count}', str(len(issues)))

    # Sort by slide number
    sorted_issues = sorted(issues.items(),
                          key=lambda x: (int(x[1]['slide']), x[1]['locale']))

    for key, data in sorted_issues:
        html += f"""
        <div class="issue">
            <div class="issue-header">
                <div class="slide-number">Slide {data['slide']}</div>
                <div class="locale">{data['locale']}</div>
            </div>
            <div class="file-path">{data['file']}</div>
"""

        if data['errors']:
            html += """
            <div class="error-list">
                <strong>Parsing Errors:</strong>
"""
            for error in data['errors']:
                if isinstance(error, dict):
                    html += '<div class="error-item">'

                    if error.get('unexpected'):
                        tag_escaped = html_module.escape(error['tag'])
                        line_content_escaped = html_module.escape(error['line_content'])
                        html += f'''
                        <div class="error-detail">
                            <span class="error-label">Problem:</span>
                            <span class="error-value">Unexpected closing tag &lt;/{tag_escaped}&gt;</span>
                        </div>
                        <div class="error-detail">
                            <span class="error-label">Line {error['line']}:</span>
                        </div>
                        <div class="line-highlight">{line_content_escaped}</div>
                        <div class="error-detail">
                            <span class="error-label">Fix:</span> Remove this closing tag or add its opening tag earlier
                        </div>
'''
                    else:
                        tag_escaped = html_module.escape(error['tag'])
                        expected_escaped = html_module.escape(error.get('expected', 'unknown'))
                        line_content_escaped = html_module.escape(error['line_content'])
                        expected_content_escaped = html_module.escape(error.get('expected_content', 'N/A'))
                        html += f'''
                        <div class="error-detail">
                            <span class="error-label">Found:</span>
                            <span class="error-value">&lt;/{tag_escaped}&gt;</span>
                        </div>
                        <div class="error-detail">
                            <span class="error-label">Expected:</span>
                            <span class="error-value">&lt;/{expected_escaped}&gt;</span>
                        </div>
                        <div class="error-detail">
                            <span class="error-label">Line {error['line']}:</span>
                        </div>
                        <div class="line-highlight">{line_content_escaped}</div>
                        <div class="error-detail">
                            <span class="error-label">Expected opened at:</span>
                            Line {error.get('expected_line', '?')}: <code>{expected_content_escaped}</code>
                        </div>
'''
                    html += '</div>'
                else:
                    error_escaped = html_module.escape(str(error))
                    html += f'<div class="error-item">{error_escaped}</div>'

            html += """
            </div>
"""

        if data['unclosed_tags']:
            html += """
            <div class="error-list">
                <strong>Unclosed Tags:</strong>
                <ul class="unclosed-list">
"""
            for unclosed in data['unclosed_tags']:
                if isinstance(unclosed, dict):
                    tag_escaped = html_module.escape(unclosed['tag'])
                    content_escaped = html_module.escape(unclosed['content'])
                    html += f'''
                    <li>
                        <div><strong>Tag:</strong> <code>&lt;{tag_escaped}&gt;</code> was never closed</div>
                        <div><strong>Opened at Line {unclosed['line']}:</strong></div>
                        <div class="line-highlight">{content_escaped}</div>
                        <div><strong>Fix:</strong> Add <code>&lt;/{tag_escaped}&gt;</code> before the file ends</div>
                    </li>
'''
                else:
                    unclosed_escaped = html_module.escape(str(unclosed))
                    html += f'<li><code>&lt;{unclosed_escaped}&gt;</code></li>'

            html += """
                </ul>
            </div>
"""

        html += """
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    with open(VALIDATION_REPORT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n📄 Validation report saved to: {VALIDATION_REPORT}")
    print(f"   Open this file in a browser to see detailed issues and fix instructions")


def tidy_slides(keep_languages):
    """Remove slides for languages that are below threshold"""
    print("\nTidying up slides...")
    for slide_dir in glob.glob(os.path.join(SLIDES_DIR, "*")):
        if not os.path.isdir(slide_dir):
            continue
        for file_path in glob.glob(os.path.join(slide_dir, "slide_*.html")):
            filename = os.path.basename(file_path)
            parts = filename.split("_")
            if len(parts) != 2:
                continue
            lang_code = os.path.splitext(parts[1])[0]
            if lang_code != "en" and lang_code not in keep_languages:
                os.remove(file_path)
                print(f"Removed {file_path}")
    print("Done. Only languages meeting threshold are kept, with English preserved.")


def main():
    print("=" * 60)
    print("Translation Management & Validation")
    print("=" * 60)

    # Step 1: Pull translations
    pull_translations()

    # Step 2: Get languages that meet threshold
    keep_languages = get_languages_to_keep()

    # Step 3: Validate HTML structure
    validation_issues = validate_translations()

    # Step 4: Generate validation report if there are issues
    if validation_issues:
        generate_validation_report(validation_issues)
        print("\n" + "=" * 60)
        print("⚠️  VALIDATION ERRORS FOUND")
        print("=" * 60)
        print(f"Please fix the {len(validation_issues)} files with HTML errors in Transifex")
        print(f"See {VALIDATION_REPORT} for details")
        print("=" * 60)

    # Step 5: Tidy slides (remove incomplete translations)
    tidy_slides(keep_languages)

    print("\n✅ Translation management complete!")
    if validation_issues:
        print(f"⚠️  Note: {len(validation_issues)} files still have HTML validation errors")


if __name__ == "__main__":
    main()
