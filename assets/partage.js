/* Kervillage — generation de l'image de partage (canvas, 100 % navigateur). */
(function (root) {
  "use strict";

  function lignes(ctx, texte, maxLargeur) {
    var mots = texte.split(" ");
    var out = [];
    var courant = "";
    mots.forEach(function (m) {
      var essai = courant ? courant + " " + m : m;
      if (ctx.measureText(essai).width > maxLargeur && courant) {
        out.push(courant);
        courant = m;
      } else {
        courant = essai;
      }
    });
    if (courant) out.push(courant);
    return out;
  }

  function genererImage(fiche) {
    var W = 1200, H = 630;
    var canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    var ctx = canvas.getContext("2d");

    // fond papier
    ctx.fillStyle = "#f7f3ea";
    ctx.fillRect(0, 0, W, H);
    // filet haut
    ctx.fillStyle = "#0e4f5c";
    ctx.fillRect(0, 0, W, 14);

    var marge = 90;

    // nom francais
    ctx.fillStyle = "#4c5a54";
    ctx.font = "600 34px -apple-system, 'Segoe UI', Roboto, sans-serif";
    ctx.fillText(fiche.nomFr.toUpperCase().split("").join(" "), marge, 150);

    // nom breton en grand
    ctx.fillStyle = "#0e4f5c";
    var taille = 110;
    ctx.font = "700 " + taille + "px Georgia, 'Times New Roman', serif";
    while (ctx.measureText(fiche.nomBr).width > W - 2 * marge && taille > 44) {
      taille -= 6;
      ctx.font = "700 " + taille + "px Georgia, 'Times New Roman', serif";
    }
    ctx.fillText(fiche.nomBr, marge, 150 + taille + 20);

    // phrase de sens
    var y = 150 + taille + 90;
    ctx.fillStyle = "#1d2a26";
    ctx.font = "400 32px Georgia, serif";
    var ls = lignes(ctx, fiche.sens, W - 2 * marge);
    ls.slice(0, 3).forEach(function (l, i) {
      ctx.fillText(l, marge, y + i * 44);
    });

    // pied
    ctx.fillStyle = "#a5772a";
    ctx.font = "700 26px -apple-system, 'Segoe UI', Roboto, sans-serif";
    ctx.fillText("KERVILLAGE", marge, H - 70);
    ctx.fillStyle = "#4c5a54";
    ctx.font = "400 26px -apple-system, 'Segoe UI', Roboto, sans-serif";
    ctx.fillText("kervillage.brozapi.com", marge + 220, H - 70);

    return canvas;
  }

  function telecharger(canvas, nomFichier) {
    canvas.toBlob(function (blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = nomFichier;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }, "image/png");
  }

  root.KVPartage = { genererImage: genererImage, telecharger: telecharger };
})(window);
