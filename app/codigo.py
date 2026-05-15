import secrets
import string

ALFABETO = string.ascii_letters + string.digits


def gerar_codigo(tamanho: int = 6) -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(tamanho))
