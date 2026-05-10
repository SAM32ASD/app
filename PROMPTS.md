# XAUUSD Trading App — Prompts de Développement Complets

> Document de référence unifié pour le développement de l'application XAUUSD Trading  
> Dernière mise à jour : 2026-05-08  
> Statut : Prêt pour implémentation

---

## Légende

| Symbole | Signification |
|---------|---------------|
| `[ ]` | À implémenter |
| `[~]` | En cours de révision |
| `[x]` | Validé |
| `🔴` | Critique — bloquant pour le build |
| `🟡` | Important — impacte l'expérience utilisateur |
| `🟢` | Standard — qualité attendue |

---

## Phase 0 : Prérequis et Architecture de Base

### 0.1 Règles d'or du projet
- [ ] **Règle 1** : Aucun build ni déploiement ne peut être réalisé tant que l'intégralité des tests ne passe pas au vert.
- [ ] **Règle 2** : Tout bouton visible sur le frontend doit déclencher une action réelle sur le backend. Aucun mock, aucun stub, aucun comportement simulé n'est toléré.
- [ ] **Règle 3** : L'application doit supporter plusieurs utilisateurs simultanés avec une isolation stricte des données, des positions et des moteurs de trading.
- [ ] **Règle 4** : Toute action sensible (démarrage, arrêt, arrêt d'urgence, modification de config) doit être persistante côté backend et reflétée en temps réel sur tous les clients connectés de l'utilisateur.
- [ ] **Règle 5** : Le seuil minimum du Sniper AI est fixé à **57** (et non 60). Les signaux entre 57 et 64 sont traités comme faibles mais acceptables, avec des mesures de protection renforcées.

### 0.2 Stack technique de référence
| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI + Python 3.11 |
| Base de données | PostgreSQL 15 |
| Cache / Pub-Sub | Redis 7 |
| Authentification | Firebase Auth (Google Sign-In) + JWT interne |
| Connexion marché | MetaApi Cloud SDK |
| Frontend | Flutter 3.19+ (Web, Android, iOS) |
| Temps réel | WebSocket natif |
| Notifications | Firebase Cloud Messaging |
| Reverse proxy | Nginx |
| Monitoring | Prometheus + Grafana |
| Hébergement | Oracle Cloud VPS (ARM, Ubuntu 22.04) |
| DNS / SSL | Cloudflare + Let's Encrypt |

---

## Phase 1 : Authentification Multi-Utilisateurs (Google OAuth + JWT)

### 1.1 Backend — Endpoint d'authentification Google
**Objectif** : Permettre à plusieurs utilisateurs de s'authentifier via Google Sign-In et recevoir un token interne sécurisé.

- [ ] Créer un endpoint dédié à la réception du token Google (`id_token`) envoyé par le frontend.
- [ ] Vérifier la validité du token Google côté serveur en interrogeant les serveurs Google ou via le SDK Firebase Admin.
- [ ] Si le token est invalide, expiré ou mal formé, rejeter la requête avec une erreur 401.
- [ ] Extraire du token Google : email, nom affiché, photo de profil, identifiant unique Firebase.
- [ ] Vérifier en base PostgreSQL si un utilisateur existe avec cet email ou cet identifiant Firebase.
- [ ] Si l'utilisateur n'existe pas, le créer automatiquement avec le rôle par défaut `viewer`, et enregistrer la date de création et la dernière connexion.
- [ ] Si l'utilisateur existe, mettre à jour son nom affiché, sa photo de profil et sa date de dernière connexion.
- [ ] Générer un token JWT interne signé avec une clé secrète, contenant : identifiant interne, email, rôle, et une date d'expiration fixée à 24 heures.
- [ ] Générer un token de rafraîchissement valable 7 jours, stocké en base ou dans Redis.
- [ ] Retourner au frontend : token d'accès, token de rafraîchissement, et un objet utilisateur (id, email, rôle, nom affiché).
- [ ] Créer un middleware d'authentification qui intercepte chaque requête sur les routes protégées.
- [ ] Le middleware extrait le JWT du header Authorization, le vérifie, et injecte l'identifiant utilisateur et le rôle dans le contexte de la requête.
- [ ] Si le token est absent, invalide ou expiré : rejeter avec 401.
- [ ] Si le token est valide mais le rôle insuffisant : rejeter avec 403.
- [ ] Implémenter un endpoint de rafraîchissement de token qui reçoit le refresh token, le vérifie, et retourne un nouveau token d'accès.

### 1.2 Backend — Gestion des rôles et permissions
- [ ] Définir trois rôles : `admin`, `trader`, `viewer`.
- [ ] Créer des décorateurs de permission par rôle pour protéger les endpoints.
- [ ] `admin` : accès total, arrêt d'urgence, gestion des utilisateurs, override de configuration globale.
- [ ] `trader` : connexion MT5, démarrage/arrêt du robot, modification de sa propre configuration.
- [ ] `viewer` : lecture seule, tableau de bord visible mais sans aucun bouton d'action.
- [ ] Implémenter un rate limiting via Redis (exemple : 10 requêtes par minute par utilisateur).
- [ ] Implémenter un whitelisting IP optionnel pour les routes admin.

### 1.3 Frontend — Écran d'authentification
- [ ] Intégrer le SDK Google Sign-In dans l'application Flutter.
- [ ] Afficher un bouton "Se connecter avec Google" sur l'écran d'authentification.
- [ ] Au clic, déclencher le flux natif Google, récupérer le `id_token`, et l'envoyer au backend via POST.
- [ ] En cas de succès, stocker de manière sécurisée le JWT interne et le refresh token (stockage sécurisé natif).
- [ ] Rediriger vers le tableau de bord si le rôle est `admin` ou `trader`.
- [ ] Rediriger vers une vue en lecture seule si le rôle est `viewer`.
- [ ] Implémenter un intercepteur HTTP qui ajoute automatiquement le JWT à chaque requête sortante.
- [ ] Gérer l'expiration du token en pleine session : intercepter la 401, appeler silencieusement l'endpoint de rafraîchissement, puis réexécuter la requête initiale.
- [ ] Afficher un indicateur de chargement pendant la connexion et désactiver le bouton pour éviter les doubles soumissions.

### 1.4 🔴 Tests obligatoires avant build
- [ ] Token Google valide → création utilisateur + retour JWT interne.
- [ ] Token Google invalide → rejet 401.
- [ ] JWT interne valide → accès route protégée autorisé.
- [ ] JWT interne expiré → rejet 401.
- [ ] Admin accède à `/admin/users` → 200.
- [ ] Viewer accède à `/admin/users` → 403.
- [ ] Rate limit dépassé → 429.

---

## Phase 2 : Connexion MetaTrader 5 et Démarrage Automatique du Trading

### 2.1 Base de données — Table des comptes MT5
- [ ] Créer une table `mt5_accounts` avec les champs : id unique, user_id (clé étrangère), broker, numéro de compte, mot de passe chiffré, serveur, statut actif, statut de connexion, date de dernière connexion, date de création.
- [ ] Assurer l'unicité de la combinaison utilisateur + numéro de compte.
- [ ] Chiffrer le mot de passe avec un algorithme symétrique robuste (Fernet/AES) avant stockage, la clé étant dans les variables d'environnement.

### 2.2 Backend — Service MetaApiConnector
- [ ] Créer un service `MT5AccountService` avec les méthodes : ajouter un compte, récupérer le compte actif d'un utilisateur, connecter le compte, déconnecter le compte, obtenir le statut de connexion.
- [ ] Utiliser le SDK MetaApi Cloud pour établir une session authentifiée avec le serveur de trading.
- [ ] Stocker l'état de connexion en mémoire (dictionnaire indexé par id de compte) et synchroniser dans Redis sous une clé dédiée.
- [ ] Implémenter une reconnexion automatique en cas de perte de connexion : maximum 5 tentatives, délai exponentiel entre chaque tentative.
- [ ] En cas d'échec définitif, mettre à jour le statut en `ERROR` et notifier l'utilisateur via WebSocket.
- [ ] Implémenter la déconnexion propre qui ferme la session MetaApi et nettoie l'état en mémoire et dans Redis.

### 2.3 Backend — Démarrage et arrêt du trading
- [ ] Créer l'endpoint `POST /trading/start`, protégé par auth, réservé aux rôles `admin` et `trader`.
- [ ] Vérifier que l'utilisateur possède un compte MT5 actif et actuellement connecté. Sinon : erreur 400.
- [ ] Vérifier que la configuration de trading de l'utilisateur autorise le démarrage. Sinon : erreur 400.
- [ ] Vérifier que le robot n'est pas déjà en cours d'exécution pour cet utilisateur. Sinon : erreur 400.
- [ ] Démarrer une instance du moteur SniperAI dédiée à cet utilisateur spécifique, en lui passant l'id du compte MT5 connecté.
- [ ] Mettre à jour le statut du robot à `RUNNING` dans Redis sous une clé propre à l'utilisateur.
- [ ] Diffuser un événement `robot.status` avec la valeur `RUNNING` aux clients WebSocket de cet utilisateur.
- [ ] Retourner une réponse de succès.
- [ ] Créer l'endpoint `POST /trading/stop` : arrêter proprement l'instance SniperAI de l'utilisateur, mettre à jour le statut à `STOPPED`, notifier via WebSocket.
- [ ] Créer l'endpoint `POST /trading/emergency-stop` : réservé au rôle `admin`. Arrêter immédiatement le moteur, fermer toutes les positions ouvertes sur le compte MT5, mettre à jour le statut des positions en base, créer une entrée dans les logs d'audit, diffuser l'événement `emergency.triggered` à tous les clients de l'utilisateur.

### 2.4 Frontend — Écran de connexion MT5
- [ ] Créer un écran avec un formulaire contenant : numéro de compte MT5, mot de passe MT5 (masqué), menu déroulant de sélection du serveur (Exness-Real, Exness-Demo, etc.).
- [ ] Afficher un bouton principal "Connecter et démarrer le trading".
- [ ] Au clic, enchaîner séquentiellement :
  1. Envoyer les identifiants au backend pour créer/mettre à jour le compte MT5.
  2. Déclencher la connexion au compte MT5.
  3. Attendre la confirmation de connexion réussie.
  4. Appeler automatiquement l'endpoint de démarrage du trading.
- [ ] Afficher un indicateur de progression circulaire pendant toute la séquence et empêcher toute interaction avec le formulaire.
- [ ] En cas de succès final, afficher un indicateur visuel "Trading actif 🟢" et rediriger vers le tableau de bord.
- [ ] En cas d'échec à n'importe quelle étape, afficher un message d'erreur clair et permettre de réessayer.
- [ ] Afficher en temps réel le statut de connexion du compte MT5 sur le tableau de bord.

### 2.5 Isolation multi-utilisateurs
- [ ] Chaque utilisateur connecté doit posséder sa propre instance logique du moteur SniperAI, indexée par son identifiant utilisateur.
- [ ] Les positions ouvertes doivent être stockées en base avec une colonne `user_id` propriétaire.
- [ ] Le gestionnaire WebSocket doit maintenir une cartographie entre les identifiants de connexion socket et les identifiants utilisateur.
- [ ] Un utilisateur ne doit jamais pouvoir consulter, modifier ou interagir avec les données ou positions d'un autre utilisateur.

### 2.6 🔴 Tests obligatoires avant build
- [ ] Mot de passe MT5 chiffré en base et déchiffrable.
- [ ] Connexion MetaApi simulée → succès + mise à jour statut Redis.
- [ ] Reconnexion automatique après déconnexion simulée.
- [ ] Flux complet : ajout compte → connexion → démarrage auto → statut RUNNING.
- [ ] Deux utilisateurs démarrent simultanément → isolation complète.
- [ ] Utilisateur A ne reçoit pas les événements WebSocket de l'utilisateur B.
- [ ] Arrêt d'urgence → toutes positions fermées + log d'audit créé.

---

## Phase 3 : API Backend — Tous les Endpoints Fonctionnels

### 3.1 Structure de base FastAPI
- [ ] Initialiser le projet avec la structure : routers, services, models, schemas.
- [ ] Configurer Uvicorn avec 2 workers, host 0.0.0.0, port 8000.
- [ ] Créer l'endpoint `GET /health` retournant le statut du service, de la connexion PostgreSQL et de la connexion Redis.
- [ ] Activer la documentation Swagger UI automatique.

### 3.2 Endpoints d'authentification
- [ ] `POST /auth/google` : réception du token Google, création/mise à jour utilisateur, génération JWT.
- [ ] `POST /auth/refresh` : rafraîchissement du token d'accès.
- [ ] `POST /auth/verify` : vérification du token Firebase + création de session.

### 3.3 Endpoints de trading
- [ ] `GET /trading/status` : retourner l'état du robot (RUNNING/STOPPED/ERROR), le P&L du jour, le niveau de volatilité, et le nombre de positions ouvertes.
- [ ] `POST /trading/start` : démarrer le moteur pour l'utilisateur authentifié (admin/trader uniquement).
- [ ] `POST /trading/stop` : arrêter le moteur proprement (admin/trader uniquement).
- [ ] `POST /trading/emergency-stop` : fermer TOUTES les positions immédiatement (admin uniquement).
- [ ] `GET /trading/config` : récupérer la configuration active de l'utilisateur.
- [ ] `PUT /trading/config` : mettre à jour les paramètres de trading. Persister en PostgreSQL, synchroniser dans Redis, notifier le moteur actif de l'utilisateur.
- [ ] `GET /trading/positions` : liste des positions ouvertes de l'utilisateur authentifié.
- [ ] `GET /trading/history` : historique des trades paginé de l'utilisateur authentifié.

### 3.4 Endpoints de données marché
- [ ] `GET /market/indicators` : retourner les valeurs RSI (M1/M5), ATR (M1/M5/H1), ADX (M1/M5).
- [ ] `GET /market/sr-levels` : retourner les niveaux de support et résistance détectés (H4 et micro-timeframes).

### 3.5 Endpoints admin
- [ ] `GET /admin/users` : liste des utilisateurs avec statut online/offline (admin uniquement).
- [ ] `PUT /admin/users/{id}/role` : changer le rôle d'un utilisateur (admin uniquement).
- [ ] `GET /admin/audit` : logs d'audit paginés (admin uniquement).

### 3.6 Endpoints MT5
- [ ] `POST /mt5/accounts` : ajouter un compte MT5 pour l'utilisateur authentifié.
- [ ] `GET /mt5/accounts` : lister les comptes MT5 de l'utilisateur.
- [ ] `POST /mt5/accounts/{id}/connect` : établir la connexion au compte.
- [ ] `POST /mt5/accounts/{id}/disconnect` : fermer la connexion au compte.
- [ ] `GET /mt5/accounts/{id}/status` : obtenir le statut de connexion.

### 3.7 🔴 Tests obligatoires avant build
- [ ] Chaque endpoint retourne le code HTTP attendu et les données au bon format.
- [ ] Les routes admin rejetées avec 403 pour un trader/viewer.
- [ ] Les routes trading rejetées avec 403 pour un viewer.
- [ ] `PUT /trading/config` persiste en base, synchronise Redis, et notifie le moteur.
- [ ] `GET /trading/positions` ne retourne que les positions de l'utilisateur authentifié.

---

## Phase 4 : Moteur de Trading Core (Sniper AI, SL, Trailing Stop, Risk, Exécution)

### 4.1 Micro-Timeframe Builder
- [ ] Implémenter `MicroTimeframeBuilder` : agrégation des ticks en barres OHLC synthétiques.
- [ ] Supporter les périodes : 5s, 10s, 15s, 20s, 30s.
- [ ] Valider les barres générées vs données MQL5 de référence.

### 4.2 Indicateurs techniques
- [ ] Calculer RSI sur M1/M5 (ta-lib ou pandas-ta).
- [ ] Calculer ATR sur M1/M5/H1.
- [ ] Calculer ADX sur M1/M5.
- [ ] Exposer les valeurs via endpoint API `/market/indicators`.

### 4.3 Support & Resistance
- [ ] Implémenter `SupportResistanceEngine` : détection de pics/creux locaux (scipy.signal.find_peaks).
- [ ] Détection S/R sur H4 (`DetectKeyLevels`).
- [ ] Détection S/R sur micro-timeframes (`DetectMicroSR`).
- [ ] Exposer via endpoint API `/market/sr-levels`.

### 4.4 🔴 Sniper AI Engine — Seuil de validation à 57%
**Objectif** : Abaisser le seuil minimum de validation des trades de 60 à 57, avec des mesures de protection différenciées selon la qualité du signal.

- [ ] Modifier la logique de validation du moteur `SniperAIEngine` pour que le score minimum d'autorisation passe de **60 à 57**.
- [ ] Conserver le système de scoring sur 0-100 avec les critères : momentum, accélération, RSI micro, volume tick, confluence des patterns.
- [ ] Adapter la logique de décision selon trois plages de score :
  - **Score 57 à 64** : Signal faible mais acceptable. Le trade est autorisé uniquement si tous les filtres pré-exécution sont validés (spread, marge, gap, volatilité). Le lot doit être réduit à **70%** de la taille calculée par le RiskManager.
  - **Score 65 à 79** : Signal modéré. Le trade est autorisé avec la taille de lot standard calculée par le RiskManager.
  - **Score 80 à 100** : Signal fort. Le trade est autorisé avec la taille de lot standard et le Trailing Stop est activé immédiatement dès l'ouverture.
- [ ] Si le score est inférieur à 57, le moteur retourne `NEUTRE` et bloque l'envoi de l'ordre, quelle que soit la direction détectée.
- [ ] Implémenter le `SniperCollectTick()` avec dédoublonnage time + prix.
- [ ] Implémenter le `SniperEvaluate()` : calcul momentum, accélération, RSI micro, volume tick.
- [ ] S'assurer que l'abaissement du seuil à 57 n'entraîne pas une augmentation excessive des faux signaux. Augmenter légèrement le poids du critère de confluence (RSI + ADX) si nécessaire pour compenser.
- [ ] Logger systématiquement le score calculé, la plage, et la décision finale dans `trade_logs`.

### 4.5 Signal Engine (Pattern Detection)
- [ ] Implémenter `PatternDetector` : détection Hammer sur barres synthétiques.
- [ ] Détection Engulfing (bullish/bearish).
- [ ] Détection Doji.
- [ ] Confluence avec RSI/ADX pour confirmation du signal.
- [ ] Générer signal final BUY/SELL/NEUTRE avec niveau de confiance.

### 4.6 🔴 Dynamic SL Calculator — Adaptatif à la qualité du signal
**Objectif** : La distance du Stop Loss n'est plus fixe mais dépendante du score Sniper AI et des conditions de marché.

- [ ] Modifier le `DynamicSLCalculator` pour que la distance du SL dépende du score Sniper AI :
  - **Score 57-64** : appliquer la méthode de SL la plus conservatrice (par défaut : méthode ATR avec un multiplicateur majoré de **1.3x** par rapport à la config standard). Le SL est placé plus loin pour absorber le bruit du signal faible.
  - **Score 65-79** : appliquer la méthode de SL standard configurée par l'utilisateur (ATR, Swings, S/R ou Hybride) avec les paramètres normaux.
  - **Score 80-100** : appliquer la méthode de SL la plus agressive (distance réduite de **15%** par rapport au calcul standard) car la confiance est élevée.
- [ ] Implémenter les 4 méthodes de SL : ATR adaptatif, Swings (lookback sur derniers swings), S/R (SL placé sous/sur le niveau S/R le plus proche), Hybride (combinaison pondérée des 3 méthodes).
- [ ] Dans tous les cas, le SL calculé doit respecter impérativement les bornes `sl_min` et `sl_max` configurées.
- [ ] Si le SL calculé dépasse `sl_max`, le recaler à `sl_max` et logger un avertissement.
- [ ] Si le SL calculé est inférieur à `sl_min`, le recaler à `sl_min` et logger un avertissement.
- [ ] Stocker dans `trade_logs` : méthode utilisée, distance initiale en pips, score ayant déterminé la méthode.

### 4.7 🔴 Trailing Stop Manager — Paliers dynamiques
**Objectif** : Remplacer le trailing fixe par un système à paliers adaptés au profit et à la volatilité.

- [ ] Modifier le `TrailingStopManager` pour un système à **paliers dynamiques** :
  - **Niveau 1 (Déclenchement)** : Activer le trailing lorsque le profit atteint **1.5x** la distance initiale du SL. À ce stade, déplacer le SL au prix d'ouverture (Break-Even).
  - **Niveau 2 (Sécurisation)** : Lorsque le profit atteint **3x** la distance initiale du SL, déplacer le SL pour verrouiller **50%** du profit en cours.
  - **Niveau 3 (Maximisation)** : Lorsque le profit atteint **5x** la distance initiale du SL, passer en mode trailing rapide (`rapid_mode`) où le SL est collé à **0.3x** l'ATR actuel sous le prix pour un BUY (ou au-dessus pour un SELL).
- [ ] En mode haute volatilité (signalé par `VolatilityMonitor`), élargir automatiquement la distance du trailing de **20%** pour éviter les clôtures parasites.
- [ ] Implémenter un **Time-based Break-Even** : si une position est ouverte depuis plus de **10 minutes** et que le profit est supérieur à **0.5x** le SL initial mais inférieur au seuil de déclenchement normal (1.5x), déplacer quand même le SL au prix d'ouverture pour sécuriser le capital.
- [ ] Le trailing stop doit être scanné et potentiellement modifié **toutes les secondes** via l'API MetaApi.
- [ ] Logger chaque modification de SL dans `trade_logs` : ancienne valeur, nouvelle valeur, raison du déplacement (niveau atteint, mode rapide, time-based BE), horodatage.

### 4.8 Risk Manager
- [ ] Implémenter `RiskManager` : calcul des lots selon solde courant.
- [ ] Formule de Kelly adaptée + tick value XAUUSD.
- [ ] Ajustement lots selon volatilité courante.
- [ ] Vérification marge disponible avant envoi d'ordre.
- [ ] Limites : `risk_percent`, `max_daily_loss_percent`, `max_consecutive_losses`.
- [ ] Pour les scores 57-64, appliquer automatiquement un lot réduit à 70% du calcul standard.

### 4.9 Execution Manager
- [ ] Implémenter `ExecutionManager` : envoi d'ordres Buy/Sell/Stop via MetaApi.
- [ ] Grille multi-ordres (`SendMultiBuyOrders` / `SendMultiSellOrders`).
- [ ] Gestion des index de grille par position.
- [ ] Système de cooldowns entre les ordres.
- [ ] Filtres pré-exécution : spread, marge, gap, RSI, ADX, volatilité.
- [ ] **Filtres supplémentaires pour scores 57-64** :
  - Le spread actuel ne doit pas dépasser 80% de la valeur moyenne du spread sur les 50 derniers ticks.
  - Le ratio ATR normalisé ne doit pas indiquer une volatilité explosive.
  - L'ADX doit être supérieur à 20 pour confirmer une tendance identifiable.
  - Si un filtre échoue, le trade est refusé malgré le score >= 57, et la raison est loguée.
- [ ] Ces filtres supplémentaires ne s'appliquent pas aux scores >= 65.

### 4.10 Position Tracker
- [ ] Implémenter `PositionTracker` : synchronisation des positions actives avec MT5.
- [ ] Mise à jour de la table `active_positions` en temps réel.
- [ ] Détection des positions fermées (par SL/TP ou manuellement).
- [ ] Gestion du `grid_index` par position.

### 4.11 Volatility Monitor
- [ ] Implémenter `VolatilityMonitor` : calcul ATR temps réel.
- [ ] True Range, Normalized ATR.
- [ ] Ratio de volatilité (mode Haute Volatilité).
- [ ] Stocker dans `market:volatility:current` (Redis).
- [ ] Ajuster le comportement du moteur en mode HV (trailing élargi de 20%).

### 4.12 Session Manager
- [ ] Implémenter `SessionManager` : reset quotidien à 00:00 UTC (APScheduler).
- [ ] Compteur de trades journalier (`session:today:trades_count`).
- [ ] Compteur de pertes consécutives (`session:today:consecutive_losses`).
- [ ] P&L réalisé journalier (`session:today:realized_pl`).
- [ ] Heures de trading programmables (`scheduled_start_time` / `scheduled_stop_time`).
- [ ] Arrêt automatique si limite quotidienne atteinte.

### 4.13 Configuration Persistante des Nouveaux Paramètres
- [ ] Ajouter dans la table `trading_configs` et exposer via API :
  - `sniper_min_score` : défaut 57.
  - `trailing_level_1_multiplier` : défaut 1.5.
  - `trailing_level_2_multiplier` : défaut 3.0.
  - `trailing_level_3_multiplier` : défaut 5.0.
  - `rapid_mode_atr_multiplier` : défaut 0.3.
  - `time_based_be_minutes` : défaut 10.
  - `time_based_be_profit_threshold` : défaut 0.5.
  - `weak_signal_lot_reduction` : défaut 0.7 (70%).
  - `weak_signal_spread_threshold` : défaut 0.8 (80%).
- [ ] Ces paramètres doivent être synchronisés en Redis et pris en compte immédiatement sans redémarrage.

### 4.15 🔴 Sniper AI Adaptive Learning Engine — Évolution Journalière

**Objectif** : Le moteur Sniper AI doit s'adapter automatiquement de jour en jour en analysant ses performances passées et en détectant le régime de marché dominant. Il ajuste dynamiquement ses paramètres internes (poids des indicateurs, seuil de validation, sensibilité) pour maximiser la rentabilité et minimiser le drawdown selon les conditions réelles du marché.

#### 4.15.1 Détection du régime de marché (Market Regime Classifier)
- [ ] Implémenter un `MarketRegimeClassifier` qui analyse les 200 derniers ticks et les 48 dernières barres H1 pour déterminer le régime de marché actuel.
- [ ] Classifier le marché en 4 régimes distincts :
  - **TRENDING_BULL** : tendance haussière forte (ADX > 30, prix au-dessus des 20 dernières moyennes, plus hauts/plus bas ascendants).
  - **TRENDING_BEAR** : tendance baissière forte (ADX > 30, prix en dessous des 20 dernières moyennes, plus hauts/plus bas descendants).
  - **RANGING** : marché en range (ADX < 20, prix oscillant entre support et résistance clairs, Bollinger Bands resserrés).
  - **VOLATILE_CHAOS** : marché chaotique/volatile (ATR > 150% de la moyenne sur 20 périodes, gaps fréquents, rejection wicks longues).
- [ ] Stocker le régime actuel dans Redis sous `market:regime:current` avec un TTL de 5 minutes.
- [ ] Logger l'évolution des régimes dans une table `market_regime_history` (timestamp, régime, confiance 0-100, indicateurs déclencheurs).
- [ ] La confiance du régime doit être calculée : si les 3 derniers échantillons H1 donnent le même régime, confiance = 90%+. Si divergence, confiance = 50-70%.

#### 4.15.2 Table d'apprentissage journalier (Performance Analytics)
- [ ] Créer une table `sniper_learning_log` avec les champs :
  - `date` (jour UTC), `regime_detected`, `total_trades`, `winning_trades`, `losing_trades`, `win_rate`, `profit_factor`, `avg_profit_pips`, `avg_loss_pips`, `max_drawdown_pips`, `avg_score_of_wins`, `avg_score_of_losses`, `avg_sl_distance`, `avg_tp_distance`, `best_performing_indicator`, `worst_performing_indicator`.
- [ ] À minuit UTC (via APScheduler), exécuter un job `DailyLearningAnalysis` qui :
  1. Agrège tous les trades de la journée écoulée depuis `trade_logs`.
  2. Calcule les métriques de performance ci-dessus.
  3. Compare les performances par régime de marché (quel régime a été le plus rentable ?).
  4. Identifie quel indicateur (momentum, RSI micro, volume tick, accélération) a eu le meilleur taux de prédiction.
  5. Persiste le résultat dans `sniper_learning_log`.

#### 4.15.3 Ajustement dynamique des poids du scoring
- [ ] Définir 4 jeux de poids distincts, un par régime de marché. Chaque jeu contient les poids pour : momentum, accélération, RSI micro, volume tick, confluence pattern.
- [ ] Poids par défaut (régime inconnu) : momentum=25, accel=20, rsi=25, volume=15, pattern=15.
- [ ] Poids initiaux par régime :
  - **TRENDING_BULL** : momentum=35, accel=25, rsi=15, volume=10, pattern=15 (privilégier le suivi de tendance).
  - **TRENDING_BEAR** : momentum=35, accel=25, rsi=15, volume=10, pattern=15.
  - **RANGING** : momentum=10, accel=10, rsi=35, volume=15, pattern=30 (privilégier les rebonds sur S/R).
  - **VOLATILE_CHAOS** : momentum=15, accel=30, rsi=20, volume=25, pattern=10 (privilégier la réaction rapide à l'accélération et au volume).
- [ ] Implémenter un algorithme d'ajustement des poids basé sur les résultats de la veille :
  - Si le win rate sur un régime donné est > 60% : augmenter légèrement le poids de l'indicateur qui a eu le meilleur score moyen sur les trades gagnants (+2 points), et diminuer celui qui a eu le pire (-2 points).
  - Si le win rate est < 40% : inverser la logique — diminuer le poids de l'indicateur sur-représenté dans les pertes, augmenter celui sous-représenté.
  - Si le win rate est entre 40% et 60% : ne pas modifier les poids, marquer la journée comme "stable".
  - L'ajustement maximal par jour est de ±5 points par indicateur pour éviter les oscillations brutales.
  - Les poids doivent toujours rester entre 5 et 50, et leur somme doit toujours être égale à 100.
- [ ] Stocker les poids actifs dans Redis sous `sniper:weights:{user_id}` pour un accès temps réel.
- [ ] Les poids sont spécifiques à chaque utilisateur (permettre des personnalisations futures) mais initialisés avec les valeurs globales apprises.

#### 4.15.4 Seuil de validation adaptatif (Adaptive Threshold)
- [ ] Le seuil minimum de validation n'est plus figé à 57 mais devient un **seuil dynamique** compris entre 55 et 62.
- [ ] Logique d'ajustement du seuil :
  - Seuil de base = 57.
  - Si le win rate sur les 3 derniers jours est > 65% → le marché est "facile", le seuil peut être relevé à 59-60 pour n'accepter que les meilleurs signaux et réduire le nombre de trades (qualité > quantité).
  - Si le win rate sur les 3 derniers jours est < 45% → le marché est "difficile", le seuil est abaissé à 55-56 pour capturer plus d'opportunités, mais avec le lot réduit à 60% (au lieu de 70%) pour les scores 55-57.
  - Si le profit factor sur les 3 derniers jours est < 1.0 → baisser le seuil à 55 ET réduire le lot global à 50% jusqu'à amélioration.
  - Si le drawdown max sur les 3 derniers jours dépasse 5% du solde → relever le seuil à 60 ET activer le mode conservateur (SL plus larges, trailing plus agressif).
  - Le seuil ne peut varier que de ±1 point par jour maximum pour éviter les changements trop brutaux.
- [ ] Le seuil adaptatif est recalculé chaque jour à 00:05 UTC (juste après le reset de session) et stocké dans Redis `sniper:adaptive_threshold:{user_id}`.
- [ ] Logger chaque modification du seuil dans `sniper_learning_log` avec la justification (win rate, drawdown, etc.).

#### 4.15.5 Apprentissage par feedback post-trade (Trade Feedback Loop)
- [ ] Pour chaque trade fermé, calculer un **score de prédiction rétrospectif** : si le trade a gagné, quel était le score Sniper au moment de l'ouverture ? Quels indicateurs étaient les plus forts ?
- [ ] Maintenir un buffer circulaire des 100 derniers trades dans Redis (`sniper:trade_feedback:{user_id}`).
- [ ] Si un pattern se révèle : "les trades avec un volume tick > 150% de la moyenne et un RSI micro entre 45-55 ont un win rate de 75%", alors augmenter légèrement le bonus appliqué à ce critère spécifique dans le calcul du score.
- [ ] Implémenter un mécanisme de **décroissance** (decay) : les feedbacks vieux de plus de 5 jours perdent 10% de leur influence par jour pour éviter que des conditions obsolètes persistent.
- [ ] Si un indicateur donne 3 faux signaux consécutifs, son poids est temporairement réduit de 50% pendant 2 heures (cooldown d'apprentissage).

#### 4.15.6 Adaptation de la stratégie par régime
- [ ] Lorsque le `MarketRegimeClassifier` détecte un changement de régime :
  - Charger immédiatement le jeu de poids correspondant.
  - Ajuster le seuil adaptatif selon les performances historiques de ce régime (ex: si le régime RANGING a historiquement un win rate de 35%, relever le seuil de +2 points en range).
  - Notifier le frontend via WebSocket de l'événement `regime.change` avec le nouveau régime et la confiance.
- [ ] En mode **TRENDING_BULL** : privilégier les signaux BUY, ignorer ou fortement pénaliser les signaux SELL (sauf score > 85).
- [ ] En mode **TRENDING_BEAR** : privilégier les signaux SELL, ignorer ou fortement pénaliser les signaux BUY (sauf score > 85).
- [ ] En mode **RANGING** : autoriser les deux directions mais exiger un score plus élevé (+2 points) car les faux breakouts sont fréquents.
- [ ] En mode **VOLATILE_CHAOS** : réduire la taille des lots de 40% supplémentaires, élargir les SL de 25%, et exiger un score > 60 minimum (quelle que soit la configuration adaptative).

#### 4.15.7 Protection contre l'overfitting et les boucles de feedback négatives
- [ ] Implémenter une **fenêtre glissante d'apprentissage** : seuls les trades des 10 derniers jours sont pris en compte pour l'ajustement des poids.
- [ ] Implémenter un **circuit breaker d'apprentissage** : si le win rate chute en dessous de 30% sur 2 jours consécutifs malgré les ajustements, réinitialiser les poids aux valeurs par défaut et fixer le seuil à 58 pendant 24 heures (mode "safe").
- [ ] Implémenter un **plancher de lot** : même en mode adaptatif difficile, le lot ne peut descendre en dessous de 30% du calcul standard du RiskManager pour éviter des trades microscopiques sans intérêt.
- [ ] Logger toute réinitialisation de sécurité dans `audit_logs` avec la raison détaillée.

#### 4.15.8 Frontend — Affichage de l'adaptation en temps réel
- [ ] Sur le dashboard, afficher le régime de marché actuel détecté : "Marché : Tendance Haussière (confiance 92%)" avec un code couleur.
- [ ] Afficher le seuil adaptatif du jour : "Seuil Sniper AI : 56 (adaptatif)" avec une icône d'information expliquant pourquoi (infobulle : "Win rate 3j : 42% → seuil ajusté à la baisse").
- [ ] Afficher les poids actifs des indicateurs sous forme de mini-barres de progression : Momentum 35%, RSI 15%, etc.
- [ ] Afficher un indicateur "Mode apprentissage actif" qui clignote doucement lorsqu'un ajustement a été appliqué dans les dernières 24 heures.
- [ ] Dans le panneau admin, ajouter une section "Performance par régime" avec un tableau montrant le win rate, le profit factor et le nombre de trades pour chacun des 4 régimes sur les 7 derniers jours.

#### 4.15.9 Configuration persistante des paramètres d'apprentissage
- [ ] Ajouter dans `trading_configs` et exposer via API :
  - `adaptive_learning_enabled` : booléen, défaut true.
  - `adaptive_threshold_min` : défaut 55.
  - `adaptive_threshold_max` : défaut 62.
  - `adaptive_threshold_base` : défaut 57.
  - `learning_window_days` : défaut 10.
  - `regime_confidence_min` : défaut 70 (seuil de confiance minimum pour changer de régime).
  - `weight_adjustment_max_daily` : défaut 5.
  - `drawdown_threshold_for_safe_mode` : défaut 5.0 (%).
  - `circuit_breaker_win_rate` : défaut 30.0 (%).
- [ ] Ces paramètres sont modifiables par l'admin et pris en compte immédiatement.

#### 4.15.10 🔴 Tests obligatoires avant build
- [ ] Régime TRENDING_BULL détecté → poids momentum augmenté, signaux BUY privilégiés.
- [ ] Régime RANGING détecté → poids RSI augmenté, seuil relevé de +2, lots inchangés.
- [ ] Régime VOLATILE_CHAOS détecté → lots réduits de 40%, SL élargis de 25%, seuil minimum 60.
- [ ] Win rate 3 jours > 65% → seuil passe de 57 à 58 (max +1/jour).
- [ ] Win rate 3 jours < 45% → seuil passe de 57 à 56 (max -1/jour), lot réduit à 60% pour scores 55-57.
- [ ] Profit factor < 1.0 sur 3 jours → lot global réduit à 50%.
- [ ] Drawdown > 5% → seuil fixé à 60, mode safe activé.
- [ ] 3 faux signaux consécutifs d'un indicateur → poids réduit de 50% pendant 2h.
- [ ] Changement de régime → événement WebSocket `regime.change` reçu côté frontend en < 1s.
- [ ] Fenêtre glissante : trades de J-11 ignorés dans le calcul d'ajustement.
- [ ] Circuit breaker : win rate < 30% sur 2 jours → reset poids + seuil 58 + log audit.
- [ ] Dashboard affiche correctement le régime, le seuil adaptatif et les poids actifs.

### 4.14 🔴 Tests obligatoires avant build
- [ ] Score 56 → trade refusé (NEUTRE).
- [ ] Score 57 avec filtres validés → trade autorisé, lot à 70%, SL conservateur (1.3x ATR).
- [ ] Score 57 avec spread trop élevé → trade refusé malgré le score.
- [ ] Score 65 → trade autorisé, lot standard, SL standard.
- [ ] Score 85 → trade autorisé, lot standard, SL agressif (-15%), trailing activé immédiatement.
- [ ] SL calculé < sl_min → recalé à sl_min + log d'avertissement.
- [ ] SL calculé > sl_max → recalé à sl_max + log d'avertissement.
- [ ] Profit atteint 1.5x SL → SL déplacé au prix d'ouverture (Break-Even).
- [ ] Profit atteint 3x SL → SL verrouille 50% du profit.
- [ ] Profit atteint 5x SL → passage en mode trailing rapide.
- [ ] Position ouverte depuis 10 min avec profit > 0.5x SL mais < 1.5x SL → Time-based BE déclenché.
- [ ] Mode haute volatilité → distance du trailing élargie de 20%.
- [ ] Modification de `sniper_min_score` via API → prise en compte immédiate sans redémarrage.
- [ ] Backtesting sur 1 mois de ticks historiques XAUUSD.
- [ ] Rapport de performance (win rate, profit factor, max drawdown).

---

## Phase 5 : Frontend — Dashboard et Boutons 100% Fonctionnels

### 5.1 Architecture frontend
- [ ] Choisir et configurer le state management (Provider / Riverpod / GetX).
- [ ] Configurer le client HTTP avec intercepteur JWT automatique.
- [ ] Configurer le client WebSocket avec reconnexion automatique.
- [ ] Intégrer le SDK Firebase (Auth + Firestore + Messaging).
- [ ] Définir le système de routing et navigation.
- [ ] Créer le thème global (couleurs, typographie, dark mode).

### 5.2 🔴 Bouton "Démarrer le Robot"
**Action backend réelle** : `POST /trading/start`
- [ ] Le bouton est visible uniquement si le compte MT5 est connecté et le robot est à l'arrêt.
- [ ] Au clic, vérifier côté frontend que le compte MT5 est bien connecté.
- [ ] Désactiver le bouton et afficher un indicateur de chargement.
- [ ] Appeler `POST /trading/start`.
- [ ] Attendre la réponse du backend avant de modifier l'interface.
- [ ] En cas de succès (200) : mettre à jour l'indicateur visuel à "RUNNING 🟢", afficher une confirmation.
- [ ] En cas d'échec : afficher le message d'erreur retourné par le backend, réactiver le bouton.
- [ ] Protéger contre les doubles clics pendant l'appel.

### 5.3 🔴 Bouton "Arrêter le Robot"
**Action backend réelle** : `POST /trading/stop`
- [ ] Le bouton est visible uniquement si le robot est en cours d'exécution.
- [ ] Au clic, afficher une boîte de dialogue de confirmation.
- [ ] Si l'utilisateur confirme, appeler `POST /trading/stop`.
- [ ] Désactiver le bouton pendant l'appel.
- [ ] En cas de succès : mettre à jour l'indicateur visuel à "STOPPED ⚪".
- [ ] Si des positions sont encore ouvertes, informer l'utilisateur que le robot s'arrête mais que les positions restent actives.

### 5.4 🔴 Bouton "Arrêt d'Urgence"
**Action backend réelle** : `POST /trading/emergency-stop`
- [ ] Le bouton est de couleur rouge, visuellement distinct, et placé de manière accessible mais pas sujette aux clics accidentels.
- [ ] Visible uniquement pour les utilisateurs avec le rôle `admin`.
- [ ] Au clic, afficher une boîte de dialogue de confirmation obligatoire avec texte explicite sur les conséquences.
- [ ] Si l'utilisateur confirme, appeler `POST /trading/emergency-stop`.
- [ ] Pendant l'appel, afficher un indicateur de chargement.
- [ ] En cas de succès : afficher une alerte permanente "Arrêt d'urgence déclenché", mettre à jour la liste des positions ouvertes (vide), changer le statut du robot.
- [ ] Ce bouton doit fermer immédiatement toutes les positions via le backend et créer un log d'audit.

### 5.5 Indicateur d'état du robot (visuel temps réel)
- [ ] Cercle vert clignotant doucement = RUNNING.
- [ ] Cercle gris fixe = STOPPED.
- [ ] Cercle rouge clignotant rapidement = ERROR ou EMERGENCY.
- [ ] Texte associé précis : "Robot actif", "Robot arrêté", "Erreur de connexion MT5", "Arrêt d'urgence déclenché".
- [ ] Ce composant est abonné à l'état global et se reconstruit instantanément à chaque changement.

### 5.6 Affichage du prix XAUUSD (temps réel)
- [ ] Afficher le dernier prix en gros caractères, mis à jour à chaque événement `tick.update`.
- [ ] Colorer en vert si supérieur au prix précédent, rouge si inférieur, gris si inchangé.
- [ ] Afficher le spread actuel à côté du prix.
- [ ] Afficher l'heure du dernier tick reçu.
- [ ] Si aucun tick n'est reçu depuis plus de 10 secondes, afficher un avertissement de flux interrompu.

### 5.7 Profit et Perte du jour (temps réel)
- [ ] Afficher le P&L réalisé depuis minuit UTC, mis à jour à chaque `trade.closed`.
- [ ] Vert si positif, rouge si négatif.
- [ ] Afficher le nombre de trades, trades gagnants, trades perdants.
- [ ] Mise à jour instantanée sans action utilisateur.

### 5.8 Solde du compte
- [ ] Afficher le solde courant du compte MT5, récupéré périodiquement (toutes les 30s) et mis à jour immédiatement si une position est fermée.
- [ ] Afficher la marge utilisée et la marge disponible.
- [ ] Marge disponible en orange si < 50% du solde, rouge si < 20%.

### 5.9 Liste des positions ouvertes (temps réel)
- [ ] Liste défilante mise à jour à chaque `position.update`.
- [ ] Pour chaque position : ticket, type (achat/vente), volume, prix d'ouverture, SL, TP, profit flottant.
- [ ] Profit flottant en vert si positif, rouge si négatif.
- [ ] Tri possible par profit, heure d'ouverture, ou volume.
- [ ] Message "Aucune position ouverte" avec icône si la liste est vide.

### 5.10 Indicateur de qualité du signal Sniper AI
- [ ] Afficher la qualité du dernier signal évalué : "Faible (57-64)", "Modéré (65-79)", ou "Fort (80+)".
- [ ] Colorer : orange pour faible, bleu pour modéré, vert pour fort.
- [ ] Afficher la distance initiale du SL calculée pour le prochain trade potentiel.
- [ ] Afficher l'état du Trailing Stop : "Inactif", "Break-Even atteint", "Sécurisation 50%", ou "Mode rapide actif".

### 5.11 Graphique historique des trades
- [ ] Graphique linéaire de l'évolution du profit cumulé.
- [ ] Mis à jour instantanément à chaque `trade.closed`.
- [ ] Périodes sélectionnables : journée, semaine, mois.
- [ ] Animation douce à l'ajout de nouveaux points.

---

## Phase 6 : Frontend — Panneau de Contrôle et Paramètres

### 6.1 🔴 Slider de pourcentage de risque
**Action backend réelle** : `PUT /trading/config`
- [ ] Slider avec bornes min/max configurables (ex: 0.5% à 5%).
- [ ] Valeur affichée à côté du slider.
- [ ] Au relâchement du slider, envoyer immédiatement la requête de mise à jour au backend.
- [ ] Attendre la confirmation du backend avant de valider visuellement le changement.
- [ ] En cas d'échec, réinitialiser le slider à sa valeur précédente et afficher une erreur.

### 6.2 🔴 Toggles (interrupteurs)
**Action backend réelle** : `PUT /trading/config`
- [ ] Toggle "Sniper AI" : active/désactive le moteur SniperAI.
- [ ] Toggle "Micro-Timeframes" : active/désactive l'agrégation des micro-timeframes.
- [ ] Toggle "Hedging" : autorise ou non les positions en sens opposé.
- [ ] Chaque changement d'état envoie une requête au backend.
- [ ] Le backend persiste en PostgreSQL, synchronise dans Redis, et notifie le moteur actif.
- [ ] Le toggle se met à jour immédiatement si un admin modifie la config globale via WebSocket.

### 6.3 🔴 Sélecteur de méthode de Stop-Loss
**Action backend réelle** : `PUT /trading/config`
- [ ] Menu déroulant ou boutons radio : ATR, Swings, Support/Résistance, Hybride.
- [ ] La sélection déclenche une mise à jour de la configuration côté backend.
- [ ] Afficher une description courte de la méthode sélectionnée.

### 6.4 🔴 Inputs de paramètres de SL
**Action backend réelle** : `PUT /trading/config`
- [ ] Input pour la borne minimale du SL.
- [ ] Input pour la borne maximale du SL.
- [ ] Validation côté frontend : valeurs numériques positives, min < max.
- [ ] Envoi au backend à la perte de focus ou au clic sur un bouton "Sauvegarder".

### 6.5 🔴 Paramètres de grille
**Action backend réelle** : `PUT /trading/config`
- [ ] Input pour le nombre maximum de positions par direction.
- [ ] Input pour le nombre total maximum de positions.
- [ ] Validation : entiers positifs, cohérence entre les deux valeurs.

### 6.6 🔴 Inputs d'heures de trading programmables
**Action backend réelle** : `PUT /trading/config`
- [ ] Input pour l'heure de démarrage automatique (`scheduled_start_time`).
- [ ] Input pour l'heure d'arrêt automatique (`scheduled_stop_time`).
- [ ] Format UTC, validation de cohérence (start < stop).

### 6.7 🔴 Paramètres avancés Sniper AI et Trailing Stop
**Action backend réelle** : `PUT /trading/config` (admin uniquement)
- [ ] Input `sniper_min_score` : valeur par défaut 57, modifiable.
- [ ] Input `trailing_level_1_multiplier` : défaut 1.5.
- [ ] Input `trailing_level_2_multiplier` : défaut 3.0.
- [ ] Input `trailing_level_3_multiplier` : défaut 5.0.
- [ ] Input `rapid_mode_atr_multiplier` : défaut 0.3.
- [ ] Input `time_based_be_minutes` : défaut 10.
- [ ] Input `weak_signal_lot_reduction` : défaut 0.7 (70%).
- [ ] Ces paramètres sont visibles uniquement dans le panneau admin ou dans une section "Paramètres avancés" pour les traders.

### 6.8 Reflet immédiat des paramètres
- [ ] Au chargement du panneau, récupérer la configuration complète via `GET /trading/config`.
- [ ] Tous les contrôles initialisés avec les valeurs du backend.
- [ ] Si un autre admin modifie la configuration globale, les contrôles se mettent à jour en temps réel via WebSocket.
- [ ] Aucune divergence entre l'état local et l'état backend.

---

## Phase 7 : Frontend — Temps Réel et WebSocket

### 7.1 Service WebSocket
- [ ] Créer un service dédié à la gestion de la connexion WebSocket, initialisé dès l'authentification.
- [ ] Établir la connexion en passant le token JWT pour identification côté backend.
- [ ] Implémenter une reconnexion automatique avec backoff exponentiel (max 30s entre tentatives).
- [ ] Limite de 10 tentatives avant affichage d'un message d'erreur persistant.
- [ ] À chaque reconnexion, récupérer l'état complet actuel via une requête HTTP de synchronisation.
- [ ] Fournir une méthode publique pour connaître l'état de connexion.

### 7.2 Réception et traitement des événements
- [ ] **tick.update** : mettre à jour le prix XAUUSD, le spread, l'horodatage. Stocker l'historique des 100 derniers ticks.
- [ ] **position.update** : remplacer la liste des positions ouvertes, recalculer le profit total.
- [ ] **trade.closed** : ajouter à l'historique, mettre à jour le P&L cumulé, décrémenter les positions ouvertes.
- [ ] **volatility.alert** : mettre à jour l'indicateur de volatilité et le mode haute volatilité.
- [ ] **robot.status** : mettre à jour immédiatement l'indicateur visuel du statut.
- [ ] **emergency.triggered** : déclencher une alerte modale bloquante et forcer l'arrêt des animations.

### 7.3 Indicateur de volatilité (temps réel)
- [ ] Indicateur visuel mis à jour par `volatility.alert`.
- [ ] Vert = faible, orange = modérée, rouge = élevée.
- [ ] Bannière d'avertissement en mode haute volatilité indiquant un ajustement automatique des paramètres.

### 7.4 Notifications push locales
- [ ] Système de notifications locales Flutter fonctionnant même en arrière-plan.
- [ ] Déclenchées pour : perte journalière atteignant la limite, robot démarré/arrêté, arrêt d'urgence, position fermée avec montant.

### 7.5 Alertes modales
- [ ] **Alerte bloquante** : `emergency.triggered` → empêche toute interaction jusqu'à acquittement.
- [ ] **Alerte non bloquante** : perte journalière à 80% de la limite → avertissement que le robot va s'arrêter.
- [ ] **Alerte de déconnexion** : WebSocket perdu depuis > 30s → données potentiellement obsolètes.

### 7.6 🔴 Tests obligatoires avant build
- [ ] Tick reçu → prix affiché mis à jour en < 1 seconde.
- [ ] Position ouverte côté backend → apparition dans la liste en < 1 seconde.
- [ ] Position fermée côté backend → disparition de la liste + ajout historique en < 1 seconde.
- [ ] P&L mis à jour immédiatement après fermeture d'une position.
- [ ] Déconnexion WebSocket simulée → reconnexion auto + resynchronisation.
- [ ] Arrêt d'urgence backend → alerte modale immédiate côté frontend.
- [ ] Modification config par admin → reflet temps réel sur le panneau de contrôle d'un autre utilisateur.
- [ ] Application en arrière-plan → notifications push reçues pour les événements critiques.

---

## Phase 8 : Tests Obligatoires Avant Tout Build

### 8.1 Tests unitaires backend
- [ ] Auth Google valide → création user + JWT.
- [ ] Auth Google invalide → 401.
- [ ] Middleware JWT valide → accès autorisé.
- [ ] Middleware JWT expiré → 401.
- [ ] Rôle admin → accès routes admin.
- [ ] Rôle viewer → 403 sur routes trading/admin.
- [ ] Chiffrement/déchiffrement mot de passe MT5.
- [ ] Connexion MetaApi mockée → succès.
- [ ] Connexion MetaApi mockée → échec + reconnexion.
- [ ] SniperAIEngine : scoring 57-64 → lot 70%, SL conservateur.
- [ ] SniperAIEngine : scoring 65-79 → lot standard, SL standard.
- [ ] SniperAIEngine : scoring 80+ → lot standard, SL agressif, trailing immédiat.
- [ ] SniperAIEngine : scoring < 57 → NEUTRE, pas d'ordre.
- [ ] DynamicSLCalculator : méthodes ATR, Swings, S/R, Hybride + bornes min/max.
- [ ] DynamicSLCalculator : score 57-64 → multiplicateur 1.3x.
- [ ] DynamicSLCalculator : score 80+ → distance réduite de 15%.
- [ ] TrailingStopManager : niveau 1 à 1.5x → BE.
- [ ] TrailingStopManager : niveau 2 à 3x → sécurisation 50%.
- [ ] TrailingStopManager : niveau 3 à 5x → mode rapide.
- [ ] TrailingStopManager : time-based BE après 10 min.
- [ ] TrailingStopManager : mode HV → distance élargie de 20%.
- [ ] RiskManager : calcul lots selon solde, risque, tick value XAUUSD.
- [ ] RiskManager : lot réduit à 70% pour scores 57-64.
- [ ] SessionManager : reset quotidien à 00:00 UTC, compteurs, limites.
- [ ] ExecutionManager : filtres pré-exécution scores 57-64 (spread, ADX, volatilité).

### 8.2 Tests d'intégration API
- [ ] Flux complet login Google → dashboard → connexion MT5 → trading actif.
- [ ] API ↔ MetaApi : exécution d'ordres sur compte démo.
- [ ] API ↔ PostgreSQL : CRUD complet.
- [ ] API ↔ Redis : cache, pub/sub.
- [ ] WebSocket : connexion, events, déconnexion, reconnexion.
- [ ] Auth : JWT Firebase, rôles, permissions.
- [ ] Rate limiting : 11 requêtes/minute → 429.
- [ ] Multi-utilisateurs : 2 users simultanés → isolation complète des données et événements.
- [ ] Signal score 58 → filtres validés → ordre envoyé avec lot réduit et SL élargi.
- [ ] Signal score 82 → ordre envoyé avec SL serré → trailing déclenché automatiquement.
- [ ] Vérification que le TrailingStopManager modifie bien le SL via MetaApi toutes les secondes.
- [ ] Vérification que les logs de modification de SL sont bien persistés en base.

### 8.3 Tests end-to-end Flutter
- [ ] Parcours login → dashboard → control panel complet.
- [ ] Scénario admin : gestion users, override config.
- [ ] Scénario arrêt d'urgence : clic bouton → confirmation → positions fermées → alerte.
- [ ] Compatibilité : Web (Chrome, Firefox, Safari, Edge), Android, iOS.
- [ ] Temps réel : tick → prix mis à jour, position ouverte/fermée → liste mise à jour.
- [ ] Dashboard affiche correctement "Signal Faible" en orange lorsqu'un trade avec score 57-64 est ouvert.
- [ ] Dashboard affiche correctement le statut du trailing : passage de "Inactif" à "Break-Even" quand le seuil est atteint.

### 8.4 Tests de charge
- [ ] 10 utilisateurs simultanés → pas de fuite mémoire.
- [ ] Latence moyenne API < 200ms sous charge.
- [ ] CPU et mémoire VPS < 70% sous charge.

### 8.5 🔴 Règle de gouvernance
- [ ] Taux de couverture de code backend ≥ 80%.
- [ ] Zéro test end-to-end en échec.
- [ ] Zéro test d'intégration en échec.
- [ ] Si un test échoue → build bloqué, correction obligatoire.

---

## Phase 9 : Build Complet et Déploiement Production

### 9.1 Préparation du VPS Oracle Cloud
- [ ] Créer un compte Oracle Cloud (Always Free).
- [ ] Provisionner l'instance ARM (4 OCPU / 24 GB RAM / 200 GB disk / Ubuntu 22.04).
- [ ] Configurer l'accès SSH (clé publique uniquement, root désactivé).
- [ ] Configurer le pare-feu UFW : ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API).
- [ ] Installer Docker + Docker Compose.
- [ ] Créer un utilisateur dédié au déploiement.

### 9.2 Base de données et cache
- [ ] Rédiger le `docker-compose.prod.yml` avec : PostgreSQL 15, Redis 7, FastAPI (2 workers), Nginx, Prometheus, Grafana.
- [ ] Créer les volumes Docker persistants pour PostgreSQL et Redis.
- [ ] Exécuter les migrations SQL initiales au premier démarrage.
- [ ] Vérifier la connectivité PostgreSQL + Redis.

### 9.3 Build backend
- [ ] Dockerfile multi-étapes pour réduire la taille de l'image.
- [ ] Uvicorn avec Gunicorn, 2 workers asynchrones, host 0.0.0.0, port 8000.
- [ ] Variables d'environnement de production dans un fichier `.env` (jamais dans le code).
- [ ] Compression des réponses HTTP.
- [ ] En-têtes de sécurité HTTP via Nginx.

### 9.4 Build frontend Flutter
- [ ] Compilation web en mode release (CanvasKit).
- [ ] Compilation Android (App Bundle signé).
- [ ] Compilation iOS (archive signé).
- [ ] Variables d'environnement injectées au build (URL API, URL WebSocket, config Firebase).
- [ ] Test sur Chrome, Firefox, Safari, Edge.
- [ ] Test sur appareils physiques Android et iOS.

### 9.5 DNS et SSL
- [ ] Configurer un domaine sur Cloudflare (plan Free).
- [ ] Enregistrement A pointant vers le VPS Oracle.
- [ ] Activer le proxy Cloudflare + protection DDoS de base.
- [ ] Forcer le mode SSL strict.
- [ ] Certificats Let's Encrypt via Certbot, auto-renouvelables.
- [ ] Nginx configuré comme reverse proxy avec terminaison SSL.
- [ ] Support WebSocket dans la configuration Nginx (headers Upgrade).

### 9.6 Déploiement
- [ ] Copier le `docker-compose.prod.yml`, le `.env` et la config Nginx sur le VPS.
- [ ] Lancer les conteneurs en mode détaché.
- [ ] Vérifier que tous les services sont en état `healthy`.
- [ ] Vérifier que l'endpoint `/health` répond correctement.
- [ ] Vérifier que Swagger UI est accessible.
- [ ] Vérifier que la connexion WebSocket s'établit depuis le navigateur.

### 9.7 Tests de validation post-déploiement
- [ ] Créer un compte via Google Sign-In sur l'instance de production.
- [ ] Configurer un compte MT5 démo Exness.
- [ ] Connecter le compte MT5 → statut "Connecté".
- [ ] Démarrer le robot → statut "RUNNING".
- [ ] Laisser fonctionner 1 heure minimum, vérifier la réception des ticks.
- [ ] Vérifier qu'une position est ouverte automatiquement et apparaît dans la liste.
- [ ] Tester le bouton arrêt d'urgence → toutes positions fermées + alerte diffusée.
- [ ] Simuler 5 utilisateurs simultanés, mesurer latence (< 200ms) et ressources (< 70%).

### 9.8 Semaine d'évaluation sur compte démo
- [ ] Maintenir l'application en fonctionnement pendant 1 semaine sans interruption.
- [ ] Surveiller quotidiennement : nombre de trades, win rate, profit factor, max drawdown, latence, erreurs.
- [ ] Documenter tout comportement anormal.
- [ ] Produire un rapport de performance détaillé avec graphiques.
- [ ] Ne passer en réel qu'après validation de la stabilité et rentabilité sur démo.

---

## Phase 10 : Monitoring, Observabilité et Documentation

### 10.1 Monitoring
- [ ] Configurer UptimeRobot : ping `GET /health` toutes les 5 minutes.
- [ ] Déployer Prometheus + Grafana en Docker.
- [ ] Dashboard Grafana : nombre de trades, latence API, P&L, uptime, CPU, mémoire.
- [ ] Alertes Grafana : robot down, perte journalière atteinte, erreur critique, mémoire > 80%.

### 10.2 Logs
- [ ] Rotation des logs Docker via logrotate.
- [ ] Conservation : 30 jours pour les logs applicatifs, 7 jours pour les logs Nginx.
- [ ] Centralisation des erreurs critiques dans un canal de notification.

### 10.3 Documentation
- [ ] `README.md` du repo : architecture, prérequis, installation locale, commandes de test.
- [ ] Documentation API : endpoints, payloads, exemples de requêtes/réponses.
- [ ] Guide de déploiement VPS Oracle : étape par étape.
- [ ] Procédure de restauration en cas de panne : redémarrage, restauration BDD, bascule secours.
- [ ] Documentation des variables d'environnement avec description et exemples.

---

## Récapitulatif Global

| Phase | Description | Critique |
|-------|-------------|----------|
| 0 | Prérequis et règles d'or | 🔴 |
| 1 | Auth Google + JWT + Rôles | 🔴 |
| 2 | Connexion MT5 + Démarrage auto | 🔴 |
| 3 | API Backend complète | 🔴 |
| 4 | Moteur Trading Core (Sniper AI 57% + Learning Engine adaptatif, SL adaptatif, Trailing dynamique) | 🔴 |
| 5 | Dashboard + Boutons fonctionnels | 🔴 |
| 6 | Panneau de contrôle + Paramètres | 🔴 |
| 7 | Temps réel WebSocket | 🔴 |
| 8 | Tests avant build | 🔴 |
| 9 | Build + Déploiement production | 🔴 |
| 10 | Monitoring + Documentation | 🟡 |

**Rappels impératifs** :
- Tout bouton du frontend exécute une action réelle sur le backend. Aucun mock. Aucun stub.
- Le seuil Sniper AI est fixé à **57** avec réduction de lot à 70% pour les signaux faibles.
- Le Trailing Stop fonctionne par paliers : BE à 1.5x, sécurisation 50% à 3x, mode rapide à 5x.
- Le Time-based Break-Even sécurise les positions stagnantes après 10 minutes.

---

*Document unifié généré le 2026-05-08 — Version 3.0*
