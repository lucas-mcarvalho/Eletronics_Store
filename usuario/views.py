from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.views.generic import View

from .forms import CadastroForm
from .jwt import JWT_COOKIE_NAME, JWT_EXP_SECONDS, buscar_usuario_por_token, gerar_token
from .mixins import AdminRequiredMixin


def get_redirect_usuario(user):
    if user.is_staff:
        return 'admin_home'

    return 'loja_home'


class Login(View):
    template_name = 'login.html'

    def get(self, request):
        token = request.COOKIES.get(JWT_COOKIE_NAME)
        usuario = buscar_usuario_por_token(token)

        if usuario:
            return redirect(get_redirect_usuario(usuario))

        return render(request, self.template_name)

    def post(self, request):
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        user = authenticate(request, username=usuario, password=senha)

        if user is None:
            return render(
                request,
                self.template_name,
                {'mensagem': 'Usuario ou senha invalidos.'},
            )

        if not user.is_active:
            return render(
                request,
                self.template_name,
                {'mensagem': 'Sua conta esta desativada.'},
            )

        auth_login(request, user)
        response = redirect(get_redirect_usuario(user))
        response.set_cookie(
            JWT_COOKIE_NAME,
            gerar_token(user),
            max_age=JWT_EXP_SECONDS,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
        )

        return response


class Cadastro(View):
    template_name = 'cadastro.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CadastroForm()})

    def post(self, request):
        form = CadastroForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        user = form.save()
        auth_login(request, user)

        response = redirect('loja_home')
        response.set_cookie(
            JWT_COOKIE_NAME,
            gerar_token(user),
            max_age=JWT_EXP_SECONDS,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
        )

        return response


class AdminHome(AdminRequiredMixin, View):
    template_name = 'admin_home.html'

    def get(self, request):
        from category.models import Categoria
        from pedido.models import Pedido
        from product.models import Produto

        contexto = {
            'total_produtos': Produto.objects.count(),
            'total_categorias': Categoria.objects.count(),
            'total_pedidos': Pedido.objects.count(),
            'pedidos_recentes': Pedido.objects.select_related('usuario')[:5],
        }

        return render(request, self.template_name, contexto)


class Logout(View):
    def get(self, request):
        auth_logout(request)
        response = redirect('login')
        response.delete_cookie(JWT_COOKIE_NAME)

        return response
