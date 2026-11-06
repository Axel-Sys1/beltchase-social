# BeltChase · publication Instagram automatique

File de posts pour @beltchase.officiel, publiée par l'API officielle d'Instagram.

- `queue.json` : les posts (heure de Paris, type `post` ou `story`, image, légende, statut).
- Statuts : `pending` (à valider par Axel) → `approved` (partira à l'heure) → `posted` (ou `failed` après 3 essais).
- `img/` : les visuels (faits dans `beltchase/marketing/pub.html`).
- `.github/workflows/publish.yml` : toutes les 15 min, publie ce qui est `approved` et dont l'heure est passée.
- Secret GitHub `IG_TOKEN` : jeton Instagram longue durée (60 jours, renouvelé automatiquement depuis le Mac).

Les stories partent sans sticker (l'API ne sait pas en mettre) : sondage et compte à rebours restent à ajouter au téléphone si besoin.
