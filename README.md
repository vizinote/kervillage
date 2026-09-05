# Kervillage — ton village en breton

Site statique gratuit : le nom breton de chaque commune de Bretagne historique,
sa lecture brique par brique, et un décodeur de panneaux.

- Production : https://kervillage.brozapi.com (GitHub Pages)
- Données : [vizinote/toponymie-bretonne](https://github.com/vizinote/toponymie-bretonne)
  (OpenStreetMap ODbL × Wikidata CC0), attributions détaillées sur la page « Sources et méthode ».

## Structure

- `index.html`, `decodeur.html`, `pourquoi.html`, `sources.html`, `mentions-legales.html` : pages principales
- `c/` : fiches statiques des 1 531 communes (générées)
- `d/` : pages des 5 départements (générées)
- `lieu.html` + `data/lieux-*.json` : fiches dynamiques des lieux-dits
- `data/search.json` : index de recherche (100 % navigateur)
- `assets/` : styles et scripts (recherche, partage canvas, fiches dynamiques)
- `content/` : textes éditoriaux (source des pages)
- `build/` : scripts de génération

## Régénérer le site

```bash
python3 build/build.py /chemin/vers/dataset.json
```

Le dataset provient du repo vizinote/toponymie-bretonne.
La carte des départements se régénère avec `build/geo.py` (télécharge le GeoJSON IGN/Etalab).

## Note lancement

Les pages portent `noindex, nofollow` tant que le lancement public n'a pas été validé
(verrou studio). Retirer la balise dans `build/build.py` (fonction `page`) au GO.
