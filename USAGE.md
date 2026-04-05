# Usage Examples

## Quick Start

### 1. Browse the Database

```bash
# Open in browser
open site/index.html

# OR serve locally
cd site
python3 -m http.server 8000
# Visit: http://localhost:8000
```

### 2. Search for Chemicals

- Type in the search box: "caffeine", "aspirin", "DDT"
- Click category badges to filter by type
- Click column headers to sort by name, toxicity, etc.
- Use the guide (right sidebar) for score explanations

## Advanced Usage

### Adding New Chemicals

1. **Add chemical names to an existing category file**:
```bash
echo "Morphine\tCC1C2CC3=C(C1OC4=C2C(=C(C=C4)O)C2=C3C(=O)CCC2" >> training_data/psychoactive_drugs.smi
echo "Codeine\tCOC1=C(O)C=C2CC3C4C(CC2=C1)OC5=C4C(=CC(=C5)O)CC3" >> training_data/psychoactive_drugs.smi
```

2. **Rebuild everything**:
```bash
cd scripts

# Rebuild both models and database (full rebuild)
python3 rebuild_all.py

# Or rebuild only the database (faster, uses existing models)
python3 rebuild_all.py --db-only

# Or retrain only the models (skip database rebuild)
python3 rebuild_all.py --models-only
```

This will:
- Retrain all classification models
- Score all compounds (including new ones)
- Rebuild the SQLite database

### Querying the Database Directly

You can query the SQLite database using any SQL client:

```bash
# Using sqlite3 command line
sqlite3 site/chemicals.db

# Example queries:
SELECT name, tox_score FROM chemicals WHERE tox_score > 0.8 LIMIT 10;
SELECT COUNT(*) FROM chemicals WHERE category LIKE '%nootropic%';
SELECT name, smiles FROM chemicals WHERE name LIKE '%amphetamine%';
```

### Exporting Data

```bash
# Export all psychoactive compounds to CSV
sqlite3 -header -csv site/chemicals.db \
  "SELECT * FROM chemicals WHERE category LIKE '%psychoactive%'" \
  > psychoactive_export.csv

# Export high-toxicity compounds
sqlite3 -header -csv site/chemicals.db \
  "SELECT name, smiles, tox_score FROM chemicals WHERE tox_score > 0.7 ORDER BY tox_score DESC" \
  > high_toxicity.csv
```

### Batch Processing

Process multiple chemical lists at once by editing the `.smi` files in `training_data/`:

```bash
#!/bin/bash
# Add chemicals to existing categories
cat new_stimulants.smi >> training_data/psychoactive_drugs.smi
cat new_carcinogens.smi >> training_data/carcinogens.smi

# Rebuild everything
cd scripts && python3 rebuild_all.py
```

## Integration Examples

### Python Script

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('site/chemicals.db')
cursor = conn.cursor()

# Find all carcinogens with high toxicity
cursor.execute("""
    SELECT name, smiles, tox_score, carc_score 
    FROM chemicals 
    WHERE category LIKE '%carcinogen%' 
    AND tox_score > 0.6
    ORDER BY tox_score DESC
""")

for row in cursor.fetchall():
    print(f"{row[0]}: tox={row[2]:.2f}, carc={row[3]:.2f}")

conn.close()
```

### JavaScript (Node.js)

```javascript
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('site/chemicals.db');

db.all(
  'SELECT name, smiles FROM chemicals WHERE category LIKE ?',
  ['%nootropic%'],
  (err, rows) => {
    if (err) throw err;
    rows.forEach(row => {
      console.log(`${row.name}: ${row.smiles}`);
    });
  }
);

db.close();
```

## Troubleshooting

### Database Not Loading
- Check that `chemicals.db` exists in the `site/` folder
- Clear browser cache and reload (or press Shift+C in the interface)
- Check browser console for errors (F12)

### SMILES Format Issues
- Ensure `.smi` files are tab-separated: `SMILES<tab>Name`
- No empty lines between entries
- Use canonical SMILES from PubChem when possible

### Rebuild Script Errors
- Ensure all `.smi` files are tab-separated (not spaces)
- Run `python3 rebuild_all.py` from the `scripts/` directory
- Check that `etoxpred/custom_scores.csv` exists (created by training step)
- Verify CSV files from etoxpred folder have correct headers

## Performance Tips

- Database loads in ~1-2 seconds with 4,000 compounds
- Searching is instant (client-side filtering)
- For very large datasets (>50k compounds), consider:
  - Server-side database with pagination
  - Indexed full-text search
  - Lazy loading of SMILES structures
