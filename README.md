# iut-stmalo-sae503

Application Python de gestion des citations du capitaine Haddock, utilisée dans le cadre de la SAÉ 5.03. Ce code est strictement destiné à des fins pédagogiques.


## Dev

```bash
docker compose build
docker compose watch
```

## BUILD/

Dossier pour build le projet

## haddock-api/

Template HELM

## kubernetes/

Template Kubernetes avec Kustomize

## Basic AUTH

```bash
curl -X GET http://localhost:5002/users -H "Authorization: Basic $(echo -n 'Alice:inWonderland' | base64)"
```

```bash
curl -X GET https://sae503-prod.kaze-cloud.fr/quotes -H "Authorization: Basic $(echo -n 'Alice:inWonderland' | base64)"
```

## HELM

```bash
helm install haddock-api haddock-api/ -f haddock-api/values-prod.yaml
```

