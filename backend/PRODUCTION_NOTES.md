# Notes pour la mise en production

## Modifications temporaires (Python 3.13 Windows dev)

Les éléments suivants ont été retirés ou modifiés pour le développement local sur Python 3.13 / Windows.
**Rétablir ces éléments** lors du déploiement en production (Linux + Python 3.11).

---

### 1. `redis[hiredis]` → `redis`

- **Original :** `redis[hiredis]==5.1.0`
- **Dev local :** `redis` (sans hiredis)
- **Raison :** `hiredis` n'a pas de wheel pré-compilé pour Python 3.13 sur Windows
- **Impact :** Redis fonctionne sans hiredis, mais ~30% plus lent sur le parsing. Aucun impact fonctionnel.
- **En prod :** Remettre `redis[hiredis]==5.1.0`

### 2. `pandas-ta` retiré

- **Original :** `pandas-ta==0.3.14b1`
- **Dev local :** Non installé (incompatible pandas 3.x sur Python 3.13)
- **Raison :** pandas-ta 0.3.14b1 dépend de pandas <2.0, et la seule version pandas disponible pour Python 3.13 est 3.x
- **Impact :** Si le code utilise `pandas_ta`, il faudra mock ou conditionner ces imports en dev. En prod avec Python 3.11, pandas 2.2.2 + pandas-ta 0.3.14b1 fonctionnent.
- **En prod :** Remettre `pandas-ta==0.3.14b1` avec `pandas==2.2.2`

### 3. Versions non épinglées

- **Original :** Versions strictes (==) pour tous les packages
- **Dev local :** Versions libres pour résoudre les conflits Python 3.13
- **En prod :** Utiliser le `requirements.txt` original avec versions épinglées :

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.2
redis[hiredis]==5.1.0
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
cryptography==43.0.1
firebase-admin==6.5.0
httpx==0.27.2
numpy==2.1.1
pandas==2.2.2
pandas-ta==0.3.14b1
websockets==13.0.1
apscheduler==3.10.4
python-dotenv==1.0.1
```

---

## Configuration production (.env)

Éléments à changer avant déploiement :

| Variable | Dev | Prod |
|----------|-----|------|
| `DATABASE_URL` | `localhost:5432` | URL du serveur PostgreSQL |
| `REDIS_URL` | `localhost:6379` | URL du serveur Redis |
| `JWT_SECRET` | `change-this...` | Clé aléatoire 64 chars |
| `JWT_REFRESH_SECRET` | `change-this...` | Clé aléatoire 64 chars |
| `ENCRYPTION_KEY` | placeholder | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `DEBUG` | `false` | `false` |
| `CORS_ORIGINS` | localhost | Domaine(s) de prod |

---

## Environnement recommandé pour production

- **OS :** Ubuntu 22.04 / Debian 12
- **Python :** 3.11.x (le plus stable pour toutes les dépendances)
- **Docker :** PostgreSQL 15 + Redis 7
- **Reverse proxy :** Nginx + SSL (Let's Encrypt)
