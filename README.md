# Chemical Database Browser

An interactive web-based database for exploring chemical compounds across multiple toxicological and pharmacological categories. Browse 3,000+ unique chemicals with SMILES notation, toxicity predictions, and custom classification scores.

![Chemical Database](https://img.shields.io/badge/chemicals-3000%2B-blue) ![Categories-4](https://img.shields.io/badge/categories-4-green)

## ⚠️ Disclaimer

**This database may contain classification errors.** The data was aggregated from multiple sources and some compounds may be incorrectly categorized. If you find a misclassified compound, please [open an issue](../../issues/new) with the compound name and the correct classification.

This is an experimental reference tool, not an authoritative source. Predictions are based on molecular structure pattern matching and have significant limitations. Do not base medical or safety decisions on this data alone.

## 🧪 Features

- **3,000+ Chemical Compounds** across 4 major categories (4,177 training entries, deduplicated by SMILES)
- **SMILES Notation** for each compound with molecular structure data
- **Toxicity Predictions** using EtoxPred model (tox-score & SA-score)
- **Custom Classification Scores** for carcinogenicity, psychoactivity, and endocrine disruption
- **Interactive Search & Filtering** with real-time results
- **Dark-Themed UI** optimized for readability
- **Sortable Columns** for easy data exploration
- **Static SQLite Database** - runs entirely client-side (via sql.js)

## 📂 Project Structure

```
chemical-database-repo/
├── site/
│   ├── index.html          # Main web interface
│   └── chemicals.db        # SQLite database with all chemical data
├── training_data/
│   ├── carcinogens.smi            # 806 known carcinogens
│   ├── endocrine_disruptors.smi   # 804 endocrine disruptors
│   ├── nootropics.smi             # 960 nootropic compounds
│   └── psychoactive_drugs.smi     # 1,607 psychoactive substances
├── etoxpred/
│   ├── custom_scores.csv   # Classification predictions
│   └── results_*.csv       # EtoxPred toxicity scores per category
└── README.md
```

## 🚀 Quick Start

Simply open `site/index.html` in any modern web browser. No server required - the entire database runs client-side using [sql.js](https://sql.js.org/).

```bash
# Option 1: Direct file
open site/index.html

# Option 2: Local server (optional)
cd site && python3 -m http.server 8000
# Visit http://localhost:8000
```

## 📊 Database Schema

The database contains a single `chemicals` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | TEXT | Chemical name (e.g., "Caffeine") |
| `smiles` | TEXT | SMILES notation (e.g., "CN1C=NC2=C1C(=O)N(C(=O)N2C)C") |
| `category` | TEXT | Comma-separated categories (nootropic, carcinogen, etc.) |
| `tox_score` | REAL | EtoxPred toxicity prediction (0-1, higher = more toxic) |
| `sa_score` | REAL | Synthetic accessibility score (0-1, normalized, higher = harder to synthesize) |
| `carc_score` | REAL | Carcinogenicity prediction (0-1) |
| `psych_score` | REAL | Psychoactivity prediction (0-1) |
| `endo_score` | REAL | Endocrine disruption prediction (0-1) |

## 📖 How It Works

### Web Interface (`site/index.html`)

A single-page application that runs entirely in the browser:

- **sql.js**: WebAssembly SQLite engine loads the database
- **No backend required**: Everything runs client-side
- **Real-time search**: Filters as you type
- **Sortable columns**: Click headers to sort
- **Category filtering**: Quick filtering by compound class
- **Score visualization**: Color-coded toxicity indicators

**Features:**
- Dark theme optimized for chemical data
- Responsive design (mobile-friendly)
- Inline help guide with scoring explanations
- Displays SMILES, categories, and all prediction scores

## 🧬 Training Data

### Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Nootropics** | 960 | Cognitive enhancers, smart drugs, memory supplements |
| **Psychoactive Drugs** | 1,607 | CNS-active compounds (stimulants, depressants, hallucinogens) |
| **Carcinogens** | 806 | Known or suspected cancer-causing agents |
| **Endocrine Disruptors** | 804 | Compounds that interfere with hormone systems |

### SMILES Format

All training data uses simplified molecular-input line-entry system (SMILES):

```
C1=CC=C(C=C1)O                          # Phenol
CN1C=NC2=C1C(=O)N(C(=O)N2C)C            # Caffeine
CC(C)CC1=CC=C(C=C1)C(C)C(=O)O           # Ibuprofen
```

- **Tab-separated values**: `SMILES<tab>Name`
- **Canonical SMILES** from PubChem ensures consistency
- Each compound appears once per category file
- Compounds may exist in multiple category files

## 🔬 Toxicity Scoring

### EtoxPred Scores

The database includes predictions from the [EtoxPred model](https://github.com/srijitseal/EtoxPred):

- **Tox-score** (0-1): Overall toxicity prediction
  - 0.0-0.3: Low toxicity (green)
  - 0.3-0.7: Moderate toxicity (yellow)
  - 0.7-1.0: High toxicity (red)

- **SA-score** (1-10): Synthetic accessibility
  - 1-3: Easy to synthesize
  - 4-7: Moderate difficulty
  - 8-10: Very difficult to synthesize

### Custom Classification Scores

Machine learning models trained on the labeled training data:

- **carc_score**: Carcinogenicity prediction (0-1)
- **psych_score**: Psychoactivity prediction (0-1)
- **endo_score**: Endocrine disruption prediction (0-1)

#### Training Methodology

Each classifier is trained as a binary one-vs-rest model:

1. **Features**: Morgan fingerprints (ECFP4, radius=2, 1024 bits) via RDKit
2. **Positives**: Compounds from the target category's `.smi` file
3. **Negatives**: ~4,900 FDA-approved drugs only (not compounds from other categories, to avoid label leakage)
4. **Balancing**: Negatives downsampled to 2:1 ratio vs positives
5. **Split**: 80/20 train/test with **scaffold split** (Murcko decomposition) to prevent structural leakage
6. **Model**: ExtraTreesClassifier (400 trees, min_samples_split=10, min_samples_leaf=3)
7. **Output**: Probability score (0-1) from `predict_proba`

Nootropics are **not used in training** (too heterogeneous) — they're only scored by the trained models.

#### Test Set Performance (Scaffold Split)

| Model | ROC-AUC | PR-AUC | Accuracy |
|-------|---------|--------|----------|
| Carcinogen | 0.92 | 0.91 | 76% |
| Psychoactive | 0.86 | 0.72 | 84% |
| Endocrine Disruptor | 0.82 | 0.69 | 82% |

Note: Recall on positives is moderate (42-53%) due to conservative predictions — the models favor precision over recall.

#### Known Limitations

- **Prodrugs invisible**: Structure-based fingerprints can't predict metabolic activation (e.g., 1,4-butanediol → GHB scores only 0.36 despite being psychoactive via metabolism)
- **Small training sets**: ~700-1100 positives per category limits generalization
- **FDA negatives bias**: Negatives are biased toward drug-like molecules

## 🛠️ Dependencies

### Runtime (Web Interface)
- None! Pure HTML/CSS/JavaScript
- sql.js loaded from CDN

### Retraining Models

The training script is in `scripts/`. Uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
cd scripts
uv sync
uv run python train_classifiers.py
```

Or with pip:
```bash
pip install rdkit scikit-learn pandas numpy joblib
python scripts/train_classifiers.py
```

## 📝 Data Sources

- **Chemical Names**: Curated from scientific literature, databases, and regulatory lists
- **SMILES Notation**: [PubChem](https://pubchem.ncbi.nlm.nih.gov/) REST API
- **Toxicity Predictions**: [EtoxPred](https://github.com/srijitseal/EtoxPred) (pre-trained model)
- **Classifications**: Labeled training data from multiple sources

## 🤝 Contributing

Contributions welcome! Ways to help:

1. **Add more chemicals**: Submit `.smi` files or chemical name lists
2. **Improve predictions**: Train better classification models
3. **Enhance UI**: Add visualizations, filters, or export features
4. **Documentation**: Add compound descriptions or sources

## 📄 License

- **Code**: GNU General Public License v3.0 - see [LICENSE](LICENSE)
- **Data**: Chemical structures from PubChem (public domain)
- **Models**: EtoxPred and custom classifiers are provided as-is for research use

## ⚠️ Disclaimer

This database is for **research and educational purposes only**. Toxicity predictions are computational estimates and should not be used for:
- Medical decision-making
- Regulatory compliance
- Consumer product safety assessments
- Legal or forensic purposes

Always consult authoritative sources (EPA, FDA, ECHA) and perform proper experimental validation for any toxicological or pharmacological claims.

## 🔗 Links

- [SMILES Notation](https://en.wikipedia.org/wiki/Simplified_molecular-input_line-entry_system)
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/)
- [EtoxPred](https://github.com/srijitseal/EtoxPred)
- [sql.js](https://sql.js.org/)

---

**Built with** 🧪 **chemistry** and ⚡ **code**
