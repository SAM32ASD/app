# XAUUSD Trading App - Suivi des Taches

> Derniere mise a jour : 2026-05-01

---

## Legende

| Statut | Signification |
|--------|---------------|
| `[ ]`  | A faire (TODO) |
| `[~]`  | En cours (IN PROGRESS) |
| `[x]`  | Termine (DONE) |
| `[!]`  | Bloque (BLOCKED) |

---

## Phase 1 : Fondation & Infrastructure (Semaines 1-2)

### 1.1 Hebergement & VPS
- [ ] Creer un compte Oracle Cloud (Always Free)
- [ ] Provisionner l'instance ARM (4 OCPU / 24 GB RAM / 200 GB disk / Ubuntu 22.04)
- [ ] Configurer l'acces SSH et la securite reseau (firewall, ports)
- [ ] Installer Docker + Docker Compose sur le VPS

### 1.2 Base de donnees & Cache
- [ ] Ecrire le `docker-compose.yml` (PostgreSQL 15 + Redis 7)
- [ ] Creer les migrations SQL initiales (tables: users, trading_configs, trade_logs, active_positions, audit_logs)
- [ ] Tester la connectivite PostgreSQL + Redis
- [ ] Installer un outil d'admin BDD (Adminer ou PgAdmin)

### 1.3 Firebase
- [ ] Creer le projet Firebase (plan Spark gratuit)
- [ ] Configurer Firebase Authentication (Email/Password + Google Sign-In)
- [ ] Initialiser Cloud Firestore (collections: users, global_settings, app_version)
- [ ] Configurer Firebase Cloud Messaging (push notifications)
- [ ] Noter et securiser les cles d'API Firebase

### 1.4 Repo & CI/CD
- [ ] Creer le repo GitHub (mono-repo: `backend/`, `frontend/`, `infra/`)
- [ ] Configurer GitHub Actions : lint + tests Python
- [ ] Configurer GitHub Actions : build Flutter Web
- [ ] Configurer GitHub Actions : deploiement SSH vers VPS sur tag `v*`

### 1.5 DNS & SSL
- [ ] Configurer un domaine sur Cloudflare (plan Free)
- [ ] Pointer le DNS vers le VPS Oracle
- [ ] Activer le proxy Cloudflare + SSL

---

## Phase 2 : Connecteur Marche & Donnees (Semaines 3-4)

### 2.1 Connexion MetaTrader
- [ ] Creer un compte MetaApi (plan Free) OU installer MT5 headless sur le VPS
- [ ] Implementer le service `MetaApiConnector` (connexion au compte Exness XAUUSD)
- [ ] Tester la reception des ticks en temps reel
- [ ] Gerer la reconnexion automatique en cas de perte de connexion

### 2.2 Market Data Feed
- [ ] Implementer `MarketDataFeed` : reception et stockage des ticks dans Redis Stream
- [ ] Implementer le buffer circulaire de 200 ticks (deque)
- [ ] Stocker le dernier tick dans `market:xauusd:last_tick` (Redis)

### 2.3 Micro-Timeframe Builder
- [ ] Implementer `MicroTimeframeBuilder` : agregation des ticks en barres OHLC synthetiques
- [ ] Supporter les periodes : 5s, 10s, 15s, 20s, 30s
- [ ] Valider les barres generees vs donnees MQL5 de reference

### 2.4 Indicateurs techniques
- [ ] Calculer RSI sur M1/M5 (ta-lib ou pandas-ta)
- [ ] Calculer ATR sur M1/M5/H1
- [ ] Calculer ADX sur M1/M5
- [ ] Exposer les valeurs via endpoint API `/market/indicators`

### 2.5 Support & Resistance
- [ ] Implementer `SupportResistanceEngine` : detection de pics/creux locaux (scipy.signal.find_peaks)
- [ ] Detection S/R sur H4 (`DetectKeyLevels`)
- [ ] Detection S/R sur micro-timeframes (`DetectMicroSR`)
- [ ] Exposer via endpoint API `/market/sr-levels`

---

## Phase 3 : Moteur de Trading Core (Semaines 5-8)

### 3.1 Sniper AI Engine
- [ ] Implementer `SniperAIEngine` avec buffer circulaire 200 ticks
- [ ] Porter `SniperCollectTick()` : dedoublonnage time + prix
- [ ] Porter `SniperEvaluate()` : calcul momentum, acceleration, RSI micro, volume tick
- [ ] Systeme de scoring 0-100 avec poids configurables
- [ ] Determination de la direction (BUY/SELL/NEUTRE)
- [ ] Tests unitaires : valider le score vs comportement EA MQL5

### 3.2 Signal Engine (Pattern Detection)
- [ ] Implementer `PatternDetector` : detection Hammer sur barres synthetiques
- [ ] Detection Engulfing (bullish/bearish)
- [ ] Detection Doji
- [ ] Confluence avec RSI/ADX pour confirmation du signal
- [ ] Generer signal final BUY/SELL/NEUTRE avec niveau de confiance

### 3.3 Dynamic SL Calculator
- [ ] Implementer `DynamicSLCalculator` : methode ATR adaptatif
- [ ] Methode Swings (lookback sur derniers swings)
- [ ] Methode S/R (SL place sous/sur le niveau S/R le plus proche)
- [ ] Methode Hybride (combinaison ponderee des 3 methodes)
- [ ] Respecter les bornes min/max SL configurables
- [ ] Tests unitaires avec scenarios de marche

### 3.4 Risk Manager
- [ ] Implementer `RiskManager` : calcul des lots selon solde courant
- [ ] Formule de Kelly adaptee + tick value XAUUSD
- [ ] Ajustement lots selon volatilite courante
- [ ] Verification marge disponible avant envoi d'ordre
- [ ] Limites : risk_percent, max_daily_loss_percent, max_consecutive_losses

### 3.5 Execution Manager
- [ ] Implementer `ExecutionManager` : envoi d'ordres Buy/Sell/Stop via MetaApi
- [ ] Grille multi-ordres (`SendMultiBuyOrders` / `SendMultiSellOrders`)
- [ ] Gestion des index de grille par position
- [ ] Systeme de cooldowns entre les ordres
- [ ] Filtres pre-execution : spread, marge, gap, RSI, ADX, volatilite

### 3.6 Position Tracker
- [ ] Implementer `PositionTracker` : synchronisation des positions actives avec MT5
- [ ] Mise a jour de la table `active_positions` en temps reel
- [ ] Detection des positions fermees (par SL/TP ou manuellement)
- [ ] Gestion du grid_index par position

### 3.7 Trailing & Break-Even Manager
- [ ] Implementer `TrailingStopManager` : scan continu toutes les 1s
- [ ] Trailing par paliers (steps configurables)
- [ ] Mode rapide (rapid_mode) pour positions en fort profit
- [ ] Break-Even (BE) : deplacer SL au prix d'entree apres X pips de profit
- [ ] Time-based BE : activer apres un delai si le trade stagne
- [ ] Modification du SL via API MetaApi

### 3.8 Volatility Monitor
- [ ] Implementer `VolatilityMonitor` : calcul ATR temps reel
- [ ] True Range, Normalized ATR
- [ ] Ratio de volatilite (mode Haute Volatilite)
- [ ] Stocker dans `market:volatility:current` (Redis)
- [ ] Ajuster le comportement du moteur en mode HV

### 3.9 Session Manager
- [ ] Implementer `SessionManager` : reset quotidien a 00:00 UTC (APScheduler)
- [ ] Compteur de trades journalier (`session:today:trades_count`)
- [ ] Compteur de pertes consecutives (`session:today:consecutive_losses`)
- [ ] P&L realise journalier (`session:today:realized_pl`)
- [ ] Heures de trading programmables (scheduled_start_time / scheduled_stop_time)
- [ ] Arret automatique si limite quotidienne atteinte

---

## Phase 4 : API Backend & Temps Reel (Semaines 9-10)

### 4.1 Structure FastAPI
- [ ] Initialiser le projet FastAPI (structure: routers, services, models, schemas)
- [ ] Configurer Uvicorn (2 workers, host 0.0.0.0, port 8000)
- [ ] Endpoint health check : `GET /health`
- [ ] Documentation Swagger UI automatique

### 4.2 Authentification & Middleware
- [ ] Middleware de verification JWT Firebase sur chaque requete
- [ ] Extraction du role utilisateur depuis le token / Firestore
- [ ] Decorateurs de permission par role (admin, trader, viewer)
- [ ] Rate limiting via Redis (ex: 10 requetes/minute)
- [ ] IP Whitelisting optionnel pour les routes admin

### 4.3 Endpoints Trading
- [ ] `POST /auth/verify` : verification token Firebase + creation session
- [ ] `GET /trading/status` : etat du robot, P&L, volatilite, positions
- [ ] `POST /trading/start` : demarrer le moteur (Admin/Trader)
- [ ] `POST /trading/stop` : arreter le moteur proprement (Admin/Trader)
- [ ] `POST /trading/emergency-stop` : fermer TOUTES les positions immediatement (Admin)
- [ ] `GET /trading/config` : recuperer la configuration active
- [ ] `PUT /trading/config` : mettre a jour les parametres (Admin)
- [ ] `GET /trading/positions` : liste des positions ouvertes
- [ ] `GET /trading/history` : historique des trades (pagine)

### 4.4 Endpoints Admin
- [ ] `GET /admin/users` : liste des utilisateurs et statut online/offline
- [ ] `PUT /admin/users/{id}/role` : changer le role d'un utilisateur
- [ ] `GET /admin/audit` : logs d'audit (pagine)

### 4.5 WebSocket Server
- [ ] Implementer `WebSocketManager` : gestion des connexions clients
- [ ] Endpoint `WS /ws/trading` : canal temps reel
- [ ] Event `tick.update` : dernier prix XAUUSD + spread
- [ ] Event `position.update` : liste positions + P&L flottant
- [ ] Event `trade.closed` : ticket ferme + profit/perte
- [ ] Event `volatility.alert` : niveau volatilite + mode HV
- [ ] Event `robot.status` : RUNNING / STOPPED / ERROR
- [ ] Event `emergency.triggered` : notification arret d'urgence

### 4.6 Synchronisation Firestore <-> PostgreSQL
- [ ] Sync des profils utilisateurs (Firestore -> PostgreSQL)
- [ ] Sync de la config globale (Firestore -> Redis/PostgreSQL)
- [ ] Persistence des parametres modifies depuis l'app

---

## Phase 5 : Frontend Flutter (Semaines 10-12)

### 5.1 Architecture Flutter
- [ ] Choisir et configurer le state management (Provider / Riverpod / GetX)
- [ ] Configurer le client HTTP (dio ou http)
- [ ] Configurer le client WebSocket
- [ ] Integrer le SDK Firebase (Auth + Firestore + Messaging)
- [ ] Definir le systeme de routing / navigation
- [ ] Creer le theme global de l'app (couleurs, typographie, dark mode)

### 5.2 Ecran Auth
- [ ] Page de Login (Email/Password)
- [ ] Page de Register
- [ ] Mot de passe oublie (Firebase)
- [ ] Login via Google Sign-In
- [ ] Redirection post-login selon le role

### 5.3 Trading Dashboard
- [ ] Affichage etat du robot (ON/OFF avec indicateur visuel)
- [ ] P&L du jour (temps reel via WebSocket)
- [ ] Solde courant du compte
- [ ] Indicateur de volatilite en temps reel
- [ ] Liste des positions ouvertes (detail : ticket, type, lots, SL, TP, profit flottant)
- [ ] Graphique des trades (historique P&L)
- [ ] Dernier prix XAUUSD + spread en temps reel

### 5.4 Control Panel
- [ ] Slider risque (%) avec validation min/max
- [ ] Input heures de demarrage/arret automatique
- [ ] Toggle Sniper AI (on/off)
- [ ] Toggle Micro-Timeframes (on/off)
- [ ] Parametres SL : methode (ATR/Swings/SR/Hybride), min, max
- [ ] Parametres de grille (max positions par direction, total)
- [ ] Toggle hedging
- [ ] Bouton START / STOP du robot
- [ ] Bouton **ARRET D'URGENCE** (rouge, confirmation obligatoire)

### 5.5 Admin Panel
- [ ] Tableau des utilisateurs (nom, email, role, online/offline, derniere connexion)
- [ ] Attribution/modification des roles (admin, trader, viewer)
- [ ] Vue des trades en cours par utilisateur
- [ ] Parametres globaux override (config qui s'applique a tous)
- [ ] Consultation des logs d'audit

### 5.6 Notifications
- [ ] Integration Firebase Cloud Messaging (FCM)
- [ ] Notification push : perte journaliere atteinte
- [ ] Notification push : robot demarre / arrete
- [ ] Notification push : arret d'urgence declenche
- [ ] Notification push : position fermee (profit/perte)

---

## Phase 6 : Integration, Tests & Production (Semaines 13-14)

### 6.1 Tests Backend
- [ ] Tests unitaires : SniperAIEngine (scoring, direction)
- [ ] Tests unitaires : PatternDetector (chaque pattern)
- [ ] Tests unitaires : DynamicSLCalculator (chaque methode)
- [ ] Tests unitaires : RiskManager (calcul lots, limites)
- [ ] Tests unitaires : SessionManager (reset, compteurs)
- [ ] Backtesting sur 1 mois de ticks historiques XAUUSD
- [ ] Rapport de performance (win rate, profit factor, max drawdown)

### 6.2 Tests Integration
- [ ] Tests API <-> MetaApi (execution d'ordres sur compte demo)
- [ ] Tests API <-> PostgreSQL (CRUD complet)
- [ ] Tests API <-> Redis (cache, pub/sub)
- [ ] Tests WebSocket (connexion, events, deconnexion)
- [ ] Tests Auth (JWT Firebase, roles, permissions)

### 6.3 Tests Frontend
- [ ] Tests end-to-end : parcours login -> dashboard -> control panel
- [ ] Tests end-to-end : scenario admin (gestion users, override config)
- [ ] Tests end-to-end : arret d'urgence
- [ ] Tests de compatibilite (Web, Android, iOS)

### 6.4 Deploiement Production
- [ ] Finaliser `docker-compose.prod.yml`
- [ ] Configurer les variables d'environnement de production (.env)
- [ ] Deployer sur VPS Oracle (Docker Compose)
- [ ] Verifier que tous les services demarrent correctement
- [ ] Tester sur compte demo Exness pendant 1 semaine minimum
- [ ] Valider les performances (latence, consommation RAM/CPU)

### 6.5 Monitoring & Observabilite
- [ ] Configurer UptimeRobot : ping `GET /health` toutes les 5 min
- [ ] Deployer Prometheus + Grafana en Docker
- [ ] Dashboard Grafana : nombre de trades, latence API, P&L, uptime
- [ ] Rotation des logs (logrotate sur docker logs)
- [ ] Alertes : robot down, perte journaliere atteinte, erreur critique

### 6.6 Documentation
- [ ] README.md du repo (installation, configuration, deploiement)
- [ ] Documentation API (endpoints, payloads, exemples)
- [ ] Guide de deploiement VPS Oracle
- [ ] Procedure de restauration en cas de panne

---

## Recapitulatif

| Phase | Taches | Terminees | Restantes |
|-------|--------|-----------|-----------|
| 1. Infrastructure | 16 | 0 | 16 |
| 2. Marche & Donnees | 15 | 0 | 15 |
| 3. Moteur Trading | 33 | 0 | 33 |
| 4. API & Temps Reel | 23 | 0 | 23 |
| 5. Frontend Flutter | 27 | 0 | 27 |
| 6. Tests & Production | 22 | 0 | 22 |
| **Total** | **136** | **0** | **136** |
