# HELICO RESTO — application web mobile

Application PWA statique à déployer sur GitHub Pages. Le dépôt doit contenir **index.html à la racine**.

## État du catalogue

Cette livraison contient **20 fiches de départ**, dont **15 fiches avec une URL de photo associée au lieu**. Ce n'est **pas** une copie intégrale des plus de 220 hélisurfaces annoncées par le site source. Les photos ne sont pas embarquées : elles sont appelées depuis les sites hébergeurs et peuvent devenir indisponibles. Vérifier les droits d'utilisation et obtenir l'autorisation de reproduction avant toute diffusion commerciale.

## Fonctionnalités

Accueil, recherche, catégories, filtres régionaux, carte Leaflet/OpenStreetMap, fiches (informations aéronautiques, contacts, photos), favoris persistants, partage, édition locale, import/export JSON, installation PWA. La carte nécessite une connexion pour les fonds OpenStreetMap. Les modifications depuis l'éditeur sont locales au navigateur et ne modifient pas le dépôt.

## GitHub Pages

1. Créer le dépôt `helicoresto-app` (public si GitHub Pages gratuit).
2. Ajouter **le contenu** de ce dossier à la racine du dépôt.
3. Dans **Settings > Pages**, sélectionner **Deploy from a branch**, branche `main`, dossier `/ (root)`.
4. Ouvrir l'URL publiée puis « Sur l'écran d'accueil » depuis Safari sur iPhone.

## Importation complémentaire

Le workflow **Actions > Prévisualiser les fiches HelicoResto > Run workflow** lance une collecte prudente des pages publiques identifiées dans les sitemaps, en respectant `robots.txt`. Il crée un artefact `fiches-a-verifier` contenant `import-review.json`. **Il ne publie pas automatiquement** les nouvelles fiches : les coordonnées, les autorisations d'atterrissage, les images et les données de sécurité doivent être revues manuellement avant intégration dans `data/venues.json` et `data/fallback-data.js`.

Pour lancer localement : `pip install requests beautifulsoup4` puis `python scripts/sync_catalog.py`.

## Sécurité aéronautique

Le guide ne remplace pas les publications officielles, la réglementation, les autorisations de poser, les NOTAM ni la reconnaissance de la zone. Certaines informations historiques peuvent être périmées, et certains établissements peuvent ne plus accepter d'hélicoptères. **Toujours vérifier directement avant le vol.**
