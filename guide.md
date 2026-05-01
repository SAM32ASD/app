Voici un **plan de développement complet et structuré**, conçu comme un cahier des charges exécutable. Il intègre la migration de votre EA MQL5 (v9.7 XAUUSD) vers une architecture moderne **Cloud-Native à coût zéro**, avec une stack adaptée à vos contraintes et à votre profil technique (Linux SysAdmin).

---

## 📋 SOMMAIRE
1. [Vision & Périmètre du Projet](#1-vision--périmètre-du-projet)
2. [Architecture Technique Cible](#2-architecture-technique-cible)
3. [Stack Technique Zéro Coût ($0)](#3-stack-technique-zéro-coût-0)
4. [Matrice de Transposition : MQL5 → Backend Python](#4-matrice-de-transposition--mql5--backend-python)
5. [Modélisation des Données](#5-modélisation-des-données)
6. [Plan de Développement par Phases (14 semaines)](#6-plan-de-développement-par-phases-14-semaines)
7. [API & Interfaces Principales](#7-api--interfaces-principales)
8. [Sécurité, Auth & Gestion des Rôles](#8-sécurité-auth--gestion-des-rôles)
9. [DevOps, Déploiement & Monitoring ($0)](#9-devops-déploiement--monitoring-0)
10. [Roadmap & Livrables](#10-roadmap--livrables)

---

## 1. Vision & Périmètre du Projet

### Objectif
Créer une **application centralisée de commande et de supervision** qui héberge la logique de trading actuellement embarquée dans l'EA MQL5. L'application permet à un administrateur (et des utilisateurs autorisés) de :
- Contrôler le robot (**Start/Stop**, scheduling, risque).
- Visualiser l'état du marché et du portefeuille en temps réel.
- Gérer des accès multi-utilisateurs avec droits granulaires.
- Exécuter sur un compte MetaTrader sans jamais intervenir manuellement sur le terminal.

### Périmètre Fonctionnel
| Domaine | Description |
|---------|-------------|
| **Trading Engine** | Reproduction fidèle de la logique v9.7 (Sniper AI, micro-timeframes, SL dynamique, trailing, grille multi-ordres). |
| **Market Data** | Récupération temps réel XAUUSD (ticks + OHLC M1/M5/H1). |
| **Exécution** | Passage d'ordres Buy/Sell/Stop avec gestion des SL/TP via API MetaTrader. |
| **Administration** | Dashboard admin (utilisateurs connectés, rôles, paramètres globaux). |
| **Contrôle** | Panneau de contrôle (risque, heures, limites quotidiennes, bouton d'arrêt d'urgence). |

---

## 2. Architecture Technique Cible

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTS (Flutter)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Mobile     │  │    Web       │  │   PWA Admin Dashboard    │  │
│  │  (iOS/Android)│  │  (Flutter)   │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
└─────────┼─────────────────┼───────────────────────┼────────────────┘
          │                 │                       │
          └─────────────────┴───────────────────────┘
                            │ HTTPS / WebSocket
┌───────────────────────────▼─────────────────────────────────────────┐
│                      BACKEND (VPS Oracle Cloud)                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  API Gateway & Métier (FastAPI - Python / Async)            │   │
│  │  - Auth JWT (Firebase)                                      │   │
│  │  - Endpoints REST (config, users, trades)                   │   │
│  │  - WebSocket Manager (push temps réel vers Flutter)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              TRADING ENGINE (Python Asyncio)                │   │
│  │  - Tick Processor (buffer circulaire Sniper AI)             │   │
│  │  - Micro-Timeframe Builder (5s→30s)                         │   │
│  │  - Signal Generator (Patterns + S/R + RSI/ADX)              │   │
│  │  - Risk Manager (SL dynamique, lots, trailing, BE)          │   │
│  │  - Execution Manager (grille multi-ordres, cooldowns)       │   │
│  │  - Volatility Monitor (ATR, True Range, mode HV)            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  MetaApi SDK / MT5 Connector  →  Compte Exness XAUUSD       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                    DATA & MESSAGING (VPS Local)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │    File System (Logs)    │  │
│  │  (Trades,    │  │  (Cache RT,  │  │                          │  │
│  │   Users,     │  │   Pub/Sub,   │  │                          │  │
│  │   Config)    │  │   Sessions)  │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                    FIREBASE (Google - Plan Spark Gratuit)           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │   Authentication │  │   Cloud Firestore│  │  Cloud Messaging│   │
│  │   (Email/Pwd,    │  │   (Users, Roles, │  │  (Push Notif)   │   │
│  │    Google)       │  │    App Config)   │  │                 │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Technique Zéro Coût ($0)

| Couche | Technologie | Justification | Coût |
|--------|-------------|---------------|------|
| **Frontend** | Flutter 3.x (Dart) | Single codebase Web + Mobile natif. | $0 |
| **Backend API** | Python 3.11+ + FastAPI | Haute perf async, idéal pour WebSocket + trading temps réel. | $0 |
| **Trading Engine** | Python `asyncio` + `pandas`/`numpy` | Portage naturel de la logique MQL5 (calculs vectoriels). | $0 |
| **Base de données** | PostgreSQL 15 (Docker) | Données relationnelles robustes (trades, users, audit). | $0 (self-hosted) |
| **Cache temps réel** | Redis 7 (Docker) | Cache des positions, pub/sub état du robot, rate limiting. | $0 (self-hosted) |
| **Auth & Users** | Firebase Auth (Spark) | Gestion sécurisée des JWT, rôles, sans serveur d'auth maison. | $0 |
| **Config Cloud** | Cloud Firestore (Spark) | Stockage des paramètres utilisateurs et flags globaux. | $0 |
| **Exécution MT** | **MetaApi.cloud** (plan Free) | API REST/WebSocket sur MT5 sans ouvrir de terminal lourd. Alternative: `MetaTrader5` Python + MT5 headless sur le VPS. | $0 (limité) |
| **Hébergement** | Oracle Cloud **Always Free** | 4 OCPU ARM + 24 GB RAM + 200 GB disk. Suffisant pour tout faire tourner 24/7. | $0 |
| **CI/CD** | GitHub Actions | Build Flutter + déploiement SSH sur VPS. | $0 |
| **Monitoring** | UptimeRobot (Free) + Grafana | Surveillance uptime + dashboard métriques (Prometheus/Grafana en Docker). | $0 |
| **DNS/SSL** | Cloudflare (Free) | SSL + proxy + protection DDoS pour le domaine. | $0 |

---

## 4. Matrice de Transposition : MQL5 → Backend Python

C'est le cœur du projet. Chaque module MQL5 de votre EA est traduit en un service Python indépendant.

| Module MQL5 (v9.7) | Implémentation Python | Librairies / Méthodes |
|---------------------|----------------------|----------------------|
| `OnTick()` + Buffer ticks | `TickProcessor` (async) | `asyncio.Queue`, `deque` (buffer circulaire 200 ticks) |
| `SniperCollectTick()` + `SniperEvaluate()` | `SniperAIEngine` | Calcul vectoriel `numpy`, poids configurable |
| `UpdateSyntheticBar()` (5s→30s) | `MicroTimeframeBuilder` | Agrégation par fenêtre temporelle (`pandas.resample`) |
| `DetectPatternOnBars()` | `PatternDetector` | Détection Hammer, Engulfing, Doji sur barres synthétiques |
| `DetectMicroSR()` / `DetectKeyLevels()` | `SupportResistanceEngine` | Détection de pics/creux locaux (`scipy.signal.find_peaks`) |
| `CalculateDynamicSL()` (ATR/Swings/SR/Hybride) | `DynamicSLCalculator` | `ta-lib` ou `pandas-ta` pour ATR, lookback swings |
| `CalculateLots()` | `RiskManager` | Formule de Kelly adaptée, tick value XAUUSD |
| `SendMultiBuyOrders()` / `SendMultiSellOrders()` | `ExecutionManager` | Grille d'ordres avec gestion des index et cooldowns |
| `ScanPositionsForSLManagement()` | `PositionTracker` + `TrailingStopManager` | Boucle async 1s, modification SL par paliers |
| `UpdateVolatilityScan()` | `VolatilityMonitor` | ATR, True Range, Normalized ATR, ratio volatilité |
| `CheckDailyReset()` + `OnTradeTransaction()` | `SessionManager` | Cron interne (`APScheduler`), reset 00:00 UTC |
| `CreateAdvancedDashboard()` | `WebSocketManager` | Push JSON temps réel vers clients Flutter |
| `OnChartEvent()` (bouton Urgence) | `EmergencyStopEndpoint` | POST `/api/v1/trading/emergency-stop` |

### Détail Critique : Le "Sniper AI"
Votre MQL5 utilise un buffer circulaire de 200 ticks. En Python :
```python
from collections import deque
import numpy as np

class SniperAIEngine:
    def __init__(self, window=40):
        self.tick_buffer = deque(maxlen=200)  # SNIPER_BUF_SIZE
        self.window = window
    
    def add_tick(self, tick: dict):
        # Dédoublonnage time + prix
        if self.tick_buffer and self.tick_buffer[-1]['time'] == tick['time']:
            return
        self.tick_buffer.append(tick)
    
    def evaluate(self) -> dict:
        # Calcul momentum, acceleration, RSI, volume tick
        # Retourne score 0-100 + direction
        ...
```

---

## 5. Modélisation des Données

### PostgreSQL (Données critiques & historiques)

```sql
-- Utilisateurs (sync avec Firebase UID)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) CHECK (role IN ('admin', 'trader', 'viewer')),
    display_name VARCHAR(100),
    is_online BOOLEAN DEFAULT false,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Configuration de trading par utilisateur (ou globale si admin)
CREATE TABLE trading_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    risk_percent DECIMAL(5,2) DEFAULT 0.5,
    max_daily_loss_percent DECIMAL(5,2) DEFAULT 3.0,
    max_consecutive_losses INT DEFAULT 8,
    max_trades_per_day INT DEFAULT 500,
    sl_method VARCHAR(50) DEFAULT 'hybrid',
    use_sniper_ai BOOLEAN DEFAULT true,
    sniper_min_score INT DEFAULT 70,
    use_micro_timeframes BOOLEAN DEFAULT true,
    max_positions_per_direction INT DEFAULT 1,
    max_total_positions INT DEFAULT 2,
    allow_hedging BOOLEAN DEFAULT false,
    trading_enabled BOOLEAN DEFAULT true,
    scheduled_start_time TIME,
    scheduled_stop_time TIME,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Journal des trades (deal ticket)
CREATE TABLE trade_logs (
    id UUID PRIMARY KEY,
    ticket BIGINT NOT NULL,
    deal_id BIGINT,
    symbol VARCHAR(20) DEFAULT 'XAUUSD',
    order_type VARCHAR(20), -- BUY_STOP, SELL_MARKET, etc.
    entry_price DECIMAL(12,5),
    sl_price DECIMAL(12,5),
    tp_price DECIMAL(12,5),
    lots DECIMAL(10,2),
    profit DECIMAL(12,2),
    commission DECIMAL(12,2),
    swap DECIMAL(12,2),
    entry_source VARCHAR(50), -- M1, MICRO_5s, SNIPER_AI
    grid_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);

-- Positions actives (état temps réel)
CREATE TABLE active_positions (
    ticket BIGINT PRIMARY KEY,
    symbol VARCHAR(20),
    position_type VARCHAR(10), -- BUY / SELL
    volume DECIMAL(10,2),
    open_price DECIMAL(12,5),
    current_sl DECIMAL(12,5),
    current_tp DECIMAL(12,5),
    open_time TIMESTAMP,
    current_profit DECIMAL(12,2),
    rapid_mode BOOLEAN DEFAULT false,
    breakeven_reached BOOLEAN DEFAULT false,
    current_step INT DEFAULT 0,
    entry_source VARCHAR(50)
);

-- Audit & Sécurité (qui a fait quoi)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100), -- START_TRADING, STOP_TRADING, UPDATE_RISK
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Redis (Cache temps réel)
- `robot:status` → `RUNNING|STOPPED|EMERGENCY`
- `market:xauusd:last_tick` → JSON du dernier tick
- `market:volatility:current` → `% volatilité`
- `session:today:trades_count` → compteur quotidien
- `session:today:consecutive_losses` → compteur pertes
- `session:today:realized_pl` → P&L réalisé
- `user:{uid}:websocket_channel` → canal de push

### Firestore (Config & Flags)
- `users/{uid}` → profil, préférences
- `global_settings` → paramètres override admin
- `app_version` → contrôle de version forcée

---

## 6. Plan de Développement par Phases (14 semaines)

### Phase 1 : Fondation & Infrastructure (Semaines 1-2)
**Objectif : Avoir un environnement de production opérationnel à $0.**

| Tâche | Livrable |
|-------|----------|
| Création compte Oracle Cloud + provisionnement VM ARM (Ubuntu 22.04) | VPS accessible en SSH |
| Installation Docker + Docker Compose | `docker-compose.yml` fonctionnel |
| Déploiement PostgreSQL + Redis + Adminer/PgAdmin | Bases accessibles |
| Création projet Firebase (Spark) | Auth + Firestore prêts |
| Setup repo GitHub (Mono-repo : `frontend/`, `backend/`, `infra/`) | CI/CD basique (lint + test) |
| Configuration DNS + Cloudflare (optionnel) | SSL pointé sur le VPS |

### Phase 2 : Connecteur Marché & Données (Semaines 3-4)
**Objectif : Recevoir et traiter le flux XAUUSD temps réel.**

| Tâche | Livrable |
|-------|----------|
| Intégration SDK MetaApi (ou `MetaTrader5` Python) | Connexion au compte Exness |
| Service `MarketDataFeed` : récupération ticks XAUUSD | Ticks stockés en Redis Stream |
| Construction `MicroTimeframeBuilder` (agrégation 5s/10s/15s/20s/30s) | Barres OHLC micro disponibles |
| Calcul indicateurs techniques (RSI, ATR, ADX) sur M1/M5 | Valeurs accessibles via API |
| Détection niveaux S/R sur H4 et micro-timeframes | API `/market/sr-levels` |

### Phase 3 : Moteur de Trading Core (Semaines 5-8)
**Objectif : Porter 100% de la logique MQL5 v9.7 en Python.**

| Tâche | Livrable |
|-------|----------|
| **Sniper AI** : Buffer circulaire + scoring temps réel | Score 0-100 à chaque tick |
| **Signal Engine** : Patterns bougies + confluence RSI/ADX | Signal BUY/SELL/NEUTRE |
| **Dynamic SL Calculator** : ATR adaptatif + Swings + S/R | Distance SL en points |
| **Risk Manager** : Calcul lots selon solde courant, ajustement volatilité | Lots précis par trade |
| **Execution Manager** : Envoi multi-ordres (grille), gestion cooldowns | Ordres exécutés sur MT5 |
| **Position Tracker** : Suivi des tickets, SL, TP, grid index | Table `active_positions` synchronisée |
| **Trailing & BE Manager** : Scan continu 1s, paliers rapides, time-based BE | SL modifiés automatiquement |
| **Session Manager** : Reset quotidien, limites (pertes, trades max), heures | Robot respecte les contraintes |

### Phase 4 : API Backend & Temps Réel (Semaines 9-10)
**Objectif : Exposer la logique via API sécurisée et WebSocket.**

| Tâche | Livrable |
|-------|----------|
| Développement API FastAPI (REST) | Swagger UI opérationnel |
| Middleware Auth JWT (vérification Firebase) | Routes protégées |
| Endpoints Trading Control (`/trading/start`, `/stop`, `/emergency`) | Robot contrôlable à distance |
| Endpoints Admin (`/admin/users`, `/admin/roles`, `/audit-logs`) | Gestion des accès |
| WebSocket Server (`/ws/trading`) | Push temps réel (P&L, positions, volatilité) |
| Synchronisation Firestore ↔ PostgreSQL (config users) | Config persistante |

### Phase 5 : Frontend Flutter (Semaines 10-12)
**Objectif : Interface utilisateur complète.**

| Écran / Module | Fonctionnalités |
|----------------|-----------------|
| **Auth** | Login/Register (Firebase), mot de passe oublié |
| **Trading Dashboard** | État du robot (ON/OFF), P&L jour, solde courant, volatilité en temps réel, positions ouvertes (liste détaillée avec SL/TP), graphique des trades |
| **Control Panel** | Slider risque (%), input heure démarrage auto, toggle Sniper AI, toggle Micro-TF, paramètres SL (min/max), bouton **ARRÊT D'URGENCE** rouge |
| **Admin Panel** | Tableau des utilisateurs (online/offline), attribution des rôles, vue des trades en cours par utilisateur, paramètres globaux override |
| **Notifications** | Push Firebase (alerte perte journalière atteinte, robot démarré/arrêté) |

### Phase 6 : Intégration, Tests & Production (Semaines 13-14)
**Objectif : Mise en production stable sur compte démo, puis réel.**

| Tâche | Livrable |
|-------|----------|
| Tests unitaires moteur (backtesting sur 1 mois de ticks historiques) | Rapport de performance |
| Tests d'intégration API ↔ MetaApi | Exécution d'ordres test |
| Tests end-to-end Flutter | Parcours utilisateur validé |
| Déploiement production sur VPS (Docker Compose prod) | Application live |
| Monitoring (Grafana + Prometheus ou UptimeRobot) | Alertes uptime |
| Documentation technique (API + Déploiement) | `README.md` + Wiki |

---

## 7. API & Interfaces Principales

### REST API (FastAPI)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/auth/verify` | Public | Vérifie le token Firebase et crée la session |
| `GET` | `/trading/status` | User | État du robot, P&L, volatilité, positions |
| `POST` | `/trading/start` | Admin/Trader | Démarre le moteur de trading |
| `POST` | `/trading/stop` | Admin/Trader | Arrête le moteur (fermeture douce) |
| `POST` | `/trading/emergency-stop` | Admin | **Ferme toutes les positions immédiatement** |
| `GET` | `/trading/config` | User | Récupère la configuration active |
| `PUT` | `/trading/config` | Admin | Met à jour les paramètres (risque, SL, etc.) |
| `GET` | `/trading/positions` | User | Liste des positions ouvertes |
| `GET` | `/trading/history` | User | Historique des trades (paginé) |
| `GET` | `/admin/users` | Admin | Liste des utilisateurs et statut |
| `PUT` | `/admin/users/{id}/role` | Admin | Change le rôle d'un utilisateur |
| `GET` | `/admin/audit` | Admin | Logs d'audit |

### WebSocket Events (Temps Réel)

| Event | Direction | Payload |
|-------|-----------|---------|
| `tick.update` | Server → Client | Dernier prix XAUUSD + spread |
| `position.update` | Server → Client | Liste positions + P&L flottant |
| `trade.closed` | Server → Client | Ticket fermé + profit/perte |
| `volatility.alert` | Server → Client | Niveau volatilité + mode Haute Vol |
| `robot.status` | Server → Client | `RUNNING`, `STOPPED`, `ERROR` |
| `emergency.triggered` | Server → Client | Notification arrêt d'urgence |

---

## 8. Sécurité, Auth & Gestion des Rôles

### Authentification
- **Firebase Authentication** (Email/Mot de passe, Google Sign-In).
- Vérification du JWT Firebase à chaque requête API via le middleware FastAPI.
- Stockage du `firebase_uid` en base pour liaison compte.

### Rôles & Permissions

| Rôle | Permissions |
|------|-------------|
| **Admin** | Tout contrôler : start/stop global, modifier config de n'importe quel utilisateur, voir tous les trades, gérer les rôles, déclencher l'arrêt d'urgence. |
| **Trader** | Contrôler son propre robot, voir ses trades, modifier sa config (dans les limites admin). |
| **Viewer** | Lecture seule : voir le dashboard, les positions, l'historique. Pas d'action sur le robot. |

### Sécurité Trading
- **Arrêt d'urgence** : Endpoint protégé + bouton physique dans l'app. Ferme toutes les positions via `trade.PositionClose()` et passe le robot en mode `EMERGENCY`.
- **Rate Limiting** : Limite API (ex: 10 requêtes/minute) via Redis pour éviter le spam.
- **IP Whitelisting** (optionnel) : Restreindre l'accès admin à certaines IP.
- **Audit Trail** : Toute action critique (start, stop, changement risque) est loguée avec IP et timestamp.

---

## 9. DevOps, Déploiement & Monitoring ($0)

### Infrastructure sur VPS Oracle (Always Free)

```yaml
# docker-compose.prod.yml (simplifié)
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    volumes:
      - pg_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"  # Pas exposé publiquement

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "127.0.0.1:6379:6379"

  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
    environment:
      - DATABASE_URL=postgresql://trader:${DB_PASSWORD}@postgres/trading_db
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
      - METAAPI_TOKEN=${METAAPI_TOKEN}
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    restart: unless-stopped

  # Optionnel: MT5 headless si vous ne utilisez pas MetaApi
  # mt5:
  #   image: your-mt5-wine-image
  #   ...

volumes:
  pg_data:
```

### CI/CD (GitHub Actions)
1. **Push sur `main`** → Tests unitaires Python + Build Flutter Web.
2. **Tag `v*`** → Déploiement automatique sur VPS Oracle via SSH (rsync + `docker-compose up -d`).

### Monitoring
- **UptimeRobot** (Free) : Ping toutes les 5 min sur `https://votre-api.com/health`.
- **Grafana + Prometheus** (Docker sur le VPS) : Métriques du robot (nombre de trades, latence API, P&L).
- **Logs** : Centralisation via `docker logs` + rotation (`logrotate`).

---

## 10. Roadmap & Livrables

| Semaine | Jalon | Livrable Clé |
|---------|-------|--------------|
| **S2** | 🏗️ Infra Ready | VPS, BDD, Firebase, CI/CD opérationnels |
| **S4** | 📡 Market Connected | Flux XAUUSD temps réel, micro-timeframes fonctionnels |
| **S8** | 🧠 Engine Complete | 100% logique MQL5 portée, tests unitaires OK |
| **S10** | 🔌 API Live | Endpoints REST + WebSocket sécurisés |
| **S12** | 📱 App Beta | Flutter Web/Mobile fonctionnel (démo) |
| **S14** | 🚀 Production | Déploiement production, compte démo validé, documentation |

---

## 🎯 Prochaines Étapes Immédiates (À faire cette semaine)

1. **Créer le compte Oracle Cloud** et provisionner l'instance ARM (4 OCPU / 24 GB).
2. **Initialiser le projet Firebase** (Spark) et noter les clés d'API.
3. **Créer le repo GitHub** avec la structure :
   ```
   xauusd-trading-app/
   ├── backend/          # FastAPI + Trading Engine
   ├── frontend/         # Flutter
   ├── infra/            # Docker Compose, scripts VPS
   └── docs/             # Cahier des charges, API specs
   ```
4. **Choisir le connecteur MT** : Créer un compte MetaApi (Free) pour tester la connexion à Exness, OU préparer l'installation de MT5 sur le VPS.
5. **Me fournir** (si vous le souhaitez) un dump des paramètres exacts que vous utilisez actuellement sur l'EA (les inputs modifiés par rapport aux defaults) pour que je génère le fichier de configuration JSON initial du backend.

---

Ce plan est conçu pour être **exécutable immédiatement**, avec une stack que vous maîtrisez déjà en tant qu'administrateur Linux. Voulez-vous que je détaille une phase spécifique (par exemple, le code Python du `SniperAIEngine` ou la structure exacte du `docker-compose.yml` pour Oracle Cloud) ?