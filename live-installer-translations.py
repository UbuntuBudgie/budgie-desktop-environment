#!/usr/bin/env python3
import subprocess
import json
import os
import glob

# ---------------- CONFIG ----------------
THRESHOLD = 50  # % completion
TX_CMD = "tx"  # path to Transifex CLI
SLIDES_DIR = "live/desktop-provision/slides"  # root folder containing slide subfolders
PROJECT_SLUG = "ubuntu-budgie"  # your Transifex project slug
RESOURCE_PREFIX = "installer-3.slide-"  # resource slug prefix in Transifex
TOTAL_SLIDES = 8
# ----------------------------------------

def pull_translations():
    """Pull all translations from Transifex"""
    print("Pulling all translations from Transifex...")
    #subprocess.run([TX_CMD, "pull", "-a", "-f", "--mode=translator"], check=True)

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

def tidy_slides(keep_languages):
    """Remove slides for languages that are below threshold"""
    print("Tidying up slides...")
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
    pull_translations()
    keep_languages = get_languages_to_keep()
    tidy_slides(keep_languages)

if __name__ == "__main__":
    main()
