"""
Base de données des recettes
============================

Ce fichier contient toutes les recettes disponibles dans notre système.
Chaque recette a :
- name : Nom de la recette
- ingredients : Liste des ingrédients nécessaires
- time : Temps de préparation
- difficulty : Niveau de difficulté (facile/moyen/difficile)
- servings : Nombre de portions
- instructions : Étapes de préparation
- category : Type de plat (dessert, plat principal, etc.)
"""

# Base de données simple : dictionnaire Python
RECIPES_DB = {
    "crepes": {
        "name": "Crêpes",
        "ingredients": ["oeufs", "lait", "farine"],
        "time": "20 min",
        "difficulty": "facile",
        "servings": 4,
        "category": "dessert",
        "instructions": [
            "Mélanger farine, œufs et lait",
            "Laisser reposer 10 min",
            "Cuire dans une poêle chaude"
        ]
    },
    
    "omelette": {
        "name": "Omelette",
        "ingredients": ["oeufs", "sel"],
        "time": "5 min",
        "difficulty": "facile",
        "servings": 2,
        "category": "plat",
        "instructions": [
            "Battre les œufs avec sel",
            "Cuire dans une poêle",
            "Plier en deux"
        ]
    },
    
    "pancakes": {
        "name": "Pancakes",
        "ingredients": ["oeufs", "lait", "farine", "sucre"],
        "time": "15 min",
        "difficulty": "facile",
        "servings": 4,
        "category": "dessert",
        "instructions": [
            "Mélanger tous les ingrédients",
            "Faire des petites crêpes épaisses",
            "Cuire 2 min chaque côté"
        ]
    },
    
    "cookies": {
        "name": "Cookies",
        "ingredients": ["farine", "sucre", "oeufs", "chocolat"],
        "time": "25 min",
        "difficulty": "facile",
        "servings": 12,
        "category": "dessert",
        "instructions": [
            "Mélanger tous les ingrédients",
            "Former des boules sur une plaque",
            "Cuire 12 min à 180°C"
        ]
    },

    "quiche": {
        "name": "Quiche Lorraine",
        "ingredients": ["pâte ", "lardons", "oeufs", "crème"],
        "time": "45 min",
        "difficulty": "moyen",
        "servings": 6,
        "category": "plat",
        "instructions": [
            "Étaler la pâte dans un moule",
            "Faire revenir les lardons",
            "Mélanger œufs et crème",
            "Ajouter les lardons et verser sur la pâte",
            "Cuire 30 min à 180°C"
        ]
    },

    "salade": {
        "name": "Salade composée",
        "ingredients": ["laitue", "tomate", "concombre", "vinaigrette"],
        "time": "10 min",
        "difficulty": "facile",
        "servings": 2,
        "category": "entrée",
        "instructions": [
            "Laver et couper les légumes",
            "Mélanger dans un saladier",
            "Ajouter la vinaigrette"
        ]

    

    },

    "Foccacia": {
        "name": "Focaccia",
        "ingredients": ["farine", "eau", "levure", "sel", "huile d'olive"],
        "time": "2h (dont 1h de repos)",
        "difficulty": "moyen",
        "servings": 4,
        "category": "entrée",
        "instructions": [
            "Mélanger farine, eau, levure, sel et huile",
            "Pétrir la pâte et laisser reposer 1h",
            "Étaler la pâte sur une plaque huilée",
            "Laisser reposer 30 min",
            "Cuire 20 min à 220°C"
        ]

    },

    "Riz au lait": {
        "name": "Riz au lait",
        "ingredients": ["riz", "lait", "sucre", "vanille"],
        "time": "40 min",
        "difficulty": "facile",
        "servings": 4,
        "category": "dessert",
        "instructions": [
            "Faire chauffer le lait avec la vanille",
            "Ajouter le riz et cuire à feu doux 30 min",
            "Ajouter le sucre en fin de cuisson"
        ]
    },



}
     



# Dictionnaire de substitutions possibles
SUBSTITUTIONS = {
    "lait": ["eau"],
    "oeufs": ["banane"],
    "sucre": ["miel"],
    "farine": ["fecule"]
}


def get_all_recipes() -> dict:
    return RECIPES_DB


def get_recipe_by_name(recipe_id: str) -> dict:
    return RECIPES_DB.get(recipe_id)


def get_all_ingredients() -> list[str]:
    all_ingredients = set()
    for recipe in RECIPES_DB.values():
        all_ingredients.update(recipe["ingredients"])
    return sorted(list(all_ingredients))

