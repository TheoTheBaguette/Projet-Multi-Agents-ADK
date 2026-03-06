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
- *Version 3* : Correction du problème avec le séquentielle qui n'arrivait pas à utiliser le state correctement étant donné que le `root agent` pouvez appeler tous les agents du séquentielle et donc ne passe pas par le séquentielle -> ajout de nouveaux agents pouvant répondre aux demandes plus spécifique de l'utilisateur et fait sorte que le workflow séquentielle fonctionne comme attendu.
- *Version 4 (final)* : suppresion de l'agent `inventory_validator_loop` qui ne servait pas vraiment au final dans les différents instruction de mon projet (il demandé aux utilisateurs s'il possedait les ingredient en fonction de la recette), le loop semblait inutile , sa faisait des prompt de l'ia inutile

### Structure des agents Final

```
root_agent (Coordinateur principal)
├── inventory_agent (Gestion inventaire)
├── recipe_agent (Recherche recettes - appels directs)
├── cooking_instructions_agent (Instructions - appels directs)
├── recipe_planning_pipeline (SequentialAgent - DÉMONTRE STATE PARTAGÉ)
│   ├── inventory_agent
│   ├── recipe_search_with_state (avec template {user_ingredients})
│   └── cooking_with_state (avec template {user_ingredients})
└── menu_generator_loop (LoopAgent, max_iterations=3)
    └── menu_course_agent (Génère entrée/plat/dessert)
```


| Agent | Rôle | Type | Template | Output Key |
|-------|------|------|----------|------------|
| **root_agent** | Coordinateur principal | LlmAgent | - | - |
| **inventory_agent** | Gère l'inventaire d'ingrédients | LlmAgent | - | `user_ingredients` |
| **recipe_agent** | Recherche recettes (appels directs) | LlmAgent | - | - |
| **cooking_instructions_agent** | Instructions pour UNE recette (appels directs) | LlmAgent | - | - |
| **recipe_search_with_state** | Recherche recettes avec state partagé | LlmAgent | `{user_ingredients}` | - |
| **cooking_with_state** | Instructions adaptées aux ingrédients disponibles | LlmAgent | `{user_ingredients}` | - |
| **recipe_planning_pipeline** | Pipeline complet : inventaire → recettes → cuisine | SequentialAgent | - | - |
| **menu_generator_loop** | Génère un menu complet (entrée-plat-dessert) | LoopAgent (3 it.) | - | - |

### Les 4 outils custom

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `search_recipes_by_ingredients()` | Recherche des recettes compatibles | `available_ingredients: List[str]` |
| `suggest_substitution()` | Propose des substitutions d'ingrédients | `missing_ingredient: str, available_ingredients: List[str]` |
| `get_recipe_instructions()` | Récupère les instructions détaillées | `recipe_name: str` |
| `generate_shopping_list()` | Génère une liste de courses | `recipe_name: str, available_ingredients: List[str]` |

---

### Les 2 mécanismes de délégation

Le projet utilise `transfer_to_agent` (délégation complète via `root_agent.sub_agents`) et `AgentTool` (transformation d'agent en outil : `recipe_search_tool = AgentTool(agent=recipe_agent)` utilisé par `cooking_instructions_agent`).

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

Un des gros soucis a été avec le ParallelAgent. Le modèle local avait vraiment du mal avec cette architecture. Je pense que mon idée initiale pour orchestrer des agents parallèles était peut-être trop confuse pour un petit modèle. Le système choisissait parfois le workflow séquentiel, parfois le parallèle, ce qui rendait le comportement imprévisible. Je suis donc passé à un LoopAgent avec une approche différente : un loop qui propose un menu complet avec les ingrédients disponibles (`menu_generator_loop` avec 3 itérations pour entrée-plat-dessert). Mais là encore, le modèle faible en local hallucine et confond parfois mon LoopAgent avec un outil. 
*J'ai donc bien préciser au root agent de ne pas les appeler en tant que outil mais avec mon modèle faible il ignore cette remarque et me l'appele en tool....*

**Les boucles infinies**

Le problème le plus frustrant a été les boucles infinies, surtout avec les modèles pas assez puissants. L'agent appelle un outil de recherche, reçoit un résultat vide, et au lieu de s'arrêter, il réessaie indéfiniment. La solution a été d'ajouter dans les instructions de chaque agent qu'il doit utiliser l'outil une seule fois avec des mots clés comme "UNE SEULE FOIS", "STOP", "ARRÊTE". Mais il fallait aussi être plus précis : l'agent doit proposer une recette même si l'utilisateur ne possède qu'un seul ingrédient parmi ceux nécessaires. Sans cette précision, il ne trouvait rien et recommençait.

**Cas limites testés**

J'ai testé plusieurs situations problématiques : demander la liste des ingrédients alors que l'inventaire est vide (l'agent répond maintenant correctement "Aucun ingrédient stocké"), proposer des ingrédients qui ne correspondent à aucune recette (l'agent propose des recettes inspirantes avec substitutions grâce à Gemini), utiliser des variantes de mots comme "oeuf" vs "oeufs" ou "tomate" vs "tomates" (le modèle ne reconnaît pas toujours). Chaque test a révélé des fragilités dans les prompts qu'il a fallu corriger.

**Problème avec les templates de state partagé**

La contrainte 4 du TP exige l'utilisation d'un `output_key` et de templates `{variable}`. Le problème : les templates ADK crashent avec `KeyError` si la variable n'existe pas dans le state. Or, un agent comme `recipe_agent` peut être appelé directement ("donne-moi une recette avec des oeufs"). Dans ce cas, `inventory_agent` n'a jamais été exécuté donc `user_ingredients` n'existe pas et il y a une erreur.

**Solution adoptée** : Architecture à deux niveaux avec agents séparés.

1. **Agents pour appels directs** (dans `root.sub_agents`) :
   - `recipe_agent` : 
   - `cooking_instructions_agent` 
Fonctionnent toujours, pas de crash si jamais l'utilisateur demande directement des recettes ou les instructions de celle si

2. **Agents pour Sequential uniquement** (PAS dans `root.sub_agents`) :
   - `recipe_search_with_state` : AVEC template `{user_ingredients}`
   - `cooking_with_state` : AVEC template `{user_ingredients}`
   -  Utilisés uniquement dans `recipe_planning_pipeline` où `inventory_agent` s'exécute en premier

**Problème dernière version du projet avec le modèle local**

Le modèle local ne fonctionne plus dutout :
- il hallucine des tools qui n'existe même pas par exemple dans `recipe_agent`, pourtant c'est bien préciser quel tool utilisé
- Il me fait des boucles infini , même s'il trouve la réponse , il continue de rappeler le tool encore et encore alors qu'encore une fois il est préciser de faire une seul fois
- Il cofond aussi les types de donnés comme dans `recipe agent` , où il pense que je mélange du string et du int alors que pas dutout.

la seul chose qu'il fait bien est le root agent qui délègue bien en fonction de l'instruction


## Comment utiliser le Chef Cuisinier


Pour les demandes rapides et ponctuelles, le système utilise un agent spécialisé qui répond immédiatement.

#### Enregistrer vos ingrédients

**Vous :** `J'ai des œufs, du lait, de la farine, du beurre et du sucre`

**Chef :** Enregistre les ingrédients dans l'inventaire et confirme.

Le `root_agent` délègue à `inventory_agent` qui stocke les ingrédients avec `output_key="user_ingredients"` (pour le state partagé).


#### Chercher une recette spécifique

**Vous :** `Trouve-moi une recette avec des œufs et de la farine`

**Chef :** Propose plusieurs recettes compatibles :
- Recettes 100% réalisables (tous les ingrédients disponibles)
- Recettes presque possibles (1-2 ingrédients manquants)
- Recettes inspirantes (pour planifier vos courses)

Le `root_agent` délègue à `recipe_agent` qui utilise le tool `search_recipes_by_ingredients()`.


#### Obtenir les instructions d'une recette

**Vous :** `Comment faire des crêpes ?`

**Chef :** Donne les instructions détaillées, le temps de préparation, la difficulté et les ingrédients nécessaires.

Le `root_agent` délègue à `cooking_instructions_agent` qui utilise le tool `get_recipe_instructions()`.

---

#### Demander une substitution

**Vous :** `Je n'ai pas de beurre, par quoi je peux le remplacer ?`

**Chef :** Suggère des alternatives (huile, margarine) avec des conseils d'utilisation.

Le `recipe_agent` ou `cooking_instructions_agent` utilise le tool `suggest_substitution()`.

---

#### Faire une liste de courses

**Vous :** `De quoi j'ai besoin pour faire des crêpes ?`

**Chef :** Génère la liste des ingrédients manquants à acheter.

L'agent utilise le tool `generate_shopping_list()` en comparant la recette avec votre inventaire.

---

### Workflow complet (SequentialAgent)

Pour une planification, le système enchaîne automatiquement 3 étapes.

**Vous :** `Planifie-moi une recette complète` ou `Qu'est-ce que je peux cuisiner avec ce que j'ai ?`

```
1. inventory_agent → Demande et enregistre vos ingrédients (state["user_ingredients"])
2. recipe_search_with_state → Trouve des recettes avec {user_ingredients} du state
3. cooking_with_state → Donne les instructions adaptées à aux ingredients
```

**Exemple de déroulement :**
```
Chef: "Quels ingrédients avez-vous ?"
Vous: "œufs, lait, farine"
Chef: "Voici 3 recettes possibles : Crêpes, Gaufres, Pancakes"
Vous: "Les crêpes"
Chef: "Voici les instructions pour faire des crêpes avec vos ingrédients..."
```
---

### Génération de menu complet (LoopAgent)

Pour créer un menu entrée-plat-dessert, le système génère 3 propositions en boucle.

**Vous :** `Propose-moi un menu avec des œufs et de la farine`

**Ce qui se passe :**
```
Itération 1: Génère une entrée (ex: Salade César)
Itération 2: Génère un plat principal (ex: Quiche Lorraine)
Itération 3: Génère un dessert (ex: Crêpes Suzette)
```

C'est le `menu_generator_loop` (LoopAgent, 3 itérations max) qui utilise `menu_course_agent` à chaque tour.

**Résultat :** Un menu complet avec les ingrédients demandés.

---

### Callbacks et logging

Chaque interaction est automatiquement loggée dans `logs/` :

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
pip install -r requirements.txt
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




