#!/usr/bin/env python3
"""
Validate translated HTML slides against en_US templates.
Checks for HTML parsing errors and structural differences.
Generates a report for manual fixes in Transifex.
"""

import os
import glob
from html.parser import HTMLParser
from collections import defaultdict
import json
import html as html_module


# ---------------- CONFIG ----------------
SLIDES_DIR = "live/desktop-provision/slides"
BASE_LOCALE = "en_US"
REPORT_FILE = "translation_validation_report.json"
HTML_REPORT_FILE = "translation_validation_report.html"
# ----------------------------------------


class HTMLStructureValidator(HTMLParser):
    """Extract HTML structure and validate parsing."""

    def __init__(self, html_content=None):
        super().__init__()
        self.tags = []
        self.errors = []
        self.attributes = defaultdict(list)
        self.tag_stack = []
        self.html_lines = html_content.split('\n') if html_content else []
        self.tag_positions = []  # Track (tag, line_num, line_content)

    def handle_starttag(self, tag, attrs):
        line_num, col = self.getpos()
        line_content = self.html_lines[line_num - 1] if line_num <= len(self.html_lines) else ""

        self.tags.append(tag)
        self.tag_stack.append({
            'tag': tag,
            'line': line_num,
            'content': line_content.strip()
        })
        self.tag_positions.append((tag, line_num, line_content.strip(), 'open'))

        for attr, value in attrs:
            self.attributes[tag].append(attr)

    def handle_endtag(self, tag):
        line_num, col = self.getpos()
        line_content = self.html_lines[line_num - 1] if line_num <= len(self.html_lines) else ""

        self.tag_positions.append((tag, line_num, line_content.strip(), 'close'))

        if self.tag_stack and self.tag_stack[-1]['tag'] == tag:
            self.tag_stack.pop()
        else:
            # More detailed error message
            if self.tag_stack:
                expected = self.tag_stack[-1]
                self.errors.append({
                    'type': 'mismatched_tag',
                    'tag': tag,
                    'line': line_num,
                    'line_content': line_content.strip(),
                    'expected': expected['tag'],
                    'expected_line': expected['line'],
                    'expected_content': expected['content']
                })
            else:
                self.errors.append({
                    'type': 'unexpected_close',
                    'tag': tag,
                    'line': line_num,
                    'line_content': line_content.strip()
                })

    def handle_data(self, data):
        # Just capture, don't validate content
        pass

    def get_structure(self):
        """Return a normalized structure representation."""
        unclosed = []
        for item in self.tag_stack:
            unclosed.append({
                'tag': item['tag'],
                'line': item['line'],
                'content': item['content']
            })

        return {
            'tags': self.tags,
            'attributes': dict(self.attributes),
            'unclosed_tags': unclosed,
            'errors': self.errors.copy(),
            'tag_positions': self.tag_positions
        }


def parse_html_structure(html_content):
    """Parse HTML and return structure + errors."""
    parser = HTMLStructureValidator(html_content)
    try:
        parser.feed(html_content)
    except Exception as e:
        parser.errors.append({
            'type': 'exception',
            'message': f"Parsing exception: {str(e)}"
        })

    return parser.get_structure()


def validate_slide(base_html, translated_html, slide_num, locale):
    """Compare translated slide against base slide structure."""
    issues = []

    base_structure = parse_html_structure(base_html)
    trans_structure = parse_html_structure(translated_html)

    # Check for parsing errors
    if trans_structure['errors']:
        for error in trans_structure['errors']:
            if isinstance(error, dict):
                if error['type'] == 'mismatched_tag':
                    issues.append({
                        'type': 'mismatched_tag',
                        'severity': 'high',
                        'message': f"Mismatched closing tag on line {error['line']}",
                        'details': {
                            'found': f"</{error['tag']}>",
                            'expected': f"</{error['expected']}>",
                            'line_number': error['line'],
                            'line_content': error['line_content'],
                            'expected_opened_at': f"Line {error['expected_line']}: {error['expected_content']}"
                        }
                    })
                elif error['type'] == 'unexpected_close':
                    issues.append({
                        'type': 'unexpected_close_tag',
                        'severity': 'high',
                        'message': f"Unexpected closing tag on line {error['line']}",
                        'details': {
                            'tag': f"</{error['tag']}>",
                            'line_number': error['line'],
                            'line_content': error['line_content'],
                            'problem': 'No matching opening tag found'
                        }
                    })
                else:
                    issues.append({
                        'type': 'parsing_error',
                        'severity': 'high',
                        'message': error.get('message', 'HTML parsing error'),
                        'details': error
                    })
            else:
                # Old string format
                issues.append({
                    'type': 'parsing_error',
                    'severity': 'high',
                    'message': 'HTML parsing errors detected',
                    'details': error
                })

    # Check for unclosed tags
    if trans_structure['unclosed_tags']:
        unclosed_details = []
        for unclosed in trans_structure['unclosed_tags']:
            if isinstance(unclosed, dict):
                unclosed_details.append({
                    'tag': f"<{unclosed['tag']}>",
                    'line_number': unclosed['line'],
                    'line_content': unclosed['content']
                })
            else:
                unclosed_details.append({'tag': f"<{unclosed}>"})

        issues.append({
            'type': 'unclosed_tags',
            'severity': 'high',
            'message': f"{len(trans_structure['unclosed_tags'])} unclosed HTML tag(s)",
            'details': unclosed_details
        })

    # Check if tag structure matches (allow some flexibility)
    base_tags = set(base_structure['tags'])
    trans_tags = set(trans_structure['tags'])

    missing_tags = base_tags - trans_tags
    if missing_tags:
        issues.append({
            'type': 'missing_tags',
            'severity': 'medium',
            'message': 'Missing HTML tags compared to base template',
            'details': list(missing_tags)
        })

    extra_tags = trans_tags - base_tags
    if extra_tags:
        issues.append({
            'type': 'extra_tags',
            'severity': 'low',
            'message': 'Additional HTML tags not in base template',
            'details': list(extra_tags)
        })

    # Check for significantly different tag counts
    if len(trans_structure['tags']) != len(base_structure['tags']):
        diff = abs(len(trans_structure['tags']) - len(base_structure['tags']))
        if diff > 2:  # Allow small variations
            issues.append({
                'type': 'tag_count_mismatch',
                'severity': 'medium',
                'message': f'Tag count differs significantly (base: {len(base_structure["tags"])}, translated: {len(trans_structure["tags"])})',
                'details': f'Difference: {diff} tags'
            })

    return issues


def validate_all_slides():
    """Validate all translated slides against en_US base."""
    validation_results = {}

    # Get all slide directories
    slide_dirs = sorted(glob.glob(os.path.join(SLIDES_DIR, "*")))

    for slide_dir in slide_dirs:
        if not os.path.isdir(slide_dir):
            continue

        slide_num = os.path.basename(slide_dir)
        base_file = os.path.join(slide_dir, f"slide_{BASE_LOCALE}.html")

        if not os.path.exists(base_file):
            print(f"Warning: Base file not found for slide {slide_num}")
            continue

        # Read base HTML
        with open(base_file, 'r', encoding='utf-8') as f:
            base_html = f.read()

        # Check all translations
        translated_files = glob.glob(os.path.join(slide_dir, "slide_*.html"))

        for trans_file in translated_files:
            filename = os.path.basename(trans_file)

            # Skip base locale
            if BASE_LOCALE in filename:
                continue

            # Extract locale code
            locale = filename.replace('slide_', '').replace('.html', '')

            # Read translated HTML
            with open(trans_file, 'r', encoding='utf-8') as f:
                trans_html = f.read()

            # Validate
            issues = validate_slide(base_html, trans_html, slide_num, locale)

            if issues:
                key = f"slide_{slide_num}_{locale}"
                validation_results[key] = {
                    'slide': slide_num,
                    'locale': locale,
                    'file': trans_file,
                    'issues': issues
                }

    return validation_results


def generate_json_report(results):
    """Generate JSON report of validation issues."""
    report = {
        'summary': {
            'total_files_checked': len(results),
            'files_with_issues': len(results),
            'high_severity': sum(1 for r in results.values()
                                for i in r['issues'] if i['severity'] == 'high'),
            'medium_severity': sum(1 for r in results.values()
                                  for i in r['issues'] if i['severity'] == 'medium'),
            'low_severity': sum(1 for r in results.values()
                               for i in r['issues'] if i['severity'] == 'low'),
        },
        'issues': results
    }

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nJSON report saved to: {REPORT_FILE}")
    return report


def generate_html_report(results):
    """Generate human-readable HTML report."""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Translation Validation Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #e95420;
            padding-bottom: 10px;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .summary-item {
            display: inline-block;
            margin-right: 30px;
            font-size: 16px;
        }
        .summary-item strong {
            color: #e95420;
        }
        .issue-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            background-color: #fff;
        }
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .slide-info {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .locale-badge {
            background-color: #e95420;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 14px;
        }
        .severity-high {
            background-color: #dc3545;
        }
        .severity-medium {
            background-color: #ffc107;
        }
        .severity-low {
            background-color: #28a745;
        }
        .issue-item {
            margin: 10px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #e95420;
            border-radius: 3px;
        }
        .issue-type {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            font-size: 16px;
        }
        .issue-details {
            margin-top: 10px;
            background-color: #fff;
            padding: 10px;
            border-radius: 3px;
            border: 1px solid #ddd;
        }
        .detail-row {
            margin: 5px 0;
            padding: 5px;
        }
        .detail-label {
            font-weight: bold;
            color: #555;
            display: inline-block;
            min-width: 150px;
        }
        .detail-value {
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .code-block {
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 10px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin: 10px 0;
            overflow-x: auto;
        }
        .line-number {
            color: #75715e;
            margin-right: 10px;
            user-select: none;
        }
        .file-path {
            color: #666;
            font-size: 12px;
            font-family: monospace;
        }
        .severity-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            color: white;
            margin-left: 10px;
        }
        .instructions {
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
        }
        .instructions h3 {
            margin-top: 0;
            color: #1976D2;
        }
        .error-highlight {
            background-color: #ffe6e6;
            border-left: 3px solid #dc3545;
            padding: 10px;
            margin: 10px 0;
        }
        .unclosed-list {
            list-style: none;
            padding: 0;
        }
        .unclosed-list li {
            padding: 8px;
            margin: 5px 0;
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Translation Validation Report</h1>
"""

    # Summary
    total = len(results)
    high = sum(1 for r in results.values() for i in r['issues'] if i['severity'] == 'high')
    medium = sum(1 for r in results.values() for i in r['issues'] if i['severity'] == 'medium')
    low = sum(1 for r in results.values() for i in r['issues'] if i['severity'] == 'low')

    html += f"""
        <div class="summary">
            <div class="summary-item"><strong>{total}</strong> files with issues</div>
            <div class="summary-item"><strong>{high}</strong> high severity</div>
            <div class="summary-item"><strong>{medium}</strong> medium severity</div>
            <div class="summary-item"><strong>{low}</strong> low severity</div>
        </div>

        <div class="instructions">
            <h3>How to Fix Issues</h3>
            <ol>
                <li>Review the issues below - each shows the <strong>exact line number</strong> and <strong>line content</strong> where the error occurs</li>
                <li>Go to Transifex and navigate to the specific resource (e.g., installer-3.slide-1)</li>
                <li>Find the language with issues and look for the line content shown below</li>
                <li>Fix the HTML structure errors - ensure all tags are properly closed and matched</li>
                <li>Save and re-run this validation script</li>
            </ol>
        </div>
"""

    # Sort by slide number then locale
    sorted_results = sorted(results.items(),
                          key=lambda x: (int(x[1]['slide']), x[1]['locale']))

    for key, data in sorted_results:
        slide = data['slide']
        locale = data['locale']
        file_path = data['file']
        issues = data['issues']

        html += f"""
        <div class="issue-card">
            <div class="issue-header">
                <div class="slide-info">Slide {slide}</div>
                <div class="locale-badge">{locale}</div>
            </div>
            <div class="file-path">{file_path}</div>
"""

        for issue in issues:
            severity_class = f"severity-{issue['severity']}"
            html += f"""
            <div class="issue-item">
                <div class="issue-type">
                    {issue['type'].replace('_', ' ').title()}
                    <span class="severity-badge {severity_class}">{issue['severity'].upper()}</span>
                </div>
                <div>{issue['message']}</div>
"""

            # Handle different detail formats
            if issue['details']:
                if isinstance(issue['details'], dict):
                    # New detailed format
                    html += '<div class="issue-details">'

                    for key, value in issue['details'].items():
                        label = key.replace('_', ' ').title()
                        # Escape HTML in the value
                        escaped_value = html_module.escape(str(value))
                        html += f'''
                        <div class="detail-row">
                            <span class="detail-label">{label}:</span>
                            <span class="detail-value">{escaped_value}</span>
                        </div>
'''

                    html += '</div>'

                elif isinstance(issue['details'], list):
                    # List of unclosed tags or errors
                    if issue['type'] == 'unclosed_tags':
                        html += '<div class="issue-details">'
                        html += '<ul class="unclosed-list">'
                        for item in issue['details']:
                            if isinstance(item, dict):
                                tag_escaped = html_module.escape(item.get('tag', 'Unknown'))
                                line_content_escaped = html_module.escape(item.get('line_content', 'N/A'))
                                html += f'''
                                <li>
                                    <strong>{tag_escaped}</strong><br>
                                    <span class="detail-label">Line {item.get('line_number', '?')}:</span>
                                    <code>{line_content_escaped}</code>
                                </li>
'''
                            else:
                                item_escaped = html_module.escape(str(item))
                                html += f'<li><code>{item_escaped}</code></li>'
                        html += '</ul></div>'
                    else:
                        # Other lists
                        escaped_list = ", ".join(html_module.escape(str(x)) for x in issue["details"])
                        html += f'<div class="issue-details"><code>{escaped_list}</code></div>'
                else:
                    # String details
                    escaped_details = html_module.escape(str(issue["details"]))
                    html += f'<div class="issue-details"><code>{escaped_details}</code></div>'

            html += """
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

    with open(HTML_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML report saved to: {HTML_REPORT_FILE}")


def main():
    print("Validating translated slides...")
    print(f"Base locale: {BASE_LOCALE}")
    print(f"Slides directory: {SLIDES_DIR}\n")

    results = validate_all_slides()

    if not results:
        print("✅ All translations are valid! No HTML structure issues found.")
        return

    print(f"\n⚠️  Found issues in {len(results)} translated files\n")

    # Generate reports
    generate_json_report(results)
    generate_html_report(results)

    print("\nValidation complete!")
    print(f"Open {HTML_REPORT_FILE} in a browser to view the full report.")


if __name__ == "__main__":
    main()
