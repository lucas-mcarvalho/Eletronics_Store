import json

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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


def _json_response(data, status=200):
    response = JsonResponse(data, status=status, safe=not isinstance(data, list))
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


@method_decorator(csrf_exempt, name='dispatch')
class LoginApi(View):
    def options(self, request):
        return _json_response({})

    def post(self, request):
        try:
            dados = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return _json_response({'erro': 'JSON invalido.'}, status=400)

        usuario = dados.get('username') or dados.get('usuario')
        senha = dados.get('password') or dados.get('senha')
        user = authenticate(request, username=usuario, password=senha)

        if user is None or not user.is_active:
            return _json_response({'erro': 'Usuario ou senha invalidos.'}, status=401)

        return _json_response({
            'id': user.pk,
            'username': user.get_username(),
            'email': user.email,
            'is_staff': user.is_staff,
            'token': gerar_token(user),
        })


@method_decorator(csrf_exempt, name='dispatch')
class CadastroApi(View):
    def options(self, request):
        return _json_response({})

    def post(self, request):
        try:
            dados = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return _json_response({'erro': 'JSON invalido.'}, status=400)

        form = CadastroForm({
            'username': dados.get('username', ''),
            'email': dados.get('email', ''),
            'password1': dados.get('password1', ''),
            'password2': dados.get('password2', ''),
        })

        if not form.is_valid():
            erros = []

            for mensagens in form.errors.values():
                erros.extend(mensagens)

            return _json_response({'erro': ' '.join(erros)}, status=400)

        user = form.save()

        return _json_response({
            'id': user.pk,
            'username': user.get_username(),
            'email': user.email,
            'is_staff': user.is_staff,
            'token': gerar_token(user),
        }, status=201)


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
