#!/usr/bin/env python3
"""Genere relecture/index.html — interface de relecture pour Enora.

Le contenu relu est EXTRAIT des pages de production du repo
(decodeur.html, pourquoi.html, sources.html), jamais re-saisi :
toute correction future du site se propage en relancant ce script.

La page est autonome (aucun backend) : noindex/nofollow, absente du
sitemap, non liee depuis les pages publiques. Envoi = mailto pre-rempli
vers contact@brozapi.com + bouton « copier » (fallback automatique si le
texte depasse la limite mailto ~2000 caracteres).

Usage : python3 build/gen_relecture.py   (a lancer depuis la racine du repo)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "relecture" / "index.html"

MAILTO_LIMIT = 1800  # au-dela, bascule automatique sur « copier »


def strip_tags(fragment):
    txt = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def short_label(fragment, words=8):
    parts = strip_tags(fragment).split()
    label = " ".join(parts[:words])
    return label + ("…" if len(parts) > words else "")


# ---------------------------------------------------------------- decodeur
def parse_decodeur():
    src = (ROOT / "decodeur.html").read_text(encoding="utf-8")
    intro_m = re.search(
        r"(<h1>Lire un panneau breton</h1>.*?)<h2 id=\"en-tete-de-nom\">",
        src, re.S)
    if not intro_m:
        raise SystemExit("intro du decodeur introuvable — le gabarit a change ?")
    intro_html = intro_m.group(1).strip()

    sections = []  # (titre_section, [cartes])
    for sec_id, sec_titre in (("en-tete-de-nom", "En tête de nom"),
                              ("en-fin-de-nom", "En fin de nom")):
        sec_m = re.search(
            r'<h2 id="%s">.*?</h2>(.*?)(?:<h2 id="|<hr>)' % sec_id, src, re.S)
        if not sec_m:
            raise SystemExit("section %s introuvable" % sec_id)
        cartes = re.findall(
            r'<div class="brique-carte" id="([^"]+)">(.*?)</div>',
            sec_m.group(1), re.S)
        sections.append((sec_titre, cartes))
    total = sum(len(c) for _, c in sections)
    if total != 30:
        raise SystemExit("30 briques attendues, %d trouvees" % total)
    return intro_html, sections


# ------------------------------------------------------------- pourquoi/sources
def parse_prose(page, group_by_h2):
    src = (ROOT / page).read_text(encoding="utf-8")
    body_m = re.search(r'<div class="cadre prose">(.*?)</div>\s*</main>',
                       src, re.S)
    if not body_m:
        raise SystemExit("contenu prose introuvable dans %s" % page)
    body = body_m.group(1)
    body = re.sub(r"<h1>.*?</h1>", "", body, flags=re.S)  # le titre porte le bloc
    elts = re.findall(r"<(?:p|ul|h2)[ >].*?</(?:p|ul|h2)>", body, re.S)
    elts = [e for e in elts if "Retour à l'accueil" not in e]
    if not group_by_h2:
        return [("bloc", e, short_label(e)) for e in elts]
    blocks, cur_titre, cur_html = [], "Introduction", []
    for e in elts:
        if e.startswith("<h2"):
            if cur_html:
                blocks.append(("groupe", "\n".join(cur_html), cur_titre))
            cur_titre, cur_html = strip_tags(e), []
        else:
            cur_html.append(e)
    if cur_html:
        blocks.append(("groupe", "\n".join(cur_html), cur_titre))
    return blocks


def esc_attr(s):
    return html.escape(s, quote=True)


def bloc_html(bloc_id, label, contenu, court=None):
    return f'''<section class="rel-bloc" data-bloc="{bloc_id}" data-label="{esc_attr(label)}" data-court="{esc_attr(court or label)}">
  <div class="rel-bloc__texte">{contenu}</div>
  <div class="rel-bloc__actions">
    <button type="button" class="rel-btn rel-btn--ok">C'est bon pour moi</button>
    <button type="button" class="rel-btn rel-btn--corr">Je corrige / je commente</button>
  </div>
  <textarea class="rel-corr" rows="3" placeholder="Ta correction ou ton commentaire…" aria-label="Correction pour {esc_attr(label)}"></textarea>
  <p class="rel-etat" aria-live="polite"></p>
</section>'''


def main():
    intro_html, sections = parse_decodeur()
    pourquoi = parse_prose("pourquoi.html", group_by_h2=False)
    sources = parse_prose("sources.html", group_by_h2=True)

    parties = []
    # 1. decodeur
    blocs = [bloc_html("dec-intro", "Introduction du décodeur", intro_html,
                       court="Intro du décodeur")]
    for sec_titre, cartes in sections:
        blocs.append(f'<h3 class="rel-soustitre">{sec_titre}</h3>')
        for anchor, carte in cartes:
            label = strip_tags(re.search(r"<h3[^>]*>(.*?)</h3>", carte, re.S).group(1))
            court = "brique " + label.split("(")[0].strip()
            blocs.append(bloc_html(f"brique-{anchor}", label, carte.strip(),
                                   court=court))
    parties.append(("1. Le décodeur — les trente briques",
                    "C'est le cœur du site. Pour chaque brique : le sens est-il juste, "
                    "les exemples sont-ils corrects, les formes bretonnes entre parenthèses "
                    "sont-elles bien orthographiées&nbsp;?", "\n".join(blocs)))
    # 2. pourquoi
    blocs = [bloc_html(f"pq-{i+1}", f"« {label} »", contenu,
                       court=f"bloc {i+1}")
             for i, (_, contenu, label) in enumerate(pourquoi)]
    parties.append(("2. La page « Pourquoi ce site »",
                    "Le ton général : est-ce que ça sonne juste et sobre, sans folklore&nbsp;?",
                    "\n".join(blocs)))
    # 3. sources
    blocs = [bloc_html(f"src-{i+1}", label, contenu, court=label)
             for i, (_, contenu, label) in enumerate(sources)]
    parties.append(("3. La page « Sources et méthode »",
                    "Même principe, section par section.", "\n".join(blocs)))

    nb_blocs = 1 + 30 + len(pourquoi) + len(sources)

    sections_html = "\n".join(
        f'<h2 class="rel-titre">{titre}</h2>\n<p class="rel-consigne">{consigne}</p>\n{corps}'
        for titre, consigne, corps in parties)

    page = TEMPLATE
    page = page.replace("__SECTIONS__", sections_html)
    page = page.replace("__NB_BLOCS__", str(nb_blocs))
    page = page.replace("__MAILTO_LIMIT__", str(MAILTO_LIMIT))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"OK {OUT} — {nb_blocs} blocs "
          f"(1 intro + 30 briques + {len(pourquoi)} pourquoi + {len(sources)} sources)")


TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relecture — Kervillage</title>
<!-- page privee de relecture : noindex volontaire et permanent, hors sitemap, non liee -->
<meta name="robots" content="noindex, nofollow">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<style>
/* ---------- interface de relecture (palette Glaz & Ajonc) ---------- */
.rel-hero { background: var(--brand); color: var(--brand-encre); padding: 2.6rem 1.25rem 2.2rem; }
.rel-hero .cadre { max-width: 46rem; }
.rel-hero h1 { font-family: var(--serif); font-size: clamp(2rem, 6vw, 2.8rem); margin: 0 0 1rem; }
.rel-hero p { color: var(--brand-encre); max-width: 40rem; }
.rel-hero .rel-regle { width: 3.5rem; height: 3px; background: var(--accent); margin: 0 0 1.2rem; border: 0; }
.rel-attentes { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); border-radius: var(--rayon); padding: 1rem 1.25rem; margin: 1.4rem 0 0; }
.rel-attentes ul { margin: .4rem 0 0; padding-left: 1.2rem; }
.rel-attentes li { margin: .35rem 0; }
.rel-attentes strong { color: #FFFFFF; }

.rel-progress { position: sticky; top: 0; z-index: 6; background: var(--papier); border-bottom: 1px solid var(--ligne); padding: .6rem 1.25rem; }
.rel-progress .cadre { display: flex; align-items: center; gap: 1rem; }
.rel-progress__barre { flex: 1; height: 8px; background: var(--papier-2); border-radius: 99px; overflow: hidden; }
.rel-progress__rempli { height: 100%; width: 0; background: var(--accent); transition: width .25s ease; }
.rel-progress__txt { font-size: .9rem; color: var(--encre-doux); white-space: nowrap; }

.rel-titre { font-family: var(--serif); font-size: 1.7rem; margin: 3rem 0 .3rem; border-top: 3px solid var(--accent); padding-top: 1.2rem; }
.rel-consigne { color: var(--encre-doux); margin-top: 0; }
.rel-soustitre { font-family: var(--serif); font-size: 1.25rem; margin: 2rem 0 .8rem; }

.rel-bloc { background: #FFFFFF; border: 1px solid var(--ligne); border-radius: var(--rayon); padding: 1.1rem 1.25rem; margin: 1rem 0; }
.rel-bloc--ok { border-color: #2E7D4F; box-shadow: inset 4px 0 0 #2E7D4F; }
.rel-bloc--corr { border-color: var(--accent); box-shadow: inset 4px 0 0 var(--accent); }
.rel-bloc__texte h3 { margin-top: 0; }
.rel-bloc__texte > :last-child { margin-bottom: 0; }
.rel-bloc__actions { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .9rem; }
.rel-btn { font: inherit; font-size: .95rem; border-radius: 99px; padding: .55rem 1.1rem; cursor: pointer; border: 2px solid transparent; min-height: 44px; }
.rel-btn--ok { background: var(--brand); color: var(--brand-encre); }
.rel-btn--ok[aria-pressed="true"] { background: #2E7D4F; color: #FFFFFF; }
.rel-btn--corr { background: transparent; color: var(--lien); border-color: var(--lien); }
.rel-btn--corr[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: var(--encre); }
.rel-corr { display: none; width: 100%; margin-top: .8rem; font: inherit; font-size: 1rem; padding: .7rem .9rem; border: 2px solid var(--brand); border-radius: var(--rayon); background: var(--papier); color: var(--encre); }
.rel-corr.is-visible { display: block; }
.rel-etat { margin: .5rem 0 0; font-size: .88rem; color: #2E7D4F; min-height: 1.2em; }

.rel-final { background: #FFFFFF; border: 1px solid var(--ligne); border-radius: var(--rayon); padding: 1.1rem 1.25rem; margin: 1rem 0; }
.rel-final fieldset { border: 0; margin: 0; padding: 0; }
.rel-final legend { font-weight: 600; margin-bottom: .6rem; }
.rel-choix { display: block; border: 1px solid var(--ligne); border-radius: var(--rayon); padding: .7rem 1rem; margin: .5rem 0; cursor: pointer; }
.rel-choix:has(input:checked) { border-color: var(--accent); background: #FBF3DF; }
.rel-choix input { margin-right: .5rem; }
.rel-mot { width: 100%; font: inherit; font-size: 1rem; padding: .7rem .9rem; border: 2px solid var(--brand); border-radius: var(--rayon); background: var(--papier); color: var(--encre); margin-top: .4rem; }

.rel-envoi { background: var(--fond-info); border-radius: var(--rayon); padding: 1.4rem 1.25rem; margin: 1rem 0 3rem; }
.rel-envoi__actions { display: flex; flex-wrap: wrap; gap: .7rem; margin-top: 1rem; }
.rel-btn--grand { background: var(--brand); color: var(--brand-encre); border: 0; font-size: 1.05rem; padding: .8rem 1.6rem; border-radius: 99px; cursor: pointer; min-height: 48px; text-decoration: none; display: inline-block; }
.rel-btn--copie { background: var(--accent); color: var(--encre); border: 0; font-size: 1.05rem; padding: .8rem 1.6rem; border-radius: 99px; cursor: pointer; min-height: 48px; }
.rel-sortie { display: none; margin-top: 1.2rem; }
.rel-sortie.is-visible { display: block; }
.rel-sortie textarea { width: 100%; font: inherit; font-size: .92rem; padding: .8rem; border: 1px solid var(--ligne); border-radius: var(--rayon); background: #FFFFFF; color: var(--encre); }
.rel-note { font-size: .9rem; color: var(--encre-doux); }
.rel-note--trop-long { color: var(--or-texte); font-weight: 600; }
.rel-reset { background: none; border: 0; color: var(--encre-doux); text-decoration: underline; cursor: pointer; font-size: .85rem; padding: 0; }
</style>
</head>
<body>
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="entete">
  <div class="cadre">
    <span class="marque"><span class="marque__hermine" aria-hidden="true"><svg width="24" height="30" viewBox="0 0 16 20" fill="none"><circle cx="4.6" cy="4" r="1.5" fill="currentColor"/><circle cx="11.4" cy="4" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.7" fill="currentColor"/><path d="M8 11c-1.4 1.6-1.4 5-1.4 7 0 .7 1.4 1.3 1.4.7-.05.6 1.4 0 1.4-.7 0-2 0-5.4-1.4-7z" fill="currentColor"/></svg></span><span class="marque__nom">Kervillage</span> <span class="marque__sig">relecture</span></span>
  </div>
</header>
<div class="filet" aria-hidden="true"></div>

<div class="rel-hero">
  <div class="cadre">
    <hr class="rel-regle">
    <h1>Merci Enora&nbsp;!</h1>
    <p>Tu connais Kervillage, le petit site qui explique les noms de communes en breton.
       Avant de le montrer au monde, j'aimerais qu'une vraie brittophone le lise — et cette
       brittophone, c'est toi.</p>
    <div class="rel-attentes">
      <strong>Ce que je te demande :</strong>
      <ul>
        <li>Vérifier <strong>l'exactitude du breton</strong> : les formes, les mutations, les accords, le dialecte.</li>
        <li>Vérifier <strong>le ton</strong> : est-ce que ça sonne juste et sobre, sans folklore&nbsp;?</li>
      </ul>
      <p style="margin:.8rem 0 0">Pas besoin de relire l'orthographe du français ni le design.
      Compte une vingtaine de minutes, à ton rythme : tu peux fermer la page et revenir plus tard,
      tes réponses restent enregistrées dans ton navigateur.</p>
    </div>
  </div>
</div>

<div class="rel-progress" aria-hidden="false">
  <div class="cadre">
    <div class="rel-progress__barre"><div class="rel-progress__rempli" id="rel-rempli"></div></div>
    <span class="rel-progress__txt" id="rel-compteur">0 / __NB_BLOCS__ blocs relus</span>
    <button type="button" class="rel-reset" id="rel-reset">tout effacer</button>
  </div>
</div>

<main id="contenu">
<div class="cadre">

__SECTIONS__

<h2 class="rel-titre">4. Pour finir</h2>
<div class="rel-final">
  <fieldset id="rel-mention">
    <legend>Veux-tu être mentionnée comme relectrice sur le site&nbsp;?</legend>
    <label class="rel-choix"><input type="radio" name="mention" value="Oui, avec mon nom complet"> Oui, avec mon nom complet</label>
    <label class="rel-choix"><input type="radio" name="mention" value="Oui, juste mon prénom"> Oui, juste mon prénom</label>
    <label class="rel-choix"><input type="radio" name="mention" value="Je préfère rester anonyme"> Je préfère rester anonyme</label>
  </fieldset>
  <p style="margin:1.2rem 0 .3rem"><label for="rel-mot"><strong>Un mot pour Franck&nbsp;?</strong> (optionnel)</label></p>
  <textarea class="rel-mot" id="rel-mot" rows="3" placeholder="Ce que tu veux — une remarque générale, un encouragement, un doute…"></textarea>
</div>

<h2 class="rel-titre">5. Envoyer ta relecture</h2>
<div class="rel-envoi">
  <p style="margin-top:0">Quand tu as fini (ou même si tu n'as pas tout fait), clique ici : la page
  rassemble toutes tes réponses dans un texte lisible, prêt à m'envoyer.</p>
  <div class="rel-envoi__actions">
    <button type="button" class="rel-btn--grand" id="rel-preparer">Préparer l'envoi</button>
  </div>
  <div class="rel-sortie" id="rel-sortie">
    <textarea id="rel-texte" rows="14" readonly aria-label="Texte compilé de ta relecture"></textarea>
    <p class="rel-note" id="rel-note-mail">Ton logiciel d'email va s'ouvrir avec tout le texte déjà rempli.
       Si rien ne s'ouvre, ou si tu préfères passer par Messenger :</p>
    <p class="rel-note rel-note--trop-long" id="rel-note-long" hidden>Le texte est trop long pour passer
       automatiquement dans un email : utilise le bouton « Copier le texte » ci-dessous, puis colle-le
       dans un email à contact@brozapi.com ou dans Messenger.</p>
    <div class="rel-envoi__actions">
      <a class="rel-btn--grand" id="rel-mailto" href="#">Ouvrir dans ma messagerie</a>
      <button type="button" class="rel-btn--copie" id="rel-copier">Copier le texte</button>
    </div>
    <p class="rel-note" id="rel-copie-etat" aria-live="polite"></p>
  </div>
</div>

</div>
</main>
<footer class="pied">
  <div class="cadre">
    <p><strong>Kervillage</strong> — ton village en breton. Un outil gratuit du studio Brozapi.</p>
  </div>
</footer>

<script>
(function () {
  "use strict";
  var CLE = "kervillage-relecture-v1";
  var LIMITE_MAILTO = __MAILTO_LIMIT__;
  var blocs = Array.prototype.slice.call(document.querySelectorAll(".rel-bloc"));
  var etat = { reponses: {}, mention: "", mot: "" };

  try {
    var brut = localStorage.getItem(CLE);
    if (brut) {
      var charge = JSON.parse(brut);
      if (charge && typeof charge === "object") {
        etat.reponses = charge.reponses || {};
        etat.mention = charge.mention || "";
        etat.mot = charge.mot || "";
      }
    }
  } catch (e) { /* stockage indisponible : la page fonctionne quand meme */ }

  function sauvegarder() {
    try { localStorage.setItem(CLE, JSON.stringify(etat)); } catch (e) {}
  }

  function reponseDe(id) {
    return etat.reponses[id] || { ok: false, corr: "" };
  }

  function rafraichirBloc(section) {
    var id = section.getAttribute("data-bloc");
    var rep = reponseDe(id);
    var btnOk = section.querySelector(".rel-btn--ok");
    var btnCorr = section.querySelector(".rel-btn--corr");
    var champ = section.querySelector(".rel-corr");
    var etatTxt = section.querySelector(".rel-etat");
    btnOk.setAttribute("aria-pressed", rep.ok ? "true" : "false");
    btnCorr.setAttribute("aria-pressed", rep.corr ? "true" : "false");
    champ.value = rep.corr || "";
    champ.classList.toggle("is-visible", !!rep.corr || champ.dataset.ouvert === "1");
    section.classList.toggle("rel-bloc--ok", rep.ok && !rep.corr);
    section.classList.toggle("rel-bloc--corr", !!rep.corr);
    etatTxt.textContent = rep.corr ? "Correction notée — merci !" : (rep.ok ? "Noté, merci !" : "");
  }

  function progression() {
    var faits = blocs.filter(function (s) {
      var rep = reponseDe(s.getAttribute("data-bloc"));
      return rep.ok || (rep.corr && rep.corr.trim());
    }).length;
    document.getElementById("rel-rempli").style.width = (faits / blocs.length * 100) + "%";
    document.getElementById("rel-compteur").textContent = faits + " / " + blocs.length + " blocs relus";
  }

  blocs.forEach(function (section) {
    var id = section.getAttribute("data-bloc");
    var btnOk = section.querySelector(".rel-btn--ok");
    var btnCorr = section.querySelector(".rel-btn--corr");
    var champ = section.querySelector(".rel-corr");
    btnOk.addEventListener("click", function () {
      var rep = reponseDe(id);
      rep.ok = !rep.ok;
      if (rep.ok) { rep.corr = ""; champ.dataset.ouvert = ""; }
      etat.reponses[id] = rep;
      sauvegarder(); rafraichirBloc(section); progression();
    });
    btnCorr.addEventListener("click", function () {
      champ.dataset.ouvert = champ.dataset.ouvert === "1" ? "" : "1";
      rafraichirBloc(section);
      if (champ.dataset.ouvert === "1") champ.focus();
    });
    champ.addEventListener("input", function () {
      var rep = reponseDe(id);
      rep.corr = champ.value;
      if (champ.value.trim()) rep.ok = false;
      etat.reponses[id] = rep;
      sauvegarder(); rafraichirBloc(section); progression();
    });
    champ.dataset.ouvert = reponseDe(id).corr ? "1" : "";
    rafraichirBloc(section);
  });
  progression();

  // mention + mot libre
  var radios = document.querySelectorAll('input[name="mention"]');
  radios.forEach(function (r) {
    if (r.value === etat.mention) r.checked = true;
    r.addEventListener("change", function () {
      etat.mention = r.value; sauvegarder();
    });
  });
  var champMot = document.getElementById("rel-mot");
  champMot.value = etat.mot;
  champMot.addEventListener("input", function () {
    etat.mot = champMot.value; sauvegarder();
  });

  document.getElementById("rel-reset").addEventListener("click", function () {
    if (!confirm("Effacer toutes tes réponses et recommencer à zéro ?")) return;
    etat = { reponses: {}, mention: "", mot: "" };
    sauvegarder();
    blocs.forEach(function (s) { s.querySelector(".rel-corr").dataset.ouvert = ""; rafraichirBloc(s); });
    radios.forEach(function (r) { r.checked = false; });
    champMot.value = "";
    progression();
  });

  // compilation
  function compiler() {
    var lignes = [];
    lignes.push("Relecture Kervillage — Enora");
    lignes.push("(envoyé le " + new Date().toLocaleDateString("fr-FR") + ")");
    lignes.push("");
    var sectionCourante = "";
    var groupe = null; // {ok:[], paslu:[], corr:[...]}
    function viderGroupe() {
      if (!groupe) return;
      lignes.push("");
      lignes.push("== " + groupe.titre.toUpperCase() + " ==");
      groupe.corr.forEach(function (c) { lignes.push("• " + c); });
      if (groupe.ok.length) lignes.push("OK : " + groupe.ok.join(", "));
      if (groupe.paslu.length) lignes.push("(pas relu) : " + groupe.paslu.join(", "));
      groupe = null;
    }
    blocs.forEach(function (s) {
      var h2 = s.previousElementSibling;
      while (h2 && !h2.classList.contains("rel-titre") && !h2.classList.contains("rel-soustitre")) {
        h2 = h2.previousElementSibling;
      }
      if (h2 && h2.classList.contains("rel-titre") &&
          (!groupe || h2.textContent !== sectionCourante)) {
        viderGroupe();
        sectionCourante = h2.textContent;
        groupe = { titre: sectionCourante.replace(/^\\d+\\.\\s*/, ""), ok: [], paslu: [], corr: [] };
      }
      var label = s.getAttribute("data-court");
      var rep = reponseDe(s.getAttribute("data-bloc"));
      if (rep.corr && rep.corr.trim()) {
        groupe.corr.push(label + " : CORRECTION — " + rep.corr.trim().replace(/\\s+/g, " "));
      } else if (rep.ok) {
        groupe.ok.push(label);
      } else {
        groupe.paslu.push(label);
      }
    });
    viderGroupe();
    lignes.push("");
    lignes.push("== MENTION COMME RELECTRICE ==");
    lignes.push(etat.mention || "(pas de réponse)");
    if (etat.mot && etat.mot.trim()) {
      lignes.push("");
      lignes.push("== UN MOT POUR FRANCK ==");
      lignes.push(etat.mot.trim());
    }
    return lignes.join("\\n");
  }

  document.getElementById("rel-preparer").addEventListener("click", function () {
    var texte = compiler();
    var sortie = document.getElementById("rel-sortie");
    var champTexte = document.getElementById("rel-texte");
    var lienMail = document.getElementById("rel-mailto");
    var noteMail = document.getElementById("rel-note-mail");
    var noteLong = document.getElementById("rel-note-long");
    champTexte.value = texte;
    var uri = "mailto:contact@brozapi.com?subject=" +
      encodeURIComponent("Relecture Kervillage — Enora") +
      "&body=" + encodeURIComponent(texte);
    if (texte.length <= LIMITE_MAILTO) {
      lienMail.href = uri;
      lienMail.style.display = "";
      noteMail.hidden = false;
      noteLong.hidden = true;
      window.location.href = uri; // ouvre la messagerie, tout est pré-rempli
    } else {
      lienMail.style.display = "none";
      noteMail.hidden = true;
      noteLong.hidden = false;
    }
    sortie.classList.add("is-visible");
    sortie.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  document.getElementById("rel-copier").addEventListener("click", function () {
    var champTexte = document.getElementById("rel-texte");
    var etatCopie = document.getElementById("rel-copie-etat");
    function ok() { etatCopie.textContent = "Copié ! Tu peux le coller dans Messenger ou un email."; }
    function manuel() {
      champTexte.focus(); champTexte.select();
      try { document.execCommand("copy"); ok(); }
      catch (e) { etatCopie.textContent = "Sélectionne le texte ci-dessus et copie-le (appui long → Copier)."; }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(champTexte.value).then(ok, manuel);
    } else { manuel(); }
  });
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
