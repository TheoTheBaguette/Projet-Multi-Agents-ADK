from typing import Optional
from ..recipes_db import RECIPES_DB, SUBSTITUTIONS, get_all_recipes


def search_recipes_by_ingredients(
    ingredients: list[str],
    max_missing: int = 3,
    category: Optional[str] = None
) -> dict:
    """
    Recherche des recettes compatibles avec les ingrédients disponibles.
    
    Ce tool est le COEUR du système. Il analyse toutes les recettes et les classe
    en 3 catégories selon le nombre d'ingrédients manquants.
    
    Args:
        ingredients: Liste des ingrédients que l'utilisateur possède (ex: ["oeufs", "lait"])
        max_missing: Nombre maximum d'ingrédients manquants à accepter (par défaut 3)
        category: Filtrer par catégorie optionnelle (ex: "dessert", "plat")
    
    Returns:
        Dictionnaire avec 3 listes de recettes :
        - perfect_match: Recettes 100% réalisables (0 ingrédient manquant)
        - almost_match: Recettes presque possibles (1-2 manquants)
        - inspiration: Recettes inspirantes (3+ manquants)
        
    Example:
        >>> search_recipes_by_ingredients(["oeufs", "lait", "farine"])
        {
            "perfect_match": [...],
            "almost_match": [...],
            "inspiration": [...]
        }
    """
    # Normaliser les ingrédients (minuscules, sans espaces)
    ingredients_norm = [ing.lower().strip() for ing in ingredients]
    
    # Structures pour stocker les résultats
    results = {
        "perfect_match": [],      # 100% compatible
        "almost_match": [],       # 1-2 manquants
        "inspiration": []         # 3+ manquants
    }
    
    # Parcourir toutes les recettes de la base de données
    for recipe_id, recipe in RECIPES_DB.items():
        # Filtrer par catégorie si demandé
        if category and recipe.get("category") != category:
            continue
        
        # Calculer les ingrédients manquants
        missing = [
            ing for ing in recipe["ingredients"] 
            if ing.lower() not in ingredients_norm
        ]
        
        # Calculer le score de compatibilité (pourcentage d'ingrédients possédés)
        total_ingredients = len(recipe["ingredients"])
        available_count = total_ingredients - len(missing)
        compatibility_score = (available_count / total_ingredients) * 100
        
        # Préparer les informations de la recette
        recipe_info = {
            "id": recipe_id,
            "name": recipe["name"],
            "missing_ingredients": missing,
            "missing_count": len(missing),
            "compatibility": f"{compatibility_score:.0f}%",
            "time": recipe["time"],
            "difficulty": recipe["difficulty"],
            "servings": recipe["servings"],
            "category": recipe["category"]
        }
        
        # Classer la recette selon le nombre d'ingrédients manquants
        if len(missing) == 0:
            results["perfect_match"].append(recipe_info)
        elif len(missing) <= 2:
            results["almost_match"].append(recipe_info)
        elif len(missing) <= max_missing:
            results["inspiration"].append(recipe_info)
    
    # Trier chaque catégorie par compatibilité décroissante
    for category_key in results:
        results[category_key].sort(
            key=lambda x: x["compatibility"], 
            reverse=True
        )
    
    return results


def suggest_substitution(
    missing_ingredient: str,
    context: str = "general"
) -> dict:
    """
    Suggère des substitutions pour un ingrédient manquant.
    
    Ce tool aide l'utilisateur à improviser quand il manque un ingrédient.
    Il utilise le dictionnaire SUBSTITUTIONS et donne des conseils d'utilisation.
    
    Args:
        missing_ingredient: L'ingrédient qui manque
        context: Contexte d'utilisation ("patisserie", "cuisine", "general")
    
    Returns:
        Dictionnaire contenant :
        - possible: bool - Si une substitution existe
        - substitutes: list - Liste des alternatives
        - advice: str - Conseil d'utilisation
        
    Example:
        >>> suggest_substitution("yaourt")
        {
            "possible": True,
            "substitutes": ["lait + citron", "creme_fraiche"],
            "advice": "Le lait + citron donne une acidité similaire au yaourt."
        }
    """
    # Normaliser l'ingrédient
    ingredient_norm = missing_ingredient.lower().strip()
    
    # Chercher dans le dictionnaire de substitutions
    if ingredient_norm in SUBSTITUTIONS:
        substitutes = SUBSTITUTIONS[ingredient_norm]
        
        # Créer un conseil personnalisé selon l'ingrédient
        advice_map = {
            "yaourt": "Le lait + citron donne une acidité similaire au yaourt.",
            "beurre": "L'huile fonctionne bien mais change légèrement la texture.",
            "creme": "Le lait + beurre est une bonne alternative pour les sauces.",
            "oeufs": "Pour la pâtisserie uniquement ! Banane = moelleux, compote = légèreté.",
            "lait": "Le lait végétal fonctionne dans presque toutes les recettes.",
            "levure": "Le bicarbonate + citron fait aussi lever la pâte.",
            "sucre": "Attention : le miel et sirop sont plus sucrés, réduire les quantités."
        }
        
        return {
            "possible": True,
            "ingredient": missing_ingredient,
            "substitutes": substitutes,
            "advice": advice_map.get(ingredient_norm, "Utilisez avec précaution.")
        }
    else:
        return {
            "possible": False,
            "ingredient": missing_ingredient,
            "substitutes": [],
            "advice": f"Pas de substitution connue pour {missing_ingredient}. Il est essentiel à la recette."
        }


def get_recipe_instructions(recipe_id: str) -> dict:
    """
    Récupère les instructions détaillées d'une recette spécifique.
    
    Ce tool est appelé quand l'utilisateur a choisi une recette et veut
    savoir comment la préparer étape par étape.
    
    Args:
        recipe_id: Identifiant de la recette (ex: "crepes", "omelette")
    
    Returns:
        Dictionnaire contenant toutes les infos de la recette :
        - name: Nom de la recette
        - ingredients: Liste complète des ingrédients
        - instructions: Liste des étapes numérotées
        - time: Temps de préparation
        - difficulty: Niveau de difficulté
        - servings: Nombre de portions
        
    Example:
        >>> get_recipe_instructions("crepes")
        {
            "name": "Crêpes",
            "ingredients": ["oeufs", "lait", ...],
            "instructions": ["1. Mélanger...", "2. Faire..."],
            ...
        }
    """
    # Vérifier si la recette existe
    if recipe_id not in RECIPES_DB:
        return {
            "error": True,
            "message": f"Recette '{recipe_id}' non trouvée dans la base de données.",
            "available_recipes": list(RECIPES_DB.keys())
        }
    
    # Récupérer la recette
    recipe = RECIPES_DB[recipe_id]
    
    # Formater les instructions avec des numéros
    instructions_formatted = [
        f"{i+1}. {step}" 
        for i, step in enumerate(recipe["instructions"])
    ]
    
    return {
        "error": False,
        "id": recipe_id,
        "name": recipe["name"],
        "ingredients": recipe["ingredients"],
        "instructions": instructions_formatted,
        "time": recipe["time"],
        "difficulty": recipe["difficulty"],
        "servings": recipe["servings"],
        "category": recipe["category"]
    }


def generate_shopping_list(
    recipe_id: str,
    available_ingredients: list[str]
) -> dict:
    """
    Génère une liste de courses pour une recette donnée.
    
    Ce tool compare les ingrédients nécessaires avec ceux disponibles
    et crée une liste de ce qu'il faut acheter.
    
    Args:
        recipe_id: Identifiant de la recette voulue
        available_ingredients: Liste des ingrédients déjà possédés
    
    Returns:
        Dictionnaire contenant :
        - recipe_name: Nom de la recette
        - to_buy: Liste des ingrédients à acheter
        - already_have: Liste des ingrédients déjà possédés
        - count: Nombre d'articles à acheter
        
    Example:
        >>> generate_shopping_list("crepes", ["oeufs", "lait"])
        {
            "recipe_name": "Crêpes",
            "to_buy": ["farine", "beurre", "sucre", "sel"],
            "already_have": ["oeufs", "lait"],
            "count": 4
        }
    """
    # Vérifier si la recette existe
    if recipe_id not in RECIPES_DB:
        return {
            "error": True,
            "message": f"Recette '{recipe_id}' non trouvée."
        }
    
    recipe = RECIPES_DB[recipe_id]
    
    # Normaliser les ingrédients disponibles
    available_norm = [ing.lower().strip() for ing in available_ingredients]
    
    # Séparer ce qui est disponible et ce qui manque
    to_buy = []
    already_have = []
    
    for ingredient in recipe["ingredients"]:
        if ingredient.lower() in available_norm:
            already_have.append(ingredient)
        else:
            to_buy.append(ingredient)
    
    return {
        "error": False,
        "recipe_name": recipe["name"],
        "recipe_id": recipe_id,
        "to_buy": to_buy,
        "already_have": already_have,
        "count": len(to_buy),
        "message": f"Il te faut acheter {len(to_buy)} ingrédient(s) pour faire {recipe['name']}."
    }
