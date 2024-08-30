Depois de criar o setup.py, você pode instalar seu projeto em modo de edição, o que é útil durante o desenvolvimento. Para isso, navegue até a raiz do seu projeto no terminal e execute:

```python
pip install -e .
```

# Rotinas Básicas

## Cria a agenda de um novo instrutor

```sh
python scripts/create_agenda.py <name> <email>
```

Exemplo:
```sh
python scripts/create_agenda.py "Rodrigo" "email@email.com.br"
```