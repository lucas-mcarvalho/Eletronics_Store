# Eletronics Store Mobile

Aplicativo Ionic/Angular para acessar a Eletronics Store pelo celular.

## Rodar em desenvolvimento

```bash
npm install
npm start
```

O app espera que o backend Django esteja rodando em `http://127.0.0.1:8000`.

## Rotas usadas

- `POST /login-api/`: autentica usuario e retorna token JWT.
- `POST /cadastro-api/`: cadastra usuario e retorna token JWT.
- `GET /produtos/api/listar/`: lista produtos ativos com estoque.
- `POST /produtos/api/novo/`: cadastra produto para administradores.
- `GET /categorias/api/listar/`: lista categorias ativas.
- `POST /categorias/api/nova/`: cadastra categoria para administradores.
