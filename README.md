# HELICO RESTO — Application web mobile (PWA)

## Installation
Décompressez le ZIP, puis publiez le contenu du dossier `helicoresto-app` sur un hébergement HTTPS (GitHub Pages, Netlify, Vercel…). Ouvrez l'URL sur iPhone dans Safari, puis utilisez Partager > Sur l'écran d'accueil. Pour tester sur ordinateur, lancez `python3 -m http.server 8080` dans ce dossier et ouvrez http://localhost:8080.

## Fonctions
Accueil, recherche, filtres, fiches, favoris, carte OpenStreetMap (Leaflet), édition locale, import/export JSON, mode installable et cache PWA.

## Limites de cette première version
- Le site public HelicoResto.com annonce plus de 220 hélisurfaces, mais **8 fiches de départ** sont intégrées dans cette version. Ce n'est pas une extraction exhaustive.
- Deux fiches ont des coordonnées GPS vérifiées sur les pages sources. Les autres ne sont pas placées arbitrairement sur la carte.
- Les photographies sont des illustrations génériques, pas des photographies certifiées des établissements.
- L'édition et les favoris sont sauvegardés dans le navigateur, sans compte ni base de données distante. Les mises à jour ne sont pas publiées automatiquement.
- Les informations aéronautiques sont indicatives, non destinées à la navigation, et doivent être confirmées avant chaque vol.
- Le fonctionnement hors connexion est partiel (fonds de carte et photos externes nécessitent une connexion).

Sources principales : https://www.helicoresto.com/ ; https://www.helicoresto.com/region-sud-est/le-domaine-de-verchant/ ; https://www.helicoresto.com/region-sud-est/chateau-de-fonscolombe/
