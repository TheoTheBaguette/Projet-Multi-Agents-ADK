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

root_agent = LlmAgent(
    name="root_agent",
    model=MODEL_NAME,
    instruction="""Tu es un coordinateur qui DÉLÈGUE aux agents spécialisés.

Utilise transfer_to_agent UNE SEULE FOIS pour déléguer :
- Enregistrer/consulter ingrédients → transfer_to_agent(agent_name="inventory_agent")
- Chercher recettes → transfer_to_agent(agent_name="recipe_agent")  
- Instructions pour UNE recette → transfer_to_agent(agent_name="cooking_instructions_agent")
- Planification complète A à Z → transfer_to_agent(agent_name="recipe_planning_pipeline")
- Générer menu complet → transfer_to_agent(agent_name="menu_generator_loop")

IMPORTANT :
- Si demande simple (recette OU instructions) → agent individuel
- Si demande complète (planification, workflow) → recipe_planning_pipeline
- Si demande de menu complet (workflow) → menu_generator_loop

Les agents ne sont PAS des tools
Après la délégation, ARRÊTE. Ne réponds pas directement.
""",
)


# ==============================================================================
# AGENT 2 : Inventory Agent (Gestionnaire d'Inventaire)

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


recipe_agent = LlmAgent(
    name="recipe_agent",
    model=MODEL_NAME,
    instruction="""Tu es un expert en recherche de recettes.

PROCÉDURE STRICTE (1 APPEL OUTIL MAXIMUM) :

1. Appelle search_recipes_by_ingredients() UNE SEULE FOIS avec les ingrédients
2. Une fois le résultat reçu, présente les recettes et ARRÊTE IMMÉDIATEMENT
3. N'appelle JAMAIS un outil deux fois

FORMAT DE RÉPONSE :

Si des recettes sont trouvées :
"Voici les recettes compatibles :

RECETTES 100% POSSIBLES :
- [Nom recette] ([temps], [difficulté])

RECETTES PRESQUE POSSIBLES :
- [Nom recette] - Manque : [ingrédients] ([temps], [difficulté])

RECETTES INSPIRANTES :
- [Nom recette] - Manque : [ingrédients] ([temps], [difficulté])"

Si aucune recette :
"Désolé, aucune recette trouvée avec ces ingrédients."

IMPORTANT : Après avoir présenté les recettes, STOP. N'appelle plus aucun outil.
Réponds EN FRANÇAIS uniquement.
""",
    tools=[
        search_recipes_by_ingredients,
        suggest_substitution,
        generate_shopping_list
    ],
)


# ==============================================================================
# AGENT 4 : Cooking Instructions Agent (Guide de Cuisine - Appels directs)


cooking_instructions_agent = LlmAgent(
    name="cooking_instructions_agent",
    model=MODEL_NAME,
    instruction="""Tu donnes les instructions pour préparer une recette.

ÉTAPES :
1. Appelle get_recipe_instructions UNE SEULE FOIS
2. Si erreur : dis "Recette non trouvée" et ARRÊTE
3. Si succès : présente ingrédients + étapes puis ARRÊTE

NE rappelle JAMAIS appeler l'outil deux fois. Réponds EN FRANÇAIS.
""",
    tools=[
        get_recipe_instructions,
        suggest_substitution
    ],
)


# ==============================================================================
# AGENT 5 : Cooking With State (Guide de Cuisine - UNIQUEMENT pour Sequential)


cooking_with_state = LlmAgent(
    name="cooking_with_state",
    model=MODEL_NAME,
    instruction="""Tu donnes les instructions de cuisine en tenant compte des ingrédients disponibles.

INGRÉDIENTS DISPONIBLES (récupérés du state partagé) : {user_ingredients}

ÉTAPES :
1. Appelle get_recipe_instructions UNE SEULE FOIS
2. Si erreur : dis "Recette non trouvée" et ARRÊTE
3. Si succès : présente les instructions ET mentionne si certains ingrédients manquent
4. Si ingrédients manquants : propose des substitutions depuis la liste disponible

NE rappelle JAMAIS appeler l'outil deux fois. Réponds EN FRANÇAIS.
""",
    tools=[
        get_recipe_instructions,
        suggest_substitution
    ],
)


# ==============================================================================
# AGENT 5 : Recipe Search With State (UNIQUEMENT pour SequentialAgent)


recipe_search_with_state = LlmAgent(
    name="recipe_search_with_state",
    model=MODEL_NAME,
    instruction="""Tu cherches des recettes en utilisant les ingrédients sauvegardés en mémoire.

INGRÉDIENTS DISPONIBLES (du state partagé) : {user_ingredients}

PROCÉDURE STRICTE (1 APPEL OUTIL MAXIMUM) :

1. Appelle search_recipes_by_ingredients() UNE SEULE FOIS avec les ingrédients du state
2. Une fois le résultat reçu, présente les recettes et ARRÊTE IMMÉDIATEMENT
3. N'appelle JAMAIS un outil deux fois

FORMAT DE RÉPONSE :

Si des recettes sont trouvées :
"Voici les recettes compatibles avec vos ingrédients :

RECETTES 100% POSSIBLES :
- [Nom recette] ([temps], [difficulté])

RECETTES PRESQUE POSSIBLES :
- [Nom recette] - Manque : [ingrédients] ([temps], [difficulté])

RECETTES INSPIRANTES :
- [Nom recette] - Manque : [ingrédients] ([temps], [difficulté])"

Si aucune recette :
"Désolé, aucune recette trouvée avec ces ingrédients."

IMPORTANT : Après avoir présenté les recettes, STOP. N'appelle plus aucun outil.
Réponds EN FRANÇAIS uniquement.
""",
    tools=[
        search_recipes_by_ingredients,
        suggest_substitution,
        generate_shopping_list
    ],
)


# ==============================================================================
# WORKFLOW AGENT 1 : SequentialAgent (Pipeline de préparation)

recipe_planning_pipeline = SequentialAgent(
    name="recipe_planning_pipeline",
    description="Pipeline pour planifier une recette de A à Z ",
    sub_agents=[
        inventory_agent,           # Sauvegarde user_ingredients dans le STATE
        recipe_search_with_state,  # Utilise le template {user_ingredients}
        cooking_with_state         # Utilise le template {user_ingredients}
    ],
 
)


# ==============================================================================
# WORKFLOW AGENT 2 : LoopAgent (Générateur de Menu Complet)

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
# CONFIGURATION DES DÉLÉGATIONS

# Mise à jour du root_agent avec les sub_agents
root_agent.sub_agents = [
    # Agents individuels (appelables directement)
    inventory_agent,                   
    recipe_agent,                      
    cooking_instructions_agent,       
    
    # Workflows
    recipe_planning_pipeline,          
    menu_generator_loop,               
]


from .logging_config import agent_logger
from datetime import datetime


def on_agent_start_callback(**kwargs) -> None:
    """
    Callback appelé AVANT qu'un agent commence à traiter une requête.
    
    """
    try:
        # ADK passe les infos via callback_context
        agent_name = "unknown_agent"
        message = ""
        
        if 'callback_context' in kwargs:
            context = kwargs['callback_context']
            
            # Récupérer le nom de l'agent (attribut direct)
            if hasattr(context, 'agent_name'):
                agent_name = context.agent_name
                print(f"[DEBUG] Agent name: {agent_name}")
            
            # Récupérer le message utilisateur
            if hasattr(context, 'user_content'):
                user_content = context.user_content
                print(f"[DEBUG] user_content type: {type(user_content)}")
                
                # user_content peut être un objet Content avec parts
                if hasattr(user_content, 'parts'):
                    if user_content.parts and len(user_content.parts) > 0:
                        if hasattr(user_content.parts[0], 'text'):
                            message = user_content.parts[0].text
                            print(f"[DEBUG] Message: {message[:50]}...")
                # Ou une simple string
                elif isinstance(user_content, str):
                    message = user_content
                    print(f"[DEBUG] Message (str): {message[:50]}...")
        
        # Log structuré
        agent_logger.log_agent_start(agent_name, message)
        
    except Exception as e:
        # Ne pas crasher si le logging échoue
        print(f"[Erreur callback agent_start] {e}")
        import traceback
        traceback.print_exc()


def on_tool_execution_callback(**kwargs) -> None:
    """
    Callback appelé APRÈS qu'un outil a été exécuté.
    
    """
    try:
        # DEBUG: Afficher tous les kwargs pour comprendre la structure
        print(f"\n[DEBUG on_tool_execution_callback] kwargs keys: {kwargs.keys()}")
        
        # ADK passe les infos via callback_context
        tool_name = "unknown_tool"
        tool_args = {}
        result = ""
        duration = 0
        
        if 'callback_context' in kwargs:
            context = kwargs['callback_context']
            print(f"[DEBUG] callback_context attributes: {[attr for attr in dir(context) if not attr.startswith('_')]}")
            
            # Explorer les attributs disponibles
            if hasattr(context, 'function_call_id'):
                print(f"[DEBUG] function_call_id: {context.function_call_id}")
            
            if hasattr(context, 'actions'):
                actions = context.actions
                print(f"[DEBUG] actions type: {type(actions)}")
                if actions:
                    print(f"[DEBUG] actions content: {actions}")
                    # Les actions peuvent contenir des infos sur les tools
                    if isinstance(actions, list) and len(actions) > 0:
                        action = actions[-1]
                        print(f"[DEBUG] last action: {action}")
                        if hasattr(action, 'tool_name'):
                            tool_name = action.tool_name
                        if hasattr(action, 'tool_input'):
                            tool_args = action.tool_input
                        if hasattr(action, 'tool_output'):
                            result = action.tool_output
            
            # Autre possibilité: regarder dans state ou event_actions
            if hasattr(context, '_event_actions'):
                print(f"[DEBUG] _event_actions: {context._event_actions}")
            
            print(f"[DEBUG] Tool name: {tool_name}")
            print(f"[DEBUG] Tool args: {str(tool_args)[:100]}")
            print(f"[DEBUG] Result preview: {str(result)[:100]}")
        
        # Log structuré
        agent_logger.log_tool_execution(
            tool_name=tool_name,
            args=tool_args,
            result=str(result),
            duration=duration
        )
        
    except Exception as e:
        # Ne pas crasher si le logging échoue
        print(f"[Erreur callback tool_execution] {e}")
        import traceback
        traceback.print_exc()



# Application des callbacks aux agents principaux

recipe_agent.before_agent_callback = on_agent_start_callback
recipe_agent.after_tool_callback = on_tool_execution_callback

recipe_search_with_state.before_agent_callback = on_agent_start_callback
recipe_search_with_state.after_tool_callback = on_tool_execution_callback

cooking_instructions_agent.before_agent_callback = on_agent_start_callback
cooking_instructions_agent.after_tool_callback = on_tool_execution_callback

cooking_with_state.before_agent_callback = on_agent_start_callback
cooking_with_state.after_tool_callback = on_tool_execution_callback