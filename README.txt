HELICO RESTO — VERSION 5.4.0
================================

OBJECTIF
Reconstruire l’interface d’accueil au plus près de la maquette fournie :
photo d’une villa gastronomique avec hélicoptère au coucher du soleil,
logo blanc/doré à gauche, cœur + menu à droite, titre en italique,
barre de recherche blanche, quatre raccourcis vitrés et navigation sombre.
L’icône de l’écran d’accueil reprend l’image présente à droite de la maquette.

CONTENU DE L’ARCHIVE (TOUS À LA RACINE)
- index.html : application complète, catalogue inclus et photos d’accueil intégrées.
- README.txt : ce document.
- apple-touch-icon.png : icône iPhone 180×180.
- icon-192.png : icône PWA 192×192.
- icon-512.png : icône PWA 512×512.
- manifest.webmanifest : manifeste de l’application installable.

FONCTIONS CONSERVÉES
- Recherche de restaurant, commune ou mot-clé avec suggestions.
- Guide des établissements, filtres, accès aux fiches.
- Carte des points existants avec Leaflet / OpenStreetMap : Internet requis.
- Favoris locaux.
- Ajout/édition locale via « Ajouter » ; ce n’est pas un serveur partagé.
- Bouton « Autour de moi » (autorisation de géolocalisation nécessaire).
- Diaporama photo ; premier visuel reconstitué depuis la maquette
  fournie, autres visuels illustratifs.

INSTALLATION SUR GITHUB PAGES
1. Décompresser le ZIP.
2. Copier LES SIX fichiers de l’archive à la RACINE du dépôt GitHub.
3. Remplacer l’ancien index.html et publier (Commit changes).
4. Attendre le déploiement GitHub Pages et recharger le site.
5. Sur iPhone : supprimer l’ancienne icône de l’écran d’accueil.
   Ouvrir le site dans Safari puis Partager > Sur l’écran d’accueil.

NOTE IMPORTANTE
Il faut publier aussi les fichiers .png et manifest.webmanifest ;
contrairement aux versions précédentes, l’icône iPhone utilise une
véritable image dédiée pour mieux fonctionner sur iOS.
Les visuels artistiques ne constituent pas des photos authentifiées de
l’état des hélisurfaces. Avant tout vol, vérifier les autorisations,
les données aéronautiques et les conditions auprès des sources officielles.
