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

1. **Create a text file with chemical names** (one per line):
```bash
echo "Morphine" > new_drugs.txt
echo "Codeine" >> new_drugs.txt
echo "Thebaine" >> new_drugs.txt
```

2. **Fetch SMILES from PubChem**:
```bash
python3 scripts/fetch_smiles.py new_drugs.txt training_data/new_drugs.smi
```

3. **Update the build script** to include your new category:
Edit `scripts/build_db.py` and add:
```python
CATEGORIES = {
    'nootropics.smi': 'nootropic',
    'carcinogens.smi': 'carcinogen',
    'endocrine_disruptors.smi': 'endocrine_disruptor',
    'psychoactive_drugs.smi': 'psychoactive',
    'new_drugs.smi': 'opioid',  # Add this line
}
```

4. **Rebuild the database**:
```bash
python3 scripts/build_db.py
```

5. **Reload the web interface** to see new chemicals

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

Process multiple chemical lists at once:

```bash
#!/bin/bash
# batch_fetch.sh

for category in stimulants depressants hallucinogens; do
    python3 scripts/fetch_smiles.py \
        sources/${category}.txt \
        training_data/${category}.smi
done

python3 scripts/build_db.py
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
- Clear browser cache and reload
- Check browser console for errors (F12)

### SMILES Fetch Failing
- PubChem API may be rate-limiting: increase sleep time in `fetch_smiles.py`
- Chemical name might be spelled incorrectly
- Try searching PubChem manually first to verify the compound exists

### Build Script Errors
- Ensure all `.smi` files are tab-separated (not spaces)
- Check that file paths in `CATEGORIES` dict match actual files
- Verify CSV files from etoxpred folder have correct headers

## Performance Tips

- Database loads in ~1-2 seconds with 4,000 compounds
- Searching is instant (client-side filtering)
- For very large datasets (>50k compounds), consider:
  - Server-side database with pagination
  - Indexed full-text search
  - Lazy loading of SMILES structures
