import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import get_user_model


JWT_COOKIE_NAME = getattr(settings, 'JWT_COOKIE_NAME', 'access_token')
JWT_EXP_SECONDS = getattr(settings, 'JWT_EXP_SECONDS', 60 * 60 * 2)


def _base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data):
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _json_encode(data):
    return json.dumps(data, separators=(',', ':')).encode('utf-8')


def gerar_token(user):
    agora = int(time.time())
    header = {
        'alg': 'HS256',
        'typ': 'JWT',
    }
    payload = {
        'user_id': user.pk,
        'username': user.get_username(),
        'iat': agora,
        'exp': agora + JWT_EXP_SECONDS,
    }

    header_b64 = _base64url_encode(_json_encode(header))
    payload_b64 = _base64url_encode(_json_encode(payload))
    assinatura = _assinar(f'{header_b64}.{payload_b64}')

    return f'{header_b64}.{payload_b64}.{assinatura}'


def validar_token(token):
    try:
        header_b64, payload_b64, assinatura = token.split('.')
    except (AttributeError, ValueError):
        return None

    assinatura_esperada = _assinar(f'{header_b64}.{payload_b64}')

    if not hmac.compare_digest(assinatura, assinatura_esperada):
        return None

    try:
        payload = json.loads(_base64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError):
        return None

    if payload.get('exp', 0) < int(time.time()):
        return None

    return payload


def buscar_usuario_por_token(token):
    payload = validar_token(token)

    if not payload:
        return None

    User = get_user_model()

    try:
        return User.objects.get(pk=payload.get('user_id'), is_active=True)
    except User.DoesNotExist:
        return None


def _assinar(conteudo):
    chave = settings.SECRET_KEY.encode('utf-8')
    assinatura = hmac.new(chave, conteudo.encode('utf-8'), hashlib.sha256).digest()
    return _base64url_encode(assinatura)
