# ⬡ Radar-Jrmy

![CI](https://github.com/Alt3k0/Radar-Jrmy/actions/workflows/ci.yml/badge.svg)
![Dernière collecte](https://github.com/Alt3k0/Radar-Jrmy/actions/workflows/collect.yml/badge.svg)

Radar technologique personnel pour suivre 20 technologies clés sur le chemin vers l'architecture logicielle.
Données collectées automatiquement toutes les 6h via GitHub Actions, hébergé sur GitHub Pages.

---

## Installation locale

```bash
pip install -r requirements-dev.txt
cp .env.example .env          # Ajouter GITHUB_TOKEN (optionnel)
python scripts/collect.py     # Génère data/data.json
python -m http.server 8080 --directory src
```

Ouvrir http://localhost:8080

## Ajouter une technologie

Éditer [`technologies.yaml`](technologies.yaml), puis :
```bash
python scripts/validate_yaml.py
```
Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) pour le guide complet.

## Architecture

Collecte Python (httpx async) → `data/data.json` (Git) → Site statique D3.js (GitHub Pages).
Zéro serveur, zéro base de données, historique des métriques dans Git.

## Roadmap

- **Phase 1 — Collecte** : sources GitHub / npm / PyPI / CNCF ✅
- **Phase 2 — Visualisation** : radar D3.js, tableau, éditeur ✅
- **Phase 3 — Backend** : API REST optionnelle pour historique long terme
