# XAUUSD Trading App — Suivi d'Avancement

> Mis à jour automatiquement au fil du développement

---

## Phase 0 : Infrastructure

| Tâche | Statut |
|-------|--------|
| Docker Compose (PostgreSQL 15 + Redis 7) | FAIT |
| Fichier .env de configuration | FAIT |
| Alembic migrations (schema initial) | FAIT |

---

## Phase 1 : Authentification Multi-Utilisateurs

| Tâche | Statut |
|-------|--------|
| Endpoint POST /auth/google (vérification Firebase + création user + JWT) | FAIT |
| Endpoint POST /auth/refresh (rafraîchissement token) | FAIT |
| Endpoint POST /auth/logout (révocation refresh token) | FAIT |
| Middleware JWT (vérification + expiration + rôles) | FAIT |
| Gestion des rôles admin/trader/viewer (décorateurs) | FAIT |
| Rate limiting Redis (10 req/min) | FAIT |
| Whitelist IP admin (optionnel) | A FAIRE |
| Tests Phase 1 (15 tests unitaires) | FAIT |

---

## Phase 2 : Connexion MT5 + Démarrage Auto

| Tâche | Statut |
|-------|--------|
| Table mt5_accounts (chiffrement Fernet) | FAIT |
| Service encryption (encrypt/decrypt password) | FAIT |
| Endpoints MT5 CRUD (POST/GET/connect/disconnect/status) | FAIT |
| MetaApiConnector (instanciation par compte) | FAIT |
| EngineManager (isolation par utilisateur) | FAIT |
| Reconnexion automatique (5 tentatives, backoff exponentiel) | FAIT |
| WebSocket broadcast par utilisateur (user_map) | FAIT |
| Endpoint POST /trading/start (vérifie MT5 connecté) | FAIT |
| Endpoint POST /trading/stop (par utilisateur) | FAIT |
| Endpoint POST /trading/emergency-stop (+ audit log) | FAIT |
| GET /trading/history (requête DB paginée) | FAIT |
| Isolation multi-utilisateurs complète | FAIT |
| Migration Alembic 002_mt5_accounts | FAIT |
| Tests Phase 2 (11 tests) | FAIT |

---

## Phase 3 : API Backend Complète

| Tâche | Statut |
|-------|--------|
| GET /health | FAIT |
| POST /auth/google | FAIT |
| POST /auth/refresh | FAIT |
| POST /auth/verify | FAIT |
| POST /auth/logout | FAIT |
| GET /trading/status | FAIT |
| POST /trading/start (vérifie MT5 + per-user) | FAIT |
| POST /trading/stop (per-user) | FAIT |
| POST /trading/emergency-stop (+ audit log) | FAIT |
| GET /trading/config | FAIT |
| PUT /trading/config | FAIT |
| GET /trading/positions | FAIT |
| GET /trading/history (paginé, per-user) | FAIT |
| GET /market/indicators | FAIT |
| GET /market/sr-levels | A FAIRE |
| GET /admin/users (depuis DB) | FAIT |
| PUT /admin/users/{id}/role (depuis DB) | FAIT |
| GET /admin/audit (paginé, depuis DB) | FAIT |
| POST /mt5/accounts | FAIT |
| GET /mt5/accounts | FAIT |
| POST /mt5/accounts/{id}/connect | FAIT |
| POST /mt5/accounts/{id}/disconnect | FAIT |
| GET /mt5/accounts/{id}/status | FAIT |

---

## Phase 4 : Moteur Trading Core

| Tâche | Statut |
|-------|--------|
| MicroTimeframeBuilder (5s-30s) | FAIT |
| Indicateurs RSI/ATR/ADX | FAIT |
| Support & Resistance Engine | FAIT |
| Sniper AI Engine (scoring 0-100, seuil 57) | FAIT |
| 3 plages de signal : WEAK(57-64), MODERATE(65-79), STRONG(80+) | FAIT |
| Lot réduit 70% pour scores 57-64 | FAIT |
| Filtres pré-exécution scores 57-64 (spread 80%, ADX>20, volatilité) | FAIT |
| Dynamic SL adaptatif par score (1.3x conservateur, -15% agressif) | FAIT |
| Trailing Stop paliers dynamiques (1.5x BE, 3x lock 50%, 5x rapide) | FAIT |
| Time-based Break-Even (10 min, profit > 0.5x SL) | FAIT |
| Trailing haute volatilité (+20% expansion) | FAIT |
| Trailing immédiat pour scores >= 80 | FAIT |
| Risk Manager (Kelly + tick value XAUUSD) | FAIT |
| Execution Manager (grille + cooldowns) | FAIT |
| Position Tracker | FAIT |
| Volatility Monitor | FAIT |
| Session Manager (reset quotidien) | FAIT |
| Pattern Detector (Hammer, Engulfing, Doji) | FAIT |
| Configuration persistante nouveaux params | A FAIRE |

---

## Phase 4.15 : Sniper AI Adaptive Learning Engine

| Tâche | Statut |
|-------|--------|
| Market Regime Classifier (4 régimes) | FAIT |
| Table sniper_learning_log + market_regime_history | FAIT |
| Daily Learning Analysis (job APScheduler) | FAIT |
| Ajustement dynamique poids scoring | FAIT |
| Seuil adaptatif (55-62) | FAIT |
| Trade Feedback Loop (buffer circulaire) | FAIT |
| Adaptation stratégie par régime | FAIT |
| Protection overfitting + circuit breaker | FAIT |
| Intégration dans TradingEngine | FAIT |
| Persistance Redis état adaptatif | FAIT |
| Tests Phase 4.15 (27 tests) | FAIT |
| Frontend affichage adaptation | A FAIRE |

---

## Phase 5 : Frontend Dashboard

| Tâche | Statut |
|-------|--------|
| Architecture state management (Provider) | FAIT |
| Client HTTP avec intercepteur JWT (Dio) | FAIT |
| Client WebSocket avec reconnexion (auto-backoff) | FAIT |
| Service Auth (Google login + refresh + logout) | FAIT |
| Service Trading (start/stop/status/config/history) | FAIT |
| Providers (Auth, Trading, Market, Config, TradeHistory) | FAIT |
| Bouton Démarrer Robot (POST /trading/start) | FAIT |
| Bouton Arrêter Robot (POST /trading/stop) | FAIT |
| Bouton Arrêt Urgence (POST /trading/emergency-stop) | FAIT |
| Indicateur état robot (temps réel via WS) | FAIT |
| Prix XAUUSD temps réel (via WS tick.update) | FAIT |
| P&L du jour (réalisé + floating) | FAIT |
| Solde compte + equity | FAIT |
| Liste positions ouvertes (temps réel) | FAIT |
| Indicateur qualité signal Sniper AI | FAIT |
| Régime de marché + seuil adaptatif | FAIT |
| Historique trades (paginé, filtrable) | FAIT |
| Configuration (CRUD via API, save) | FAIT |
| Graphique chandeliers avancé | A FAIRE |

---

## Phase 6 : Panneau de Contrôle

| Tâche | Statut |
|-------|--------|
| Slider risque (PUT /trading/config) | FAIT |
| Toggles (Sniper AI, Micro-TF, Hedging) | FAIT |
| Sélecteur méthode SL | FAIT |
| Inputs SL min/max | FAIT |
| Paramètres grille | FAIT |
| Heures programmables | FAIT |
| Paramètres avancés Sniper/Trailing | FAIT |
| Filtres (RSI, ADX, Spread, Gap, Volatilité) | FAIT |
| Poids Sniper (6 sliders) | FAIT |
| Trailing Stop (niveaux, rapid, time-based BE) | FAIT |
| Micro TF toggles individuels | FAIT |

---

## Phase 7 : Temps Réel WebSocket

| Tâche | Statut |
|-------|--------|
| Service WebSocket backend (broadcast) | FAIT |
| Service WebSocket frontend (connexion + reconnexion + état) | FAIT |
| Événements tick.update | FAIT |
| Événements position.update / trade.closed | FAIT |
| Événements robot.status / emergency.triggered | FAIT |
| Notifications push locales (flutter_local_notifications) | FAIT |
| Alertes modales (emergency, connection error, engine error) | FAIT |
| Toast overlay (trade closed avec animation slide-in) | FAIT |
| Panneau notifications (historique, badge unread, clear) | FAIT |
| Indicateur connexion WS (dot vert/gris dans header) | FAIT |
| NotificationProvider (bridge WS → toasts + push + alertes) | FAIT |

---

## Phase 8 : Tests

| Tâche | Statut |
|-------|--------|
| Tests unitaires backend | A FAIRE |
| Tests d'intégration API | A FAIRE |
| Tests E2E Flutter | A FAIRE |
| Tests de charge | A FAIRE |
| Couverture >= 80% | A FAIRE |

---

## Phase 9 : Déploiement

| Tâche | Statut |
|-------|--------|
| VPS Oracle Cloud | A FAIRE |
| docker-compose.prod.yml | A FAIRE |
| Build backend (Dockerfile) | A FAIRE |
| Build Flutter (web + mobile) | A FAIRE |
| DNS + SSL (Cloudflare + Let's Encrypt) | A FAIRE |
| Validation post-déploiement | A FAIRE |

---

## Phase 10 : Monitoring

| Tâche | Statut |
|-------|--------|
| Prometheus + Grafana | A FAIRE |
| UptimeRobot | A FAIRE |
| Rotation logs | A FAIRE |
| Documentation | A FAIRE |
