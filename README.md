# Agentic SDLC Demo App

Aplicação mínima e observável usada para provar a jornada real da [Agentic SDLC Reference Architecture](https://github.com/leandrosflora/agentic-sdlc-reference-architecture) com o [runtime](https://github.com/leandrosflora/agentic-sdlc-runtime).

## Jornada demonstrada

~~~text
GitHub Issue
→ Product → Architecture → Developer
→ branch + mudança + Pull Request
→ Test → Security → Reviewer
→ aprovação humana
→ deploy demo
→ health check
→ sucesso ou rollback
~~~

Este repositório é o alvo seguro da mudança. Ele não representa um template de produção.

## API

| Endpoint | Finalidade |
|---|---|
| `/` | identificação do serviço e digest implantado |
| `/health` | sinal usado para observação e rollback |
| `/ready` | confirma que o processo iniciou |
| `/version` | expõe somente o digest do artefato |

O digest vem de `ARTIFACT_DIGEST`, ligando aprovação, release e telemetria à mesma identidade imutável.

## Executar localmente

~~~bash
python -m venv .venv
python -m pip install -e ".[dev]"
pytest
agentic-demo-app --host 127.0.0.1 --port 8000
~~~

Em outro terminal:

~~~bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
~~~

Com Docker:

~~~bash
ARTIFACT_DIGEST=sha256:local docker compose up --build
~~~

## Deploy demo e rollback

O adapter local mantém estado em `.demo/deployment.json` e inicia o serviço apenas em `127.0.0.1:8000`.

~~~bash
ARTIFACT_DIGEST=sha256:stable python ops/deploy.py deploy
curl http://127.0.0.1:8000/health

ARTIFACT_DIGEST=sha256:candidate \
  P6_DEMO_FORCE_UNHEALTHY=true python ops/deploy.py deploy

ARTIFACT_DIGEST=sha256:stable python ops/deploy.py rollback
python ops/deploy.py status
python ops/deploy.py stop
~~~

A variável `P6_DEMO_FORCE_UNHEALTHY` existe exclusivamente para exercitar o rollback automático.

## Conectar ao runtime P6

No Environment `demo` do repositório do runtime, configure:

~~~text
P6_DEPLOY_COMMAND=["python","ops/deploy.py","deploy"]
P6_ROLLBACK_COMMAND=["python","ops/deploy.py","rollback"]
P6_HEALTH_URL=http://127.0.0.1:8000/health
~~~

Para uma integração entre repositórios, o job deve fazer checkout desta aplicação antes de executar o runtime. O contrato consumível está em [`.agentic/project.json`](.agentic/project.json).

## Controles

- aplicação sem dependências de runtime;
- container executado como usuário não-root;
- comandos sem shell;
- bind local por padrão;
- health e readiness separados;
- testes para sucesso e falha observável;
- CI prova deploy, health check e rollback;
- nenhum secret ou dado de produção.

## Primeiro experimento

1. Após o merge, crie o label `agentic-sdlc`.
2. Abra uma Issue pelo template **Agentic change**.
3. Use uma mudança simples, como adicionar um campo `environment` ao endpoint `/version`.
4. O Developer Agent deve criar uma branch e um PR; não deve fazer merge.
5. Após revisão e aprovação, execute o release demo e depois um cenário de rollback.
