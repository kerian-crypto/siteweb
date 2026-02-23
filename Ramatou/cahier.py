
CAHIER DES CHARGES : Plateforme E-commerce UNKNOW

Date : 18/02/2026
By DigitalGetServices

1. Présentation du Projet
1.1. Contexte
L'entrepreneur UNKNOW, experte dans le domaine de la nutrition, souhaite digitaliser son activité afin de commercialiser des produits physiques (alimentaires) et des ressources numériques (livres de recettes, fiches techniques nutritionnelles).
1.2. Objectifs
•	Fournir une vitrine professionnelle pour la marque.
•	Automatiser la vente et la distribution des produits numériques.
•	Simplifier la gestion des stocks et des commandes de produits alimentaires.
•	Instaurer un système de retrait sécurisé via QR Code en kiosques physiques.

2. Spécifications Fonctionnelles
2.1. Espace Client (FrontOffice)
•	Catalogue Hybride : Affichage dynamique des produits avec filtres par catégories (Physique / Numérique).
•	Système de Notation : Évaluation des produits manuscrits via un système d'étoiles (1 à 5) et commentaires vérifiés.
•	Processus d'achat :
o	Paniers multiproduits.
o	Paiement via agrégateurs de monnaie mobile (Orange Money/Mobile Money).
•	Expérience Post-Achat :
o	Numérique : Accès immédiat au téléchargement après validation du paiement.
o	Physique : Génération automatique d'un Coupon QR Code unique.
•	Communication : Interface de chat en temps réel avec l'administratrice (support client).
2.2. Dashboard Administrateur (Back-Office)
•	Gestion du Catalogue :
o	Ajout de produits (Nom, prix, images, description).
o	Gestion de la gratuité (Produits "Lead Magnet" vs Payants).
o	Configuration des stocks (quantité minimale, alertes).
•	Gestion des Commandes & Logistique :
o	Modification des dates de livraison (par défaut J+1).
o	Statut des commandes (En préparation, Prête, Livrée).
•	CRM (Gestion Utilisateurs) :
o	Fiche client détaillée : historique d'achats, dates, quantités et volume d'affaires généré par utilisateur.
•	Module de Validation Kiosque :
o	Scanner intégré pour valider les coupons.
o	Désactivation automatique du coupon après usage avec horodatage.

3. Fonctionnalités Additionnelles Préconisées
Afin d'optimiser la rentabilité et la sécurité de l'application, les modules suivants sont intégrés :
•	Système de Facturation Automatique : Génération d'une facture PDF envoyée par e-mail après chaque transaction.
•	Protection des Médias : Mise en place d'un système de filigrane (Water mark) sur les aperçus des fiches techniques pour éviter le vol de contenu.
•	Notifications Push/SMS : Alerte automatique au client lorsque sa commande est prête au kiosque ou pour confirmer un rendez-vous conseil.
•	Dashboard Statistique (KPIs) : Visualisation graphique du chiffre d'affaires, du panier moyen et des produits les plus vendus.
•	SEO & Optimisation Mobile : Structure optimisée pour le référencement naturel et interface "Mobile-First" (essentiel pour les paiements mobiles).

4. Spécifications Techniques
4.1. Architecture logicielle
•	Interface (Frontend) : Framework moderne (React.js ou Vue.js) pour une navigation fluide sans rechargement de page.
•	Serveur (Backend) : Architecture robuste (Node.js/Express ou Laravel) gérant les communications en temps réel (Web Sockets).
•	Base de données : Relationnelle (PostgreSQL ou MySQL) pour garantir l'intégrité des données financières.
4.2. Sécurité
•	Chiffrement SSL (HTTPS).
•	Sécurisation des accès API par tokens (JWT).
•	Sauvegarde quotidienne automatisée de la base de données.


