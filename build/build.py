#!/usr/bin/env python3
"""Build du site statique Kervillage (kervillage.brozapi.com).

Sources :
- content/decodeur.md, content/pourquoi.md, content/sources.md (redacteur, carte t_88a3c583)
- dataset toponymie-bretonne (carte t_006bf6ba) : chemin passe en argument ou KERVILLAGE_DATASET
- build/carte.json (geo.py), build/telephone.html (extrait des mentions legales AccessiCheck)

Sortie : fichiers statiques a la racine du repo (GitHub Pages).
"""
import html
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "KERVILLAGE_DATASET", "/opt/data/breton-dataset/dataset.json")
SITE_URL = "https://kervillage.brozapi.com"
SITE_NAME = "Kervillage"
TAGLINE = "ton village en breton"

DEPT_NOMS = {"22": "Côtes-d'Armor", "29": "Finistère", "35": "Ille-et-Vilaine",
             "44": "Loire-Atlantique", "56": "Morbihan"}
TYPE_LABELS = {"commune": "Commune", "town": "Ville", "village": "Village", "hamlet": "Lieu-dit"}

# ---------------------------------------------------------------- pliage

def fold(s):
    if not s:
        return ""
    s = s.replace("œ", "oe").replace("æ", "ae").replace("’", "'")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().replace("'", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def nb(n):
    """1 531 — separateur de milliers francais (espace fine)."""
    return f"{n:,}".replace(",", " ")

# ---------------------------------------------------------------- markdown minimal

def md_inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_blocks(md):
    """Convertit le markdown simple des contenus (h1/h2, listes, paragraphes)."""
    out, in_list = [], False
    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            title = line[3:].strip()
            out.append(f'<h2 id="{fold(title)}">{md_inline(title)}</h2>')
        elif line.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h1>{md_inline(line[2:].strip())}</h1>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{md_inline(line[2:].strip())}</li>")
        elif line.strip() == "---":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{md_inline(line.strip())}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)

# ---------------------------------------------------------------- decodeur -> briques

SHORT_GLOSS = {
    "plou": "paroisse", "ker": "village, lieu habité", "lan": "ermitage, terre consacrée",
    "tre": "trève", "loc": "lieu consacré", "gwik": "bourg", "gwen": "blanc",
    "sant": "saint", "pen": "tête, bout", "ros": "tertre", "poull": "mare, creux d'eau",
    "coat": "bois, forêt", "bod": "demeure", "moustoir": "monastère", "pont": "pont",
    "aber": "estuaire", "menez": "mont", "beg": "pointe", "kemper": "confluent",
    "kastell": "château", "iliz": "église", "mael": "prince, chef", "meur": "grand",
    "nevez": "neuf", "march": "cheval", "ac": "domaine de…", "ach": "domaine de…",
    "venez": "île", "an-ar": "article « le, la »", "bro": "pays",
}
PROBABLE = {"ros", "mael", "ach"}  # etymologies debattues (carte redacteur)
PREFIX_ANCHORS = ["plou", "ker", "lan", "tre", "loc", "gwik", "gwen", "sant", "pen",
                  "ros", "poull", "coat", "bod", "moustoir", "pont", "aber", "menez",
                  "beg", "an-ar", "bro"]
SUFFIX_ANCHORS = ["kemper", "kastell", "iliz", "mael", "meur", "nevez", "march",
                  "ac", "ach", "venez"]
# formes repliees exclues du matching automatique (trop generiques -> faux positifs)
SKIP_FORMS = {"e", "y", "ac", "ec", "oc"}
# noms dont la decomposition mecanique serait fausse
MATCH_EXCLUDE = {"gwened", "gwenned"}


def parse_decodeur(md):
    """Retourne (html_page, briques[]) avec forms/surface/anchor/sens/exemples/note."""
    lines = md.split("\n")
    intro, blocks = [], []
    cur_h2 = None
    i = 0
    briques = []
    body_md = []
    while i < len(lines):
        line = lines[i].rstrip()
        m = re.match(r"^\*\*(.+)\*\*$", line.strip())
        if m and not line.startswith("## "):
            titre = m.group(1)
            sens = note = exemples = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].startswith(("**", "##")):
                sens = lines[j].strip()
                j += 1
            while j < len(lines):
                l2 = lines[j].strip()
                if l2.startswith("Exemples :"):
                    exemples = l2[len("Exemples :"):].strip()
                    j += 1
                elif l2.startswith("Attention :"):
                    note = l2[len("Attention :"):].strip()
                    j += 1
                elif not l2:
                    j += 1
                else:
                    break
            briques.append({"titre": titre, "sens": sens, "exemples": exemples,
                            "note": note, "section": cur_h2})
            i = j
            continue
        if line.startswith("## "):
            cur_h2 = line[3:].strip()
        body_md.append(line)
        i += 1
    return md_blocks("\n".join(body_md)), briques


def brique_forms(titre):
    """'Plou- (Plo-, Plu-)' -> ['plou','plo','plu'] (repliees, sans tiret)."""
    base = titre.split("(")[0]
    paren = re.search(r"\((.+?)\)", titre)
    parts = re.split(r"[/,]", base)
    if paren:
        inner = paren.group(1).replace("formes françaises", "")
        parts += re.split(r"[/,]", inner)
    forms = []
    for part in parts:
        f = fold(part.strip()).strip("-")
        if f and f not in forms:
            forms.append(f)
    return forms


def brique_anchor(titre):
    first = re.split(r"[/,(]", titre)[0].strip().strip("-")
    special = {"an": "an-ar", "bro": "bro", "-kemper": "kemper", "Kemper": "kemper"}
    t = titre.strip()
    if t.startswith("-kastell") or t.startswith("-gastel"):
        return "kastell"
    if t.startswith("-ac'h") or t.startswith("-ec'h"):
        return "ach"
    if t.startswith("-ac "):
        return "ac"
    if t.startswith("-marc"):
        return "march"
    if t.startswith("an /") or t == "an / ar":
        return "an-ar"
    if t.startswith("bro"):
        return "bro"
    return fold(first)


def build_briques(briques_raw):
    out = []
    for b in briques_raw:
        anchor = brique_anchor(b["titre"])
        forms = brique_forms(b["titre"])
        out.append({
            "anchor": anchor,
            "titre": b["titre"],
            "sens": b["sens"],
            "exemples": b["exemples"],
            "note": b["note"],
            "forms": forms,
            "match_forms": [f for f in forms if f not in SKIP_FORMS],
            "court": SHORT_GLOSS.get(anchor, ""),
            "probable": anchor in PROBABLE,
            "position": "prefix" if anchor in PREFIX_ANCHORS else "suffix",
        })
    return out

# ---------------------------------------------------------------- decomposition

def decompose(nom, briques):
    """Decompose mecanique d'un nom replie. Retourne une liste de segments :
    {"t": "brique", "surface": str, "brique": {...}} ou {"t": "reste", "surface": str}."""
    s = fold(nom)
    if not s or s in MATCH_EXCLUDE:
        return []
    prefixes = sorted((b for b in briques if b["position"] == "prefix"),
                      key=lambda b: -max((len(f) for f in b["match_forms"]), default=0))
    suffixes = sorted((b for b in briques if b["position"] == "suffix"),
                      key=lambda b: -max((len(f) for f in b["match_forms"]), default=0))
    # le nom entier est une brique (Kemper, Breizh…)
    for b in briques:
        for f in b["match_forms"]:
            if s == f:
                return [{"t": "brique", "surface": s, "brique": b}]
    segs = []
    rest = s
    # prefixes en tete
    changed = True
    while changed and rest:
        changed = False
        for b in prefixes:
            for f in sorted(b["match_forms"], key=len, reverse=True):
                if rest.startswith(f) and len(rest) - len(f) >= 3:
                    segs.append({"t": "brique", "surface": rest[:len(f)], "brique": b})
                    rest = rest[len(f):].lstrip("-")
                    changed = True
                    break
            if changed:
                break
    # suffixes en fin (accepte le reste entier, ou 2 lettres avant minimum)
    tail = []
    changed = True
    while changed and rest:
        changed = False
        for b in suffixes:
            for f in sorted(b["match_forms"], key=len, reverse=True):
                avant = len(rest) - len(f)
                if rest.endswith(f) and (avant >= 2 or (avant == 0 and segs)):
                    tail.insert(0, {"t": "brique", "surface": rest[-len(f):], "brique": b})
                    rest = rest[:-len(f)].rstrip("-")
                    changed = True
                    break
            if changed:
                break
    if rest:
        segs.append({"t": "reste", "surface": rest})
    segs.extend(tail)
    if not any(g["t"] == "brique" for g in segs):
        return []
    return segs

# ---------------------------------------------------------------- source

def source_label(src):
    if src == "osm+wikidata":
        return "OpenStreetMap (ODbL) + Wikidata (CC0)"
    if src == "wikidata":
        return "Wikidata (CC0)"
    return "OpenStreetMap (ODbL)"

# ---------------------------------------------------------------- gabarits

def page(title, desc, body, canonical, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<!-- noindex temporaire : le lancement public est un verrou Franck (a retirer au GO) -->
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="{SITE_URL}{canonical}">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{SITE_URL}{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{extra_head}
</head>
<body>
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="entete">
  <div class="cadre">
    <a class="marque" href="/"><span class="marque__nom">{SITE_NAME}</span> <span class="marque__sig">{TAGLINE}</span></a>
    <nav class="nav" aria-label="Navigation principale">
      <a href="/">Accueil</a>
      <a href="/decodeur.html">Décodeur</a>
      <a href="/pourquoi.html">Pourquoi ce site</a>
      <a href="/sources.html">Sources</a>
    </nav>
  </div>
</header>
<main id="contenu">
{body}
</main>
<footer class="pied">
  <div class="cadre pied__grille">
    <div>
      <p><strong>{SITE_NAME}</strong> — {TAGLINE}.<br>Un outil gratuit du studio <a href="https://brozapi.com">Brozapi</a>.</p>
    </div>
    <div>
      <p><a href="/decodeur.html">Lire un panneau breton</a></p>
      <p><a href="/pourquoi.html">Pourquoi ce site</a></p>
      <p><a href="/sources.html">Sources et méthode</a></p>
      <p><a href="/mentions-legales.html">Mentions légales</a></p>
    </div>
    <div>
      <p class="pied__sources">Noms bretons : © les contributeurs d'OpenStreetMap (ODbL), Wikidata (CC0), Wikipédia en breton (CC BY-SA).</p>
    </div>
  </div>
</footer>
</body>
</html>
"""


def header_recherche():
    return """
<div class="recherche" role="search">
  <label class="recherche__label" for="champ">Tape le nom de ta commune</label>
  <input id="champ" class="recherche__champ" type="search" autocomplete="off"
         placeholder="Rennes, Plougastel, Kemper…" aria-describedby="aide-recherche">
  <p id="aide-recherche" class="recherche__aide">Français ou breton, avec ou sans accents.</p>
  <ul id="resultats" class="recherche__resultats" role="listbox" hidden></ul>
</div>
<script src="/assets/search-core.js"></script>
<script src="/assets/app.js"></script>
"""

# ---------------------------------------------------------------- fiche commune

def sens_phrase(entry, segs):
    """La 'signification en une phrase' de la fiche."""
    if entry.get("insee") == "56165":  # Ploermel — formulation verifiee (journal n.91)
        return ('Ploermael, c\'est « la paroisse de saint Armel » : <em>plou</em>, la paroisse, '
                'et <em>Mael</em>, saint Armel.')
    briques = [g for g in segs if g["t"] == "brique"]
    restes = [g for g in segs if g["t"] == "reste"]
    if not briques:
        return None
    courts = []
    for g in briques:
        b = g["brique"]
        c = b["court"] + (" (sens probable)" if b["probable"] else "")
        courts.append(f"« {g['surface']} » : {c}")
    phrase = "On y retrouve " + " et ".join(courts) + "."
    if restes:
        surfaces = " », « ".join(g["surface"] for g in restes)
        phrase += f" Le reste du nom (« {surfaces} ») n'a pas de lecture certaine."
    return phrase


def render_fiche(e):
    slug = f"c/{e['insee']}-{fold(e['nom_fr'])}.html"
    segs = decompose(e["nom_br"], briques) if e.get("nom_br") else []
    sens = sens_phrase(e, segs)
    titre = f"{e['nom_br']} — le nom breton de {e['nom_fr']}"
    desc = f"{e['nom_fr']} en breton : {e['nom_br']}. Origine du nom, décomposition et source."
    chips = []
    for g in segs:
        if g["t"] == "brique":
            b = g["brique"]
            prob = ' <span class="brique__prob">probable</span>' if b["probable"] else ""
            chips.append(
                f'<a class="brique" href="/decodeur.html#{b["anchor"]}" '
                f'title="{html.escape(b["titre"])} : {html.escape(b["court"])}">'
                f'<span class="brique__surf" lang="br">{html.escape(g["surface"])}</span>'
                f'<span class="brique__sens">{html.escape(b["court"])}{prob}</span></a>')
        else:
            chips.append(f'<span class="brique brique--reste"><span class="brique__surf" lang="br">'
                         f'{html.escape(g["surface"])}</span><span class="brique__sens">non décodé</span></span>')
    bloc_briques = ""
    if chips:
        bloc_briques = ('<section class="fiche__briques"><h2>Comment lire ce nom</h2>'
                        '<div class="briques">' + "\n".join(chips) + "</div>"
                        '<p class="fiche__lien-decodeur">Ces briques, et toutes les autres, sont expliquées '
                        'dans le <a href="/decodeur.html">décodeur de panneaux</a>.</p></section>')
    lien_brwiki = ""
    if e.get("brwiki"):
        lien_brwiki = (f'<li><a href="{html.escape(e["brwiki"])}" rel="noopener">Article sur Wikipédia '
                       f'en breton</a> (CC BY-SA)</li>')
    bloc_sens = f'<p class="fiche__sens">{sens}</p>' if sens else ""
    body = f"""
<article class="cadre fiche">
  <p class="fiche__fil"><a href="/">Accueil</a> · <a href="/d/{e['departement']}-{fold(DEPT_NOMS[e['departement']])}.html">{html.escape(DEPT_NOMS[e['departement']])}</a></p>
  <p class="fiche__type">{TYPE_LABELS.get(e['type'], e['type'])} · {html.escape(e['nom_fr'])}</p>
  <h1 class="fiche__nom" lang="br">{html.escape(e['nom_br'])}</h1>
  {bloc_sens}
  {bloc_briques}
  <section class="fiche__source">
    <h2>Source</h2>
    <p class="badge-source">Source : {html.escape(source_label(e['source']))}</p>
    <ul>
      <li><a href="{html.escape(e['url_source'])}" rel="noopener">Fiche d'origine</a></li>
      {lien_brwiki}
      <li><a href="/sources.html">Comment ces informations sont rassemblées</a></li>
    </ul>
  </section>
  <section class="fiche__partage">
    <h2>Faire découvrir ce nom</h2>
    <p>Une image toute prête pour les réseaux, générée dans ton navigateur — rien n'est envoyé nulle part.</p>
    <p>
      <button class="bouton" id="btn-partage" type="button">Partager mon village</button>
      <button class="bouton bouton--second" id="btn-lien" type="button">Copier le lien</button>
    </p>
    <p class="fiche__partage-statut" id="partage-statut" role="status" aria-live="polite"></p>
  </section>
  {header_recherche()}
</article>
<script src="/assets/partage.js"></script>
<script>
window.KERVILLAGE_FICHE = {json.dumps({
        "nomFr": e["nom_fr"], "nomBr": e["nom_br"],
        "sens": re.sub(r"<[^>]+>", "", sens or f"Forme bretonne de {e['nom_fr']}."),
        "url": f"{SITE_URL}/{slug}"}, ensure_ascii=False)};
</script>
<script src="/assets/fiche.js"></script>
"""
    return slug, page(titre, desc, body, f"/{slug}")

# ---------------------------------------------------------------- pages

def render_index(communes, nb_lieux):
    carte = json.load(open(os.path.join(ROOT, "build", "carte.json"), encoding="utf-8"))
    paths = []
    for code, d in sorted(carte["depts"].items()):
        url = f"/d/{code}-{fold(d['nom'])}.html"
        paths.append(
            f'<a href="{url}" aria-label="{html.escape(d["nom"])}">'
            f'<path d="{d["path"]}" class="carte__dept"><title>{html.escape(d["nom"])}</title></path></a>')
    carte_svg = (f'<svg viewBox="{carte["viewBox"]}" class="carte" role="img" '
                 f'aria-label="Carte des cinq départements de Bretagne historique">'
                 + "".join(paths) + "</svg>")
    body = f"""
<section class="cadre hero">
  <h1 class="hero__titre">Ton village<br>en breton</h1>
  <p class="hero__sous">Le nom breton de ta commune, ce qu'il signifie,
  et la clé pour lire les panneaux de Bretagne. Gratuit, sourcé, sans compte.</p>
  {header_recherche()}
  <p class="hero__stats">{nb(len(communes))} communes et {nb(nb_lieux)} lieux-dits couverts
  dans les cinq départements de Bretagne historique, plus quelques communes limitrophes.</p>
</section>
<section class="cadre carte-section">
  <h2>Les cinq départements</h2>
  <div class="carte-wrap">{carte_svg}</div>
  <ul class="dept-liens">
    {"".join(f'<li><a href="/d/{c}-{fold(n)}.html">{html.escape(n)}</a></li>' for c, n in sorted(DEPT_NOMS.items()))}
  </ul>
</section>
<section class="cadre trois">
  <div class="trois__col">
    <h2>Cherche</h2>
    <p>Tape « Rennes », tu trouves <em lang="br">Roazhon</em>. Tape « Kemper », tu tombes sur Quimper.
    La recherche pardonne les accents et les fautes de frappe.</p>
  </div>
  <div class="trois__col">
    <h2>Comprends</h2>
    <p>Chaque nom se décompose en briques : <em lang="br">plou</em> la paroisse, <em lang="br">ker</em> le village,
    <em lang="br">loc</em> le lieu consacré. Trente briques suffisent pour lire la plupart des panneaux.</p>
    <p><a href="/decodeur.html">Ouvrir le décodeur</a></p>
  </div>
  <div class="trois__col">
    <h2>Partage</h2>
    <p>Sur chaque fiche, un bouton génère une image du nom breton, prête pour les réseaux.
    Le breton gagne à être montré.</p>
  </div>
</section>
<section class="cadre confiance">
  <h2>Rien d'inventé</h2>
  <p>Chaque nom affiché vient d'OpenStreetMap, de Wikidata ou de Wikipédia en breton, et la source
  est écrite sur la fiche. Aucun texte n'est généré automatiquement. La méthode complète est sur la
  page <a href="/sources.html">Sources et méthode</a>.</p>
</section>
"""
    return page(f"{SITE_NAME} — {TAGLINE}",
                "Le nom breton de ta commune, sa signification et un décodeur pour lire "
                "les panneaux de Bretagne. Gratuit et sourcé.",
                body, "/")


def render_departement(code, communes_dept, nb_lieux_dept):
    nom = DEPT_NOMS[code]
    slug = f"d/{code}-{fold(nom)}.html"
    items = "\n".join(
        f'<li><a href="/c/{c["insee"]}-{fold(c["nom_fr"])}.html">{html.escape(c["nom_fr"])}</a>'
        f' <span class="liste__br" lang="br">{html.escape(c["nom_br"])}</span></li>'
        for c in sorted(communes_dept, key=lambda x: fold(x["nom_fr"])))
    note_limitrophes = (
        "\n  <p>Quelques communes limitrophes du pays nantais (Vendée, Maine-et-Loire) "
        "figurent aussi dans cette liste : elles appartiennent au même territoire "
        "de toponymie bretonne.</p>" if code == "44" else "")
    body = f"""
<div class="cadre">
  <p class="fiche__fil"><a href="/">Accueil</a></p>
  <h1>{html.escape(nom)} ({code})</h1>
  <p>{len(communes_dept)} communes, toutes avec leur nom breton, et {nb_lieux_dept} lieux-dits répertoriés
  dans la base. Cherche un nom ci-dessous ou parcours la liste.</p>{note_limitrophes}
  {header_recherche()}
  <ul class="liste">{items}</ul>
</div>
"""
    return slug, page(f"{nom} — les communes en breton | {SITE_NAME}",
                      f"Le nom breton des {len(communes_dept)} communes de {nom} ({code}).",
                      body, f"/{slug}")


def render_decodeur(body_md_html, briques):
    cartes = []
    for b in briques:
        note = f'<p class="brique-carte__note">{md_inline(b["note"])}</p>' if b["note"] else ""
        ex = f'<p class="brique-carte__ex"><span class="etiquette">Exemples</span> {md_inline(b["exemples"])}</p>' if b["exemples"] else ""
        prob = ' <span class="badge-probable">sens probable</span>' if b["probable"] else ""
        cartes.append(f"""
<div class="brique-carte" id="{b['anchor']}">
  <h3 lang="br">{html.escape(b['titre'])}</h3>{prob}
  <p>{md_inline(b['sens'])}</p>
  {ex}
  {note}
</div>""")
    # reconstruit la page : intro du markdown, puis les cartes par section
    # replace les cartes sous leurs titres de section du markdown
    cartes_prefix = "".join(c for c, b in zip(cartes, briques) if b["position"] == "prefix")
    cartes_suffix = "".join(c for c, b in zip(cartes, briques) if b["position"] == "suffix")
    h2_tete = '<h2 id="en-tete-de-nom">En tête de nom</h2>'
    h2_fin = '<h2 id="en-fin-de-nom">En fin de nom</h2>'
    intro, sep, reste = body_md_html.partition(h2_tete)
    assert sep, "section 'En tête de nom' introuvable dans decodeur.md"
    _, sep2, conclusion = reste.partition(h2_fin)
    assert sep2, "section 'En fin de nom' introuvable dans decodeur.md"
    body = f"""
<div class="cadre">
  {intro}
  {h2_tete}
  <div class="brique-cartes">{cartes_prefix}</div>
  {h2_fin}
  <div class="brique-cartes">{cartes_suffix}</div>
  {conclusion}
  <p><a href="/">Chercher une commune</a></p>
</div>
"""
    return page("Lire un panneau breton — le décodeur | " + SITE_NAME,
                "Trente briques toponymiques (Plou-, Ker-, Loc-, -ac'h…) pour lire les noms "
                "de communes de Bretagne comme une phrase.",
                body, "/decodeur.html")


def render_simple(md_file, title, desc, canonical, complement=""):
    md = open(os.path.join(ROOT, "content", md_file), encoding="utf-8").read()
    body = f'<div class="cadre prose">{md_blocks(md)}{complement}<p><a href="/">Retour à l\'accueil</a></p></div>'
    return page(title, desc, body, canonical)


def render_mentions():
    # build/telephone.html est une page HTML autonome (noindex) : on n'en extrait
    # que le fragment <li> avec le numero, pour l'inserer dans les mentions.
    src = open(os.path.join(ROOT, "build", "telephone.html"), encoding="utf-8").read()
    tel = re.search(r"<li>.*?</li>", src, re.S).group(0).strip()
    body = f"""
<div class="cadre prose">
<h1>Mentions légales</h1>
<h2>Éditeur du site</h2>
<ul>
  <li>Éditeur : <strong>Franck Barrin</strong> — Entrepreneur individuel, nom commercial « Vizinote », profession libérale non réglementée, régime micro-BNC</li>
  <li>SIRET : 103 472 866 00013 — Code APE : 6201Z (programmation informatique)</li>
  <li>Adresse : 11 rue Chevalier Tristan, 56800 Ploërmel, France</li>
  <li>Contact : <a href="mailto:contact@brozapi.com">contact@brozapi.com</a></li>
  {tel}
  <li>Directeur de la publication : <strong>Franck Barrin</strong></li>
  <li>TVA non applicable, article 293 B du CGI (franchise en base de TVA)</li>
</ul>
<h2>Hébergement</h2>
<ul>
  <li>Site : GitHub Pages — GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis (filiale de Microsoft, données encadrées par les clauses contractuelles types UE).</li>
</ul>
<h2>Propriété intellectuelle</h2>
<p>Le site, sa charte graphique et ses textes (pages « Pourquoi ce site », « Sources et méthode », décodeur) sont la propriété du studio Brozapi, sauf mention contraire.</p>
<p>Les données affichées restent la propriété de leurs sources : noms bretons © les contributeurs d'OpenStreetMap (licence ODbL), correspondances Wikidata (CC0), étymologies issues de Wikipédia en breton (CC BY-SA). Conformément à l'ODbL, la base dérivée est repartagée sous la même licence sur <a href="https://github.com/vizinote/toponymie-bretonne">github.com/vizinote/toponymie-bretonne</a>.</p>
<h2 id="confidentialite">Confidentialité</h2>
<p>{SITE_NAME} ne collecte <strong>aucune donnée personnelle</strong> : pas de compte, pas de formulaire, pas de cookie, pas de mesure d'audience. La recherche s'effectue entièrement dans votre navigateur ; aucune requête n'est envoyée à un serveur.</p>
<p>Pour toute question ou pour signaler une erreur : <a href="mailto:contact@brozapi.com">contact@brozapi.com</a>. Vous disposez des droits prévus par le RGPD et pouvez saisir la CNIL en cas de différend.</p>
<p><a href="/">Retour à l'accueil</a></p>
</div>
"""
    return page(f"Mentions légales | {SITE_NAME}",
                "Mentions légales et politique de confidentialité de Kervillage.",
                body, "/mentions-legales.html")


def render_lieu():
    body = f"""
<article class="cadre fiche" id="fiche-lieu">
  <p class="fiche__fil"><a href="/">Accueil</a> <span id="fil-dept"></span></p>
  <p class="fiche__type" id="lieu-type"></p>
  <h1 class="fiche__nom" lang="br" id="lieu-nom"></h1>
  <p class="fiche__sens" id="lieu-sens"></p>
  <section class="fiche__briques" id="lieu-briques" hidden>
    <h2>Comment lire ce nom</h2>
    <div class="briques" id="lieu-chips"></div>
    <p class="fiche__lien-decodeur">Ces briques, et toutes les autres, sont expliquées dans le
    <a href="/decodeur.html">décodeur de panneaux</a>.</p>
  </section>
  <section class="fiche__source">
    <h2>Source</h2>
    <p class="badge-source" id="lieu-source"></p>
    <ul id="lieu-liens"></ul>
  </section>
  <section class="fiche__partage">
    <h2>Faire découvrir ce nom</h2>
    <p>Une image toute prête pour les réseaux, générée dans ton navigateur — rien n'est envoyé nulle part.</p>
    <p>
      <button class="bouton" id="btn-partage" type="button">Partager ce lieu</button>
      <button class="bouton bouton--second" id="btn-lien" type="button">Copier le lien</button>
    </p>
    <p class="fiche__partage-statut" id="partage-statut" role="status" aria-live="polite"></p>
  </section>
  {header_recherche()}
</article>
<script src="/assets/briques.js"></script>
<script src="/assets/partage.js"></script>
<script src="/assets/fiche.js"></script>
<script src="/assets/lieu.js"></script>
"""
    return page(f"Un lieu de Bretagne en breton | {SITE_NAME}",
                "Le nom breton d'un lieu de Bretagne, sa source et sa lecture brique par brique.",
                body, "/lieu.html")

# ---------------------------------------------------------------- main

def main():
    global briques
    dataset = json.load(open(DATASET, encoding="utf-8"))
    dec_md = open(os.path.join(ROOT, "content", "decodeur.md"), encoding="utf-8").read()
    dec_intro_html, briques_raw = parse_decodeur(dec_md)
    briques = build_briques(briques_raw)

    communes = [e for e in dataset if e["type"] == "commune" and e.get("insee")]
    lieux = [e for e in dataset if not (e["type"] == "commune" and e.get("insee"))]
    print(f"communes: {len(communes)}, autres lieux: {len(lieux)}")

    os.makedirs(os.path.join(ROOT, "c"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "d"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)

    def w(path, content):
        with open(os.path.join(ROOT, path), "w", encoding="utf-8") as f:
            f.write(content)

    # fiches communes
    urls = ["/", "/decodeur.html", "/pourquoi.html", "/sources.html", "/mentions-legales.html"]
    for e in communes:
        slug, html_page = render_fiche(e)
        w(slug, html_page)
        urls.append("/" + slug)
    print("fiches communes ecrites")

    # departements
    for code in DEPT_NOMS:
        cs = [c for c in communes if c["departement"] == code]
        lx = [l for l in lieux if l["departement"] == code]
        slug, html_page = render_departement(code, cs, len(lx))
        w(slug, html_page)
        urls.append("/" + slug)

    # pages simples
    w("index.html", render_index(communes, len(lieux)))
    w("decodeur.html", render_decodeur(dec_intro_html, briques))
    w("pourquoi.html", render_simple("pourquoi.md",
                                     f"Pourquoi ce site | {SITE_NAME}",
                                     "Pourquoi Kervillage existe : rendre lisibles les panneaux bilingues de Bretagne.",
                                     "/pourquoi.html"))
    complement = """
<h2 id="complements-techniques">Compléments techniques</h2>
<ul>
<li>Fond de carte des départements (page d'accueil) : données IGN GEOFLA via le jeu de données ouvert france-geojson, sous Licence Ouverte Etalab, simplifiées pour le web.</li>
<li>La base dérivée complète (noms bretons croisés OpenStreetMap × Wikidata) est repartagée sous licence ODbL sur <a href="https://github.com/vizinote/toponymie-bretonne">github.com/vizinote/toponymie-bretonne</a>.</li>
</ul>
"""
    w("sources.html", render_simple("sources.md",
                                    f"Sources et méthode | {SITE_NAME}",
                                    "D'où viennent les noms bretons affichés sur Kervillage : OpenStreetMap, Wikidata, Wikipédia en breton. Attributions et méthode.",
                                    "/sources.html", complement=complement))
    w("mentions-legales.html", render_mentions())
    w("lieu.html", render_lieu())

    # donnees lieux par departement
    idx = {}
    lieux_par_dept = {}
    for l in lieux:
        lieux_par_dept.setdefault(l["departement"], []).append(l)
    for code, lst in lieux_par_dept.items():
        lst.sort(key=lambda x: fold(x.get("nom_br") or x.get("nom_fr") or ""))
        compact = [{k: l.get(k) for k in ("nom_fr", "nom_br", "type", "source", "url_source",
                                          "brwiki", "departement_nom")} for l in lst]
        w(f"data/lieux-{code}.json", json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
        for i, l in enumerate(lst):
            idx[id(l)] = i

    # index de recherche
    search = []
    seen = set()
    for e in communes:
        search.append({"n": e["nom_fr"], "b": e["nom_br"], "s": fold(e["nom_fr"]),
                       "q": fold(e["nom_br"]), "d": e["departement"], "t": "commune",
                       "u": f"c/{e['insee']}-{fold(e['nom_fr'])}.html"})
    for l in lieux:
        n = l.get("nom_fr") or l.get("nom_br")
        b = l.get("nom_br") or l.get("nom_fr")
        if not n:
            continue
        key = (fold(n), fold(b or ""), l["departement"], l["type"])
        if key in seen:
            continue
        seen.add(key)
        search.append({"n": n, "b": b, "s": fold(n), "q": fold(b or ""),
                       "d": l["departement"], "t": l["type"],
                       "u": f"lieu.html?d={l['departement']}&i={idx[id(l)]}"})
    w("data/search.json", json.dumps(search, ensure_ascii=False, separators=(",", ":")))
    print(f"index recherche: {len(search)} entrees")

    # briques.js (portage JS du matching pour lieu.html)
    bjs = {
        "briques": [{"anchor": b["anchor"], "titre": b["titre"], "court": b["court"],
                     "probable": b["probable"], "position": b["position"],
                     "matchForms": b["match_forms"]} for b in briques],
        "exclude": sorted(MATCH_EXCLUDE),
    }
    w("assets/briques.js", "window.KERVILLAGE_BRIQUES = " + json.dumps(bjs, ensure_ascii=False) + ";\n")

    # sitemap + robots
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{SITE_URL}{u}</loc></url>")
    sm.append("</urlset>")
    w("sitemap.xml", "\n".join(sm))
    w("robots.txt", "User-agent: *\nAllow: /\nSitemap: " + SITE_URL + "/sitemap.xml\n")
    print("build termine")


if __name__ == "__main__":
    briques = []
    main()
