# HELICO RESTO — application professionnelle PWA

**Version 2.0 · 13 novembre 2026** — Annuaire de destinations gastronomiques avec informations d'hélisurface.

## Ce qui est réellement inclus

- **20 fiches initiales** lues et recoupées avec HelicoResto.com, toutes avec coordonnées GPS et liens vers la page source.
- **20 photos choisies individuellement pour leur correspondance avec les établissements**, et **aucune image générique**. Les images initiales restent chargées depuis des sites de tiers (elles **ne sont pas incluses dans le ZIP**), peuvent ne pas s'afficher, et leur réutilisation doit respecter les droits des propriétaires. Vérifier les droits d'exploitation avant une diffusion commerciale.
- Interface mobile **Accueil / Explorer / Carte / Favoris / Plus**, fiches avec onglets **Le lieu / Hélisurface / Pratique / Photos**, recherche instantanée, filtres, carte Leaflet, partage, appel téléphonique, copie GPS, favoris persistants et édition locale.
- PWA installable depuis Safari. Navigation et fiches intégrées accessibles hors connexion après installation/cache ; les fonds de carte et photos externes nécessitent Internet.
- **Collecteur Python** et **GitHub Actions** pour découvrir progressivement les pages accessibles du site, analyser les textes et associer **seulement les photographies hébergées sur la fiche HelicoResto correspondante**. Les images collectées sont transformées en WebP local, le catalogue JSON est mis à jour, et le site republié.

**IMPORTANT :** HelicoResto.com affiche « plus de 220 hélisurfaces ». Ce chiffre est celui annoncé par le site, pas le nombre importé et vérifié. Depuis notre environnement de préparation, l'accès réseau direct au domaine était bloqué : nous n'avons **pas** exécuté ni contrôlé un aspirateur complet de ces 220 fiches. Le collecteur pourra fonctionner dans GitHub Actions selon l'accès réseau, le robots.txt et la structure des pages. Le résultat réel est écrit dans `data/sync_report.json` ; **ne pas annoncer un catalogue exhaustif avant validation du rapport**.

## Publier sur GitHub Pages (dépôt `helicoresto-app`)

1. Créer un dépôt GitHub public `helicoresto-app`, avec la branche **main**.
2. Décompresser le ZIP puis envoyer **tous les fichiers et dossiers à la racine du dépôt**. À la racine, on doit notamment voir `index.html`, `app.js`, `style.css`, `data`, `assets`, `scripts`, `.github`.
3. Dans le dépôt, ouvrir **Settings > Pages**, et sous **Build and deployment > Source**, choisir **GitHub Actions** (et non « Deploy from a branch »).
4. Dans l'onglet **Actions**, lancer **Synchroniser HelicoResto et publier l'application > Run workflow**. Le workflow se lance aussi à chaque modification de `main` et automatiquement le lundi à 04:10 UTC.
5. Consulter le résultat via `https://VOTRE-PSEUDO.github.io/helicoresto-app/` et le rapport `data/sync_report.json`. Selon les règles GitHub, un déploiement Pages peut demander l'autorisation d'activer les workflows.
6. Sur iPhone dans Safari : **Partager > Sur l'écran d'accueil**.

## Modifier les fiches

Dans **Plus > Gérer les établissements**, on peut ajouter ou modifier les fiches, sans réinstaller l'application. Ces modifications sont enregistrées **localement uniquement** sur l'appareil utilisé, avec export/import JSON. Pour publier une modification pour tous les visiteurs, éditer `data/venues.json` sur GitHub. Le collecteur conserve les fiches existantes lorsqu'il ne peut pas relire le site.

Le fichier `data/fallback-data.js` contient le miroir des données pour permettre d'ouvrir l'interface hors serveur. Il est régénéré pendant la synchronisation ; ne pas oublier de le mettre à jour en cas de modifications manuelles de `venues.json`.

## Actualisation automatique depuis le site

Le script `scripts/sync_helicoresto.py` :

- consulte la politique `robots.txt` quand disponible et effectue des requêtes espacées de 350 ms (modifiable), plafonnées à 1 300 requêtes ;
- découvre les pages via les sitemaps WordPress, menus et paginations, et parcourt uniquement le domaine HelicoResto ;
- ne reconnaît une fiche que si des sections liées à l'hélisurface et aux informations pratiques sont présentes ;
- extrait nom, ville, département, catégorie, GPS, téléphone, informations pratiques, observations, et images propres à cette fiche ;
- télécharge au plus six photographies sur le domaine d'origine **HelicoResto**, en éliminant les petits logos et avatars, et en privilégiant les grandes photos associées au nom ;
- met les fichiers dans `assets/venues/`, conserve les données existantes quand elles ne sont pas récupérées et inscrit les erreurs dans `data/sync_report.json`.

**Limites :** selon les protections anti-aspiration, la pagination Javascript, les sitemaps et l'évolution des modèles de pages, certaines fiches peuvent rester absentes ou incomplètes. Vérifier le rapport, les textes, les photos et les coordonnées avant d'annoncer la base comme complète. L'association automatique de photographies reste une présélection nécessitant contrôle éditorial.

Exécution locale sur un ordinateur qui a accès au domaine :

```bash
pip install -r scripts/requirements.txt
python scripts/sync_helicoresto.py --limit 1300 --delay .35
```

## Sécurité / responsabilité

Les indications d'approche sont des observations historiques, pas des consignes de navigation. Confirmer avant chaque vol : **droit de poser auprès du propriétaire, carte aéronautique officielle à jour, NOTAM, météo, CTR, restrictions, obstacles, terrain, appareil et capacité du pilote.** La simple présence d'une fiche n'établit ni la légalité ni la disponibilité actuelle d'une hélisurface.


## Correctif V3 — écran de chargement
Le catalogue embarqué s'affiche immédiatement, même sans réseau. Le catalogue JSON se recharge ensuite en arrière-plan avec un délai maximal de 3,5 secondes. Le service worker privilégie la dernière version en ligne et vide les anciens caches.

Pour publier : extraire tout le ZIP à la racine du dépôt (incluant `data/` et `assets/`), puis recharger l'application iPhone. Si l'ancienne version persiste, retirer l'icône de l'écran d'accueil et l'ajouter à nouveau après la publication.
