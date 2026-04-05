# GitHub Workflows

## update-stats.yml

Automatically updates chemical statistics in README.md when data changes.

### Triggers
- Push to `training_data/*.smi` files
- Push to `site/chemicals.db`
- Push to `etoxpred/custom_scores.csv`
- Manual trigger via workflow_dispatch

### What it updates
1. Badge count (`chemicals-XXXX+-blue`)
2. Feature line count
3. All 4 category counts in the table:
   - Nootropics
   - Psychoactive Drugs
   - Carcinogens
   - Endocrine Disruptors

### Smart behavior
- Uses database count when available (deduplicated)
- Falls back to training data count during rebuilds
- Rounds to nearest 100 for display
- Skips commit if no changes detected
- Uses `[skip ci]` to prevent infinite loops

### Manual use
```bash
# Run locally
python3 scripts/update_stats.py
```

## create-pr.yml

Creates PR from master to main branch automatically.
