from django.shortcuts import redirect

from .jwt import JWT_COOKIE_NAME, buscar_usuario_por_token


class JWTLoginRequiredMixin:
    login_url = 'login'

    def get_jwt_user(self, request):
        token = request.COOKIES.get(JWT_COOKIE_NAME)
        return buscar_usuario_por_token(token)

    def dispatch(self, request, *args, **kwargs):
        usuario = self.get_jwt_user(request)

        if usuario is None:
            return redirect(self.login_url)

        request.jwt_user = usuario
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(JWTLoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        usuario = self.get_jwt_user(request)

        if usuario is None:
            return redirect(self.login_url)

        request.jwt_user = usuario

        if not usuario.is_staff:
            return redirect('loja_home')

        return super().dispatch(request, *args, **kwargs)
