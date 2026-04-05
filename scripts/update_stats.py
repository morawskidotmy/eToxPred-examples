#!/usr/bin/env python3
"""
Update chemical statistics in README.md

Can be run locally or in CI to keep counts accurate.
"""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README_PATH = REPO_ROOT / "README.md"
TRAINING_DATA = REPO_ROOT / "training_data"
DB_PATH = REPO_ROOT / "site" / "chemicals.db"


def count_chemicals():
    """Count chemicals from various sources."""
    counts = {}
    
    # Count from training data files
    for smi_file in TRAINING_DATA.glob("*.smi"):
        with open(smi_file) as f:
            counts[smi_file.stem] = sum(1 for line in f if line.strip())
    
    # Count from database (deduplicated)
    db_count = 0
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        db_count = c.execute("SELECT COUNT(*) FROM chemicals").fetchone()[0]
        conn.close()
    
    # Map to display names
    category_counts = {
        "carcinogens": counts.get("carcinogens", 0),
        "endocrine_disruptors": counts.get("endocrine_disruptors", 0),
        "nootropics": counts.get("nootropics", 0),
        "psychoactive_drugs": counts.get("psychoactive_drugs", 0),
    }
    
    total_training = sum(category_counts.values())
    display_count = db_count if db_count > 0 else total_training
    display_rounded = int(round(display_count, -2))  # Round to nearest 100
    
    return {
        "db_count": db_count,
        "training_total": total_training,
        "display": display_rounded,
        "carcinogens": category_counts["carcinogens"],
        "endocrine_disruptors": category_counts["endocrine_disruptors"],
        "nootropics": category_counts["nootropics"],
        "psychoactive_drugs": category_counts["psychoactive_drugs"],
    }


def update_readme(counts):
    """Update README.md with current counts."""
    with open(README_PATH) as f:
        content = f.read()
    
    original = content
    
    # Update badge
    content = re.sub(
        r"chemicals-\d+%2B-blue",
        f"chemicals-{counts['display']}%2B-blue",
        content
    )
    
    # Update intro line "Browse X+ unique chemicals"
    content = re.sub(
        r"Browse [\d,]+\+ unique chemicals",
        f"Browse {counts['display']:,}+ unique chemicals",
        content
    )
    
    # Update feature line (allow for comma formatting)
    content = re.sub(
        r"\*\*[\d,]+\+ Chemical Compounds\*\*",
        f"**{counts['display']:,}+ Chemical Compounds**",
        content
    )
    
    # Update training entries count in features line
    content = re.sub(
        r"\([\d,]+\+? training entries,",
        f"({counts['training_total']:,} training entries,",
        content
    )
    
    # Update category counts in table
    content = re.sub(
        r"\| \*\*Nootropics\*\* \| [\d,]+ \|",
        f"| **Nootropics** | {counts['nootropics']:,} |",
        content
    )
    content = re.sub(
        r"\| \*\*Psychoactive Drugs\*\* \| [\d,]+ \|",
        f"| **Psychoactive Drugs** | {counts['psychoactive_drugs']:,} |",
        content
    )
    content = re.sub(
        r"\| \*\*Carcinogens\*\* \| [\d,]+ \|",
        f"| **Carcinogens** | {counts['carcinogens']:,} |",
        content
    )
    content = re.sub(
        r"\| \*\*Endocrine Disruptors\*\* \| [\d,]+ \|",
        f"| **Endocrine Disruptors** | {counts['endocrine_disruptors']:,} |",
        content
    )
    
    # Update file counts in project structure
    content = re.sub(
        r"carcinogens\.smi\s+# [\d,]+ known carcinogens",
        f"carcinogens.smi            # {counts['carcinogens']:,} known carcinogens",
        content
    )
    content = re.sub(
        r"endocrine_disruptors\.smi\s+# [\d,]+ endocrine disruptors",
        f"endocrine_disruptors.smi   # {counts['endocrine_disruptors']:,} endocrine disruptors",
        content
    )
    content = re.sub(
        r"nootropics\.smi\s+# [\d,]+ nootropic compounds",
        f"nootropics.smi             # {counts['nootropics']:,} nootropic compounds",
        content
    )
    content = re.sub(
        r"psychoactive_drugs\.smi\s+# [\d,]+ psychoactive substances",
        f"psychoactive_drugs.smi     # {counts['psychoactive_drugs']:,} psychoactive substances",
        content
    )
    
    if content != original:
        with open(README_PATH, 'w') as f:
            f.write(content)
        return True
    return False


def main():
    print("=" * 60)
    print("Updating Chemical Statistics")
    print("=" * 60)
    
    counts = count_chemicals()
    
    print("\nCurrent counts:")
    print(f"  Database (unique):      {counts['db_count']:,}")
    print(f"  Training (total):       {counts['training_total']:,}")
    print(f"  Display (rounded):      {counts['display']:,}+")
    print()
    print("By category:")
    print(f"  Carcinogens:           {counts['carcinogens']:,}")
    print(f"  Endocrine Disruptors:  {counts['endocrine_disruptors']:,}")
    print(f"  Nootropics:            {counts['nootropics']:,}")
    print(f"  Psychoactive Drugs:    {counts['psychoactive_drugs']:,}")
    
    print("\nUpdating README.md...")
    changed = update_readme(counts)
    
    if changed:
        print("✓ README.md updated")
    else:
        print("ℹ No changes needed")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
