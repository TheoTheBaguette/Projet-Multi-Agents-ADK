"""
Script de test pour vérifier le bon fonctionnement du système
"""

# Test 1: Importation des tools
print("\n[TEST 1] Importation des tools")
try:
    from my_agent.tools import (
        search_recipes_by_ingredients,
        suggest_substitution,
        get_recipe_instructions,
        generate_shopping_list
    )
    print("OK - Tous les tools importés")
except Exception as e:
    print(f"ERREUR - {e}")
    exit(1)

# Test 2: Recherche de recettes
print("\n[TEST 2] Recherche de recettes")
ingredients = ["oeufs", "lait", "farine"]
results = search_recipes_by_ingredients(ingredients, max_missing=3)

print(f"Recettes compatibles: {len(results['perfect_match'])}")
print(f"Recettes presque possibles: {len(results['almost_match'])}")
print(f"Recettes inspirantes: {len(results['inspiration'])}")

# Test 3: Suggestions de substitution
print("\n[TEST 3] Suggestions de substitution")
test_ingredients = ["yaourt", "beurre", "oeufs"]
for ing in test_ingredients:
    result = suggest_substitution(ing)
    status = "OK" if result['possible'] else "Non disponible"
    print(f"{ing}: {status}")

# Test 4: Instructions de recette
print("\n[TEST 4] Instructions de recette")
recipe_detail = get_recipe_instructions("crepes")
if not recipe_detail.get('error'):
    print(f"OK - Recette '{recipe_detail['name']}' chargée")
    print(f"  {recipe_detail['time']} | {recipe_detail['difficulty']} | {recipe_detail['servings']} portions")
else:
    print(f"ERREUR - {recipe_detail['message']}")

# Test 5: Liste de courses
print("\n[TEST 5] Liste de courses")
shopping = generate_shopping_list("crepes", ["oeufs", "lait"])
if not shopping.get('error'):
    print(f"OK - Liste générée pour '{shopping['recipe_name']}'")
    print(f"  A acheter: {shopping['count']} ingrédients")
else:
    print(f"ERREUR - {shopping['message']}")

# Test 6: Chargement des agents
print("\n[TEST 6] Chargement des agents")
try:
    from my_agent.agent import root_agent, inventory_agent, recipe_agent, cooking_agent
    print(f"OK - {root_agent.name}")
    print(f"OK - {inventory_agent.name} (output_key: {inventory_agent.output_key})")
    print(f"OK - {recipe_agent.name}")
    print(f"OK - {cooking_agent.name}")
except Exception as e:
    print(f"ERREUR - {e}")


print("Tous les tests terminés avec succès")

