# GrieeLive E-commerce (Flask)

Plateforme multi-pages avec authentification client, catalogue segmenté et dashboard administrateur.
Refonte UI modulaire avec palette personnalisée:
`#7FA834 #568319 #194118 #26190F #8C1B6D #D02893`.

## Parcours pages
- `/` : page d'accueil simple (visualisation produits uniquement, sans commande).
- `/auth` : page login/register.
- `/shop` : accueil complet du site (commande, chat, notation).
- `/nutrition` : page produits nutritionnels (physiques).
- `/fiches-techniques` : page fiches techniques / contenus numériques.
- `/bibliographie` : page bibliographie.
- `/mes-achats` : page personnelle avec coupons, fiches et produits achetés.
- `/admin` : dashboard administrateur.

## Fonctionnalités
- Authentification session Flask (inscription/connexion/déconnexion).
- Protection CSRF (meta + header `X-CSRF-Token` + champs cachés formulaires).
- Décorateurs d'accès: `login_required` (user) et `admin_required` (admin).
- Catalogue hybride filtrable et panier partagé via `localStorage`.
- Paiement mobile simulé (Orange Money / Mobile Money).
- Téléchargement immédiat des produits numériques.
- Coupon QR unique pour retrait kiosque de produits physiques.
- Historique client (`/mes-achats`) avec téléchargements + coupons.
- Avis produits (étoiles + commentaire).
- Chat style messagerie (type WhatsApp) user/admin avec pièces jointes:
- images, documents, vidéos.
- Contrôle/modération admin sur les messages (visible/hidden).
- Dashboard admin (KPI, commandes, CRM, validation coupon, ajout produit).

## Architecture Frontend Modulaire
- `templates/partials/` : composants communs (`header`, `footer`).
- `static/css/main.css` : point d'entrée styles.
- `static/css/core/` : tokens, base, layout.
- `static/css/components/` : boutons, cartes, formulaires, panneaux, contenus.
- `static/css/pages/` : styles spécifiques par page.
- `static/js/core/` : API, formatage, storage.
- `static/js/features/` : catalogue, panier, checkout, chat.
- `static/js/pages/` : scripts d'entrée par page (`public`, `shop`, `products`, `purchases`).

## Architecture Backend
- `Blueprint user` : routes publiques + espace client + APIs utilisateur.
- `Blueprint admin` : dashboard + APIs d'administration.
- `security.py` : CSRF + décorateurs `login_required` / `admin_required`.
- `services.py` : logique métier (factures, coupons, chat, pièces jointes, seed/migration).

## Lancer le projet
```bash
python -m pip install -r requirements.txt
python app.py
```

## Accès
- Site: `http://127.0.0.1:5000/`
- Admin: `http://127.0.0.1:5000/admin`
- Identifiants admin: `ramatou@gmail.com` / `ramatouAdmin`
