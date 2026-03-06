"""
Système Multi-Agents : Chef Cuisinier Virtuel
==============================================

Ce système permet de :
- Gérer un inventaire d'ingrédients
- Trouver des recettes compatibles
- Guider l'utilisateur dans la préparation

Architecture : 4 agents spécialisés qui collaborent
- root_agent : Coordinateur principal (obligatoire dans ADK)
- inventory_agent : Gestion des ingrédients
- recipe_agent : Expert en recettes
- cooking_agent : Guide de cuisine

IMPORTANT pour la démo :
- Chaque agent a un RÔLE précis (specialisation)
- Les agents communiquent via STATE partagé
- Ils utilisent les TOOLS créés précédemment
"""

from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from .tools import (
    search_recipes_by_ingredients,
    suggest_substitution,
    get_recipe_instructions,
    generate_shopping_list
)
import os

# Charge le modèle depuis le fichier .env
# ADK lit automatiquement ADK_MODEL_NAME et ADK_MODEL_PROVIDER
PROVIDER = os.getenv("ADK_MODEL_PROVIDER", "ollama")
MODEL = os.getenv("ADK_MODEL_NAME", "llama3.2:latest")

# Construction du nom complet selon le provider
if PROVIDER == "ollama":
    MODEL_NAME = f"ollama/{MODEL}"
elif PROVIDER == "google":
    MODEL_NAME = MODEL  # Pour Google, on utilise directement le nom du modèle (ex: gemini-1.5-flash)
else:
    MODEL_NAME = f"{PROVIDER}/{MODEL}"


# ==============================================================================
# AGENT 1 : Root Agent (Coordinateur Principal)

# Rôle : C'est le "chef d'orchestre" qui accueille l'utilisateur et délègue
#        aux bons agents spécialisés selon la demande
# ==============================================================================

root_agent = LlmAgent(
    name="root_agent",
    model=MODEL_NAME,
    instruction="""Tu es un coordinateur qui DÉLÈGUE aux agents spécialisés.

Utilise transfer_to_agent UNE SEULE FOIS pour déléguer :
- Ingrédients → transfer_to_agent(agent_name="inventory_agent")
- Recettes → transfer_to_agent(agent_name="recipe_agent")  
- Instructions cuisine → transfer_to_agent(agent_name="cooking_agent")
- Planification complète → transfer_to_agent(agent_name="recipe_planning_pipeline")
- Menu complet → transfer_to_agent(agent_name="menu_generator_loop")
- Vérification inventaire → transfer_to_agent(agent_name="inventory_validator_loop")

Après la délégation, ARRÊTE. Ne réponds pas directement.
""",
)


# ==============================================================================
# AGENT 2 : Inventory Agent (Gestionnaire d'Inventaire)
# ==============================================================================
# Rôle : Garde en mémoire les ingrédients disponibles et aide à la planification
# ==============================================================================

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=MODEL_NAME,
    instruction="""Tu gères les ingrédients de l'utilisateur.

Quand l'utilisateur donne des ingrédients :
1. Liste-les clairement
2. Confirme l'enregistrement

Exemple :
User: "J'ai des œufs, lait, farine"
Toi: "Ingrédients enregistrés : œufs, lait, farine. ✓"

Réponds EN FRANÇAIS uniquement.
""",
    # Cet agent SAUVEGARDE les données pour les autres agents
    output_key="user_ingredients",  # ← IMPORTANT : State partagé !
)


# ==============================================================================
# AGENT 3 : Recipe Agent (Expert en Recettes)
# ==============================================================================
# Rôle : Trouve des recettes compatibles avec les ingrédients disponibles
# Tools : Utilise search_recipes_by_ingredients, suggest_substitution
# ==============================================================================

recipe_agent = LlmAgent(
    name="recipe_agent",
    model=MODEL_NAME,
    instruction="""Tu cherches des recettes avec les ingrédients de l'utilisateur.

ÉTAPES :
1. Appelle search_recipes_by_ingredients UNE SEULE FOIS
2. Si résultats vides : dis "Désolé, aucune recette avec ces ingrédients" et ARRÊTE
3. Si résultats trouvés : présente les recettes par catégorie puis ARRÊTE

les catégories sont :
- RECETTES 100% possibles
- RECETTES presque possibles (manque 1 ou 2 ingrédients)
- RECETTES inspirantes (beaucoup d'ingrédients manquants mais on possède au moins 1 ingrédient clé)

NE rappelle JAMAIS l'outil deux fois. Réponds EN FRANÇAIS.
""",
    tools=[
        search_recipes_by_ingredients,
        suggest_substitution,
        generate_shopping_list
    ],
)


# ==============================================================================
# AGENT 4 : Cooking Agent (Guide de Cuisine)
# ==============================================================================
# Rôle : Donne les instructions étape par étape pour préparer une recette
# Tools : Utilise get_recipe_instructions
# ==============================================================================

cooking_agent = LlmAgent(
    name="cooking_agent",
    model=MODEL_NAME,
    instruction="""Tu donnes les instructions de cuisine.

ÉTAPES :
1. Appelle get_recipe_instructions UNE SEULE FOIS
2. Si erreur : dis "Recette non trouvée" et ARRÊTE
3. Si succès : présente ingrédients + étapes puis ARRÊTE

NE rappelle JAMAIS l'outil deux fois. Réponds EN FRANÇAIS.
""",
    tools=[
        get_recipe_instructions,
        suggest_substitution
    ],
)





# ==============================================================================
# WORKFLOW AGENT 1 : SequentialAgent (Pipeline de préparation)
# ==============================================================================
# Rôle : Enchaîne plusieurs agents dans un ordre précis
# Use case : Planification complète d'une recette
# DÉMONTRE : STATE PARTAGÉ (Contrainte 4 du TP)
# ==============================================================================

recipe_planning_pipeline = SequentialAgent(
    name="recipe_planning_pipeline",
    description="Pipeline pour planifier une recette de A à Z",
    # Ce workflow enchaîne les agents dans cet ordre :
    # 1. inventory_agent : Sauvegarde les ingrédients avec output_key="user_ingredients"
    # 2. recipe_agent : Trouve des recettes (peut accéder au state partagé)
    # 3. cooking_agent : Donne les instructions de préparation
    sub_agents=[
        inventory_agent,    # Sauvegarde user_ingredients dans le STATE
        recipe_agent,       # Accède au STATE partagé
        cooking_agent       # Accède au STATE partagé
    ],
    # IMPORTANT : SequentialAgent = tous les agents partagent le MÊME state
    # C'est la DÉMONSTRATION du STATE PARTAGÉ (Contrainte 4 du TP) !
)


# ==============================================================================
# WORKFLOW AGENT 2 : LoopAgent (Générateur de Menu Complet)
# ==============================================================================
# Rôle : Exécute un agent EN BOUCLE pour créer un menu complet
# Use case : Générer Entrée → Plat principal → Dessert (3 plats différents)
# ==============================================================================

# Agent qui sera exécuté en boucle pour chaque type de plat
menu_course_agent = LlmAgent(
    name="menu_course_agent",
    model=MODEL_NAME,
    instruction="""Tu génères des suggestions de plats pour composer un menu.

Si l'utilisateur a mentionné des ingrédients : utilise-les pour personnaliser le menu.
Sinon : propose des recettes inspirantes générales.

PROCESSUS :
1. À chaque itération, propose UN type de plat différent :
   - Itération 1 : ENTRÉE → utilise category="entrée" dans search_recipes_by_ingredients
   - Itération 2 : PLAT PRINCIPAL → utilise category="plat" dans search_recipes_by_ingredients
   - Itération 3 : DESSERT → utilise category="dessert" dans search_recipes_by_ingredients

2. Pour chaque catégorie :
   - Appelle search_recipes_by_ingredients avec le paramètre category approprié
   - Si user a mentionné des ingrédients : extrais-les et passe-les au tool
   - Sinon : passe une liste vide [] pour avoir des suggestions inspirantes

3. Choisis la meilleure recette et présente :
   - Type de plat (Entrée/Plat/Dessert)
   - Nom de la recette
   - Temps de préparation
   - Difficulté

4. ARRÊTE après avoir suggéré UN plat

FORMAT DE RÉPONSE :
"[Type] : [Nom] - [Temps] - [Difficulté]"

Exemples :
"Entrée : Salade composée - 10min - Facile"
"Plat : Quiche Lorraine - 45min - Moyen"
"Dessert : Crêpes - 20min - Facile"

IMPORTANT : 
- Appelle l'outil UNE SEULE FOIS avec le bon paramètre category
- Ne génère qu'UNE suggestion puis STOP
- Ne boucle pas sur plusieurs catégories toi-même (le LoopAgent s'en charge)""",
    tools=[search_recipes_by_ingredients],
)

# LoopAgent qui génère un menu complet en 3 itérations
menu_generator_loop = LoopAgent(
    name="menu_generator_loop",
    description="Génère un menu complet selon les ingrédients disponibles : Entrée → Plat → Dessert",
    sub_agents=[menu_course_agent],  # Liste avec UN agent qui sera répété
    max_iterations=3,  # 3 itérations = entrée + plat + dessert
)


# ==============================================================================
# WORKFLOW AGENT 3 : LoopAgent (Validateur d'Inventaire Interactif)
# ==============================================================================
# Rôle : Exécute un agent EN BOUCLE pour vérifier chaque ingrédient un par un
# Use case : Valider si l'utilisateur possède tous les ingrédients d'une recette
# ==============================================================================

# Agent qui vérifie UN ingrédient à la fois
ingredient_checker_agent = LlmAgent(
    name="ingredient_checker_agent",
    model=MODEL_NAME,
    instruction="""Tu vérifies si l'utilisateur possède UN ingrédient.

PROCESSUS SIMPLE :
1. Demande "As-tu [ingrédient] ?"
2. Attends la réponse (oui/non)
3. Note : si oui, si non
4. STOP - passe au suivant

Sois bref : "As-tu des œufs ? " puis ARRÊTE.""",
)

# LoopAgent qui vérifie plusieurs ingrédients
inventory_validator_loop = LoopAgent(
    name="inventory_validator_loop",
    description="Valide l'inventaire en vérifiant chaque ingrédient un par un",
    sub_agents=[ingredient_checker_agent],  # Agent répété en boucle
    max_iterations=5,  # Maximum 5 ingrédients à vérifier
    # IMPORTANT : Cas d'usage très clair et utile !
    # User : "Vérifie si j'ai tout pour faire des crêpes"
    # Itération 1 : "As-tu des œufs ?" → Vérifie
    # Itération 2 : "As-tu du lait ?" → Vérifie
    # Itération 3 : "As-tu de la farine ?" → Vérifie
    # → Inventaire validé ingrédient par ingrédient
)


# ==============================================================================
# CONFIGURATION DES DÉLÉGATIONS
# ==============================================================================
# Maintenant que tous les agents sont définis, configurons le root_agent
# pour qu'il puisse DÉLÉGUER aux agents spécialisés
# ==============================================================================

# Mise à jour du root_agent avec les sub_agents
root_agent.sub_agents = [
    inventory_agent,
    recipe_agent,
    cooking_agent,
    recipe_planning_pipeline,    # Workflow séquentiel
    menu_generator_loop,          # Workflow en boucle #1 : Menu
    inventory_validator_loop      # Workflow en boucle #2 : Validation
]

# EXPLICATION pour la démo :
# Avec sub_agents configuré, le root_agent peut maintenant :
# 1. TRANSFER TO AGENT : Déléguer complètement à un agent spécialisé
#    Exemple : "Trouve-moi une recette" → root transfère à recipe_agent
#    L'utilisateur interagit alors DIRECTEMENT avec recipe_agent
#
# 2. AGENT TOOL : Invoquer un agent comme un outil (on configurera ça plus tard)
#    L'agent est appelé en arrière-plan et retourne un résultat


# ==============================================================================
# CALLBACKS (Minimum 2 types différents requis par le TP)
# ==============================================================================
# Les callbacks permettent d'exécuter du code à des moments précis :
# - before_agent_callback : Avant qu'un agent commence
# - after_agent_callback : Après qu'un agent termine
# - before_tool_callback : Avant qu'un outil soit appelé
# - after_tool_callback : Après qu'un outil soit appelé
# - on_model_error_callback : En cas d'erreur du modèle
# - on_tool_error_callback : En cas d'erreur d'un outil
# ==============================================================================

def on_agent_start_callback(**kwargs) -> None:
    #Callback appelé AVANT qu'un agent commence à traiter une requête

    print("\nAgent démarré...")

    

def on_tool_execution_callback(**kwargs) -> None:
    
    #Callback appelé APRÈS qu'un outil a été exécuté
    print("\n Outil exécuté")



# Application des callbacks aux agents principaux
# Note : On applique les callbacks aux agents qui font le plus de travail
# Les callbacks sont simplifiés pour éviter les erreurs d'accès aux attributs Context

recipe_agent.before_agent_callback = on_agent_start_callback

recipe_agent.after_tool_callback = on_tool_execution_callback

cooking_agent.before_agent_callback = on_agent_start_callback

cooking_agent.after_tool_callback = on_tool_execution_callback