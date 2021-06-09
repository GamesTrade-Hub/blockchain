# Blockchain-coin

## Introduction

Cette blockchain est destinée à la gestion de la monnaie interne aux jeux vidéo. Chaque jeu voulant une monnaie va lancer une blockchain qui sera un fork de celle-ci.


## Lancement

Afin de lancer la blockchain facilement un docker-compose est présent.
Celui-ci contient 'blockchain' qui lance un serveur flask et fait tourner la blockchain dessus.
Il contient également "tests" qui run les tests de unittest en python

à savoir : les tests units tests sont lancés automatiquement à chaque push et pull request sur main.
