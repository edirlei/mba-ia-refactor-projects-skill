# Task Manager API

API Flask organizada em camadas MVC para usuários, tarefas, categorias e relatórios.

## Arquitetura

```text
HTTP -> routes -> controllers -> services -> repositories -> models -> SQLite
          |                         |
          +-> schemas              +-> regras e transações
```

- `app.py`: application factory e composition root.
- `config/`: configuração validada a partir do ambiente.
- `routes/`: fronteira HTTP e códigos de resposta.
- `controllers/`: coordenação dos casos de uso.
- `services/`: autenticação, autorização e regras de negócio.
- `repositories/`: consultas ORM, paginação e agregações.
- `models/`: entidades e serializers públicos seguros.
- `schemas/`: validação central com Marshmallow.
- `middlewares/`: autenticação e tratamento central de erros.
- `tests/`: contratos, segurança, arquitetura e smoke HTTP.

## Configuração

No PowerShell, prepare o ambiente virtual e a configuração:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o valor aleatório para `SECRET_KEY` no `.env`. Preencha também as três variáveis `SEED_*_PASSWORD` com senhas distintas de pelo menos 12 caracteres. O arquivo `.env` é ignorado pelo Git.

Depois inicialize os dados e execute a API:

```powershell
python seed.py
python app.py
```

A configuração padrão usa `http://127.0.0.1:5000`. Debug e CORS ficam desabilitados até serem configurados explicitamente.

## Autenticação

`POST /login` retorna um token assinado e temporário. Envie-o nas rotas protegidas:

```http
Authorization: Bearer <token>
```

O cadastro público sempre cria papel `user`. Operações administrativas exigem `admin`; relatórios gerais e categorias aceitam `admin` ou `manager`. Usuários comuns acessam somente a própria conta e as próprias tarefas.

## Paginação

Listagens aceitam `page` e `per_page`. O limite máximo padrão é 100 e pode ser ajustado por configuração sem alterar o formato de resposta, que continua sendo uma lista JSON.

## Testes

```powershell
python -m unittest discover -s tests -v
python -m tests.smoke_http
```

O primeiro comando cobre contratos, segurança e arquitetura em banco isolado. O segundo inicia um servidor temporário e executa os 22 endpoints originais por HTTP real.
