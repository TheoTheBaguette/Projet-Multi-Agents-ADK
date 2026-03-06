Pour le choix du modèle : mon pc étant très faible en terme de puissance , aucun réel modèle ne fonctionne très bien notamment en terme (plus deux de minutes à ce lancer avec des modèles 2G.B et environ 1min pour chaque échange avec les agents, il est donc inconcevable pour d'utiliser un modèle en local avec plus de puissance de calcul (testé avec 5GB , il n'a jamis répondu au bout de 20 min) , Donc utilisé une clé api gémini pour voir faire différents (et aussi que cela soit plus rapide, différents test effectué pour repérer les différentes erreur par exmple il prend à l'etre même avec ce modèle puissant le nom de l'ingredient si jamais il y a un s en plus il ne le reconnait pas comme ingrédient) , pas de boucle infinie possible avec gemini , après ce sont des test aussi si on lui proposes uniquement des ingredients qui n'ont pas de recette
néammoins je continue a utiliser le 2Gb car cela permet de comprendre les potentiel erreurs , et de faire des prompt pas forcément plus long mais plus optimisé , le modèle avait du mal avec le parralèe, de plus je pense que mon idée pour les ganet parralèle etait peut  etre confus donc je suis passé au loop avec de nouvelle idée

un loop où il va proposer un menu entier, potentiellement en avec les ingredients diposnible , probablement sdu à la puissance du modèle il hallucibe et voit mon loup comme un outil quand il essaye de se rappeler 

tester différent cas aussi pour voir comment les agnets 

il est arrivé aussi qu'il prenne mes agents parallèle pour des outils mes très rarement , il donc fallue mieux préciser le type de chaque truc

Boucle inifinie dans la recherche pour les modèle pas puissant :

Le problème est une boucle infinie : l'agent appelle l'outil, reçoit un résultat vide, et réessaie indéfiniment. Il faut que l'agent sache quand s'arrêter.
donc dans le séquentielle dans chaque agent on signale qu'on utilise l'outil une seul fois si jamais on ne trouve rien , mais il censé trouvé des recettes quand même avec un ingrédient qu'on possède hors ce n'est pass le cas donc bien préciser de donner la recette si on possède au moins un ingredient

si je lui demande de regarder les la liste des ingrédients stocké alors , qu'il est vides 


pour le même prompt il va parfois choisr parallèle ou bien le sequential