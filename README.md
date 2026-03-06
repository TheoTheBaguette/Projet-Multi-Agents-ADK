# Chef Cuisinier Virtuel - Système Multi-Agents ADK

## Description du projet

### Concept

Le **Chef Cuisinier Virtuel** est un assistant culinaire intelligent qui utilise une architecture multi-agents pour aider les utilisateurs à cuisiner en fonction de leurs ingrédients disponibles.

### Fonctionnalités

- **Gestion d'inventaire** : Stocke et mémorise les ingrédients disponibles
- **Recherche de recettes** : Trouve des recettes compatibles avec les ingrédients possédés
- **Instructions de cuisine** : Donne les instrcutions de pour la recettes de cuisine
- **Substitutions d'ingrédients** : Propose des alternatives d'ingredients
- **Liste de courses** : Génère automatiquement les ingrédients manquants
- **Génération de menus** : Crée des menus complets (entrée-plat-dessert)
- **Validation d'inventaire** : Vérifie la disponibilité des ingrédients

---

## Architecture Multi-Agents

### Schéma visuel

**Voir les différent fichier  d'évolution pour les différentes versions (comme par exemple des test de sequetial , de boucle  workflow, etc ) () pour le diagramme complet de l'architecture.**

- *Version 1* : test avec un workflow de parallèle , fonctionne pas avec modèle faible et je n'aimais pas la structure
- *Version 2* : remplacement du workflow de parallèle avec un workflow loop , marche mieux pour l'idée mais galère toujours avec le modèle faible 

### Structure des agents Final

```
root_agent (Coordinateur principal)
├── inventory_agent (Gestion inventaire)
├── recipe_agent (Recherche recettes)
├── cooking_agent (Instructions)
├── recipe_planning_pipeline (SequentialAgent)
│   ├── inventory_agent
│   ├── recipe_agent
│   └── cooking_agent
├── menu_generator_loop (LoopAgent, max_iterations=3)
│   └── menu_course_agent (Génère entrée/plat/dessert)
└── inventory_validator_loop (LoopAgent, max_iterations=5)
    └── ingredient_checker_agent (Valide ingrédients un par un)
```

### Description des agents

| Agent | Rôle | Type | Output Key |
|-------|------|------|------------|
| **root_agent** | Coordinateur principal | LlmAgent | - |
| **inventory_agent** | Gère l'inventaire d'ingrédients | LlmAgent | `user_ingredients` |
| **recipe_agent** | Recherche et recommande des recettes | LlmAgent | - |
| **cooking_agent** | Guide les instructions de cuisine | LlmAgent | - |
| **recipe_planning_pipeline** | Exécute séquentiellement : inventaire → recettes → cuisine | SequentialAgent | - |
| **menu_generator_loop** | Génère un menu complet (entrée-plat-dessert) | LoopAgent (3 it.) | - |
| **inventory_validator_loop** | Valide les ingrédients un par un | LoopAgent (5 it.) | - |

### Les 4 outils custom

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `search_recipes_by_ingredients()` | Recherche des recettes compatibles | `available_ingredients: List[str]` |
| `suggest_substitution()` | Propose des substitutions d'ingrédients | `missing_ingredient: str, available_ingredients: List[str]` |
| `get_recipe_instructions()` | Récupère les instructions détaillées | `recipe_name: str` |
| `generate_shopping_list()` | Génère une liste de courses | `recipe_name: str, available_ingredients: List[str]` |

---

## Modèles testés

| Modèle | Taille | Temps de réponse | 
|--------|--------|------------------ |
| **llama3.2:latest** | 2GB | 2 min/échange
| **gemma2: latest**| 5GB | 20 min sans réponse
| **gemma2:2b** | 2GB | 2 min/échange
| **gemini-2.5-flash** | Cloud | instané
| **gemini-3.1-flash-lite** | Cloud | instané


## Tests et problèmes rencontrés

**Problème principal :** PC avec faibles performances pour les modèles local

**Sur le choix du modèle**

Mon ordinateur étant assez faible en termes de performances, j'ai rapidement compris que les modèles locaux n'allaient pas être viables pour ce projet. Même avec un modèle de 2GB comme llama3.2, il fallait attendre plus de deux minutes juste pour le lancer, puis environ une minute pour chaque échange avec les agents. Ça devenait ingérable. J'ai même tenté avec un modèle de 5GB, mais après 20 minutes d'attente sans aucune réponse, j'ai abandonné l'idée d'utiliser des modèles plus gourmands.

La solution est venue de l'API Gemini. Non seulement c'était beaucoup plus rapide, mais ça m'a aussi permis de faire des tests plus variés et de mieux comprendre les erreurs du système. Par exemple, même avec Gemini qui est un modèle puissant, j'ai remarqué des problèmes de reconnaissance des ingrédients : si l'utilisateur met un "s" en plus (comme "oeufs" au lieu de "oeuf"), le modèle local ne le reconnaissait pas. 


Malgré tout, j'ai continué à tester avec le modèle 2GB en parallèle. Parce que ses limitations m'ont forcé à optimiser mes prompts. Quand un modèle faible échoue, ça met en lumière les faiblesses de la conception. Ça m'a poussé à écrire des instructions plus précises, et mieux structurées. La où ces erreurs ne serait pas arrivé avec Gémini


## Problème de prompt et d'agent

**Le problème du ParallelAgent**

Un des gros soucis a été avec le ParallelAgent. Le modèle local avait vraiment du mal avec cette architecture. Je pense que mon idée initiale pour orchestrer des agents parallèles était peut-être trop confuse pour un petit modèle. Le système choisissait parfois le workflow séquentiel, parfois le parallèle, ce qui rendait le comportement imprévisible. Je suis donc passé aux LoopAgent avec une approche différente : un loop qui propose un menu complet avec les ingrédients disponibles (`menu_generator_loop` avec 3 itérations pour entrée-plat-dessert) et un autre pour valider les ingrédients un par un (`inventory_validator_loop` avec 5 itérations maximum). Mais là encore, le modèle faible en local hallucine et confond parfois mon LoopAgent avec un outil. 
*J'ai donc bien préciser au root agent de ne pas les appeler en tant que outil mais avec mon modèle faible il ignore cette remarque et me l'appele en tool....*

**Les boucles infinies**

Le problème le plus frustrant a été les boucles infinies, surtout avec les modèles pas assez puissants. L'agent appelle un outil de recherche, reçoit un résultat vide, et au lieu de s'arrêter, il réessaie indéfiniment. La solution a été d'ajouter dans les instructions de chaque agent qu'il doit utiliser l'outil une seule fois avec des mots clés comme "UNE SEULE FOIS", "STOP", "ARRÊTE". Mais il fallait aussi être plus précis : l'agent doit proposer une recette même si l'utilisateur ne possède qu'un seul ingrédient parmi ceux nécessaires. Sans cette précision, il ne trouvait rien et recommençait.

**Cas limites testés**

J'ai testé plusieurs situations problématiques : demander la liste des ingrédients alors que l'inventaire est vide (l'agent répond maintenant correctement "Aucun ingrédient stocké"), proposer des ingrédients qui ne correspondent à aucune recette (l'agent propose des recettes inspirantes avec substitutions grâce à Gemini), utiliser des variantes de mots comme "oeuf" vs "oeufs" ou "tomate" vs "tomates" (le modèle ne reconnaît pas toujours). Chaque test a révélé des fragilités dans les prompts qu'il a fallu corriger.

**Problème avec les templates de state partagé**

La contrainte 4 du TP exige l'utilisation d'un `output_key` et de templates `{variable}`. Le problème : les templates ADK crashent avec `KeyError` si la variable n'existe pas dans le state. Or, un agent comme `recipe_agent` peut être appelé directement ("donne-moi une recette avec des oeufs") ou via le pipeline séquentiel. Dans le premier cas, `inventory_agent` n'a jamais été exécuté donc `user_ingredients` n'existe pas. Si on met le template `{user_ingredients}` dans l'instruction de `recipe_agent`, l'appel direct crashe. Solution adoptée : garder `output_key="user_ingredients"` dans `inventory_agent` pour satisfaire la contrainte, mais ne pas utiliser de templates explicites dans les agents appelables directement. Le state fonctionne dans le `recipe_planning_pipeline` de manière transparente.

## Workflow Agents en détail

### 1. SequentialAgent : `recipe_planning_pipeline`

Enchaîne les agents dans un ordre précis pour planifier une recette complète :
```
1. inventory_agent → Enregistre les ingrédients disponibles
2. recipe_agent → Trouve des recettes compatibles
3. cooking_agent → Donne les instructions de préparation
```

**Cas d'usage :** Workflow complet de A à Z pour cuisiner

### 2. LoopAgent : `menu_generator_loop`

Génère un menu complet en itérant 3 fois :
```
Itération 1: Entrée (ex: Salade)
Itération 2: Plat principal (ex: Lasagnes)
Itération 3: Dessert (ex: Tiramisu)
```
''''''''''''''''''CORIGERRRRRR'''''''''''''''''''''''''''''''''''''


**Cas d'usage :** Vérification interactive de l'inventaire

### Communication inter-agents

**State partagé** : Les agents communiquent via un état partagé :
- `inventory_agent` sauvegarde les ingrédients avec `output_key="user_ingredients"`
- Les autres agents accèdent à ces données via `{user_ingredients}` dans leurs instructions

**Exemple de flux :**
```
User → inventory_agent → state["user_ingredients"] = ["oeuf", "lait"]
                                    ↓
                          recipe_agent accède à {user_ingredients}
```

'''''''''''''''''''''''''''''''''''''''''''''''''''''''

### Callbacks implémentés

Deux types de callbacks sont implémentés pour le logging et la traçabilité :

1. **before_agent_callback** : Enregistre le démarrage d'un agent (nom, timestamp)
2. **after_tool_callback** : Enregistre l'exécution d'un outil (nom, résultat, durée)

---

## Installation / Pré-requis

- **Python 3.10+** installé
- **Choix du modèle :**
Dans un env un peut mettre soit en local , soit avec une api:
  - *Option Api* : clé Api (exemple pour gémini)
  - *Option Local* : Ollama installé localement + modèle téléchargé

### Étapes d'installation

1. **Cloner le projet**
```bash
git clone <votre-repo>
cd Projet-Multi-Agents-ADK
```

2. **Créer l'environnement virtuel**
```bash
python -m venv .venv
```

3. **Activer l'environnement virtuel**

Windows PowerShell :
```powershell
.venv\Scripts\Activate.ps1
```

4. **Installer les dépendances**
```bash
pip install google-adk
```

5. **Configurer le modèle**

**Option A : clé API**

Créer/éditer `my_agent/.env` :
```env
GOOGLE_API_KEY=votre_clé_api_ici
ADK_MODEL_PROVIDER=google (si vous utiliser gémini)
ADK_MODEL_NAME=gemini-2.5-flash
```

**Option B : Ollama**

1. Installer Ollama
2. Télécharger un modèle (par exemple llama3.2) :
```bash
ollama run llama3.2
```
3. Créer/éditer `my_agent/.env` :
```env
ADK_MODEL_PROVIDER=ollama
ADK_MODEL_NAME=ollama/llama3.2:latest
```

### Vérification de l'installation

```bash
python test_system.py
```

Tous les tests doivent passer

---

## Lancement

### Option 1 : Interface Web 

```bash
adk web
```

### Option 2 : Ligne de commande (Runner programmatique)

```bash
python main.py
```

Interface en ligne de commande interactive

---

## Exemples d'utilisation

(Remarque pour : 1.1 , 1.2 , etc ; cela signifie qu'il faut l'executer à la suite dans le même ADK )

### Scénario 1.1 : Enregistrer ses ingrédients

**Vous :** `J'ai des œufs, du lait, de la farine, du beurre et du sucre`

**Chef :** Enregistre les ingrédients et confirme

### Scénario 1.2 : Chercher des recettes

**Vous :** `Qu'est-ce que je peux cuisiner avec ce que j'ai ?`

**Chef :** Affiche :
- Recettes 100% possibles (tous les ingrédients disponibles)
- Recettes presque possibles (1-2 ingrédients manquants)
- Recettes inspirantes (pour planifier les courses)

### Scénario 2 : Obtenir des instructions

**Vous :** `Comment faire des crêpes ?`

**Chef :** Donne les instructions détaillées étape par étape

### Scénario 3 : Demander une substitution

**Vous :** `Je n'ai pas de beurre, par quoi je peux le remplacer ?`

**Chef :** Suggère de l'huile ou de la margarine avec des conseils

### Scénario 4   : Liste de courses

**Vous :** `De quoi j'ai besoin pour faire des crêpes ?`

**Chef :** Génère une liste de courses avec ce qu'il faut acheter

### Scénario 5 : Créer un menu

**Vous :** `Propose moi un menu avec des oeufs et de la farine`

**Chef :** Gènere une entrée , un plat et un dessert qui comprenne des oeufs et de la farine.




