import json

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.utils.decorators import method_decorator

from usuario.jwt import JWT_COOKIE_NAME, buscar_usuario_por_token
from usuario.mixins import AdminRequiredMixin

from .forms import CategoriaForm
from .models import Categoria


class CategoriaListar(AdminRequiredMixin, ListView):
    model = Categoria
    context_object_name = 'categorias'
    template_name = 'produtos/categoria_listar.html'


class CategoriaCadastrar(AdminRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('categoria_listar')


class CategoriaEditar(AdminRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('categoria_listar')
    pk_url_kwarg = 'id'


class CategoriaExcluir(AdminRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'produtos/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_listar')
    pk_url_kwarg = 'id'


class CategoriaApiMixin:
    allowed_methods = 'GET, POST, OPTIONS'

    def get_usuario(self, request):
        authorization = request.headers.get('Authorization', '')

        if authorization.startswith('Token '):
            token = authorization.removeprefix('Token ').strip()
        elif authorization.startswith('Bearer '):
            token = authorization.removeprefix('Bearer ').strip()
        else:
            token = request.COOKIES.get(JWT_COOKIE_NAME)

        return buscar_usuario_por_token(token)

    def get_admin(self, request):
        usuario = self.get_usuario(request)

        if usuario is None or not usuario.is_staff:
            return None

        return usuario

    def json_response(self, data, status=200):
        response = JsonResponse(data, status=status, safe=not isinstance(data, list))
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Methods'] = self.allowed_methods
        return response


@method_decorator(csrf_exempt, name='dispatch')
class CategoriaApiListar(CategoriaApiMixin, View):
    def options(self, request):
        return self.json_response({})

    def get(self, request):
        usuario = self.get_usuario(request)

        if usuario is None:
            return self.json_response({'erro': 'Token invalido.'}, status=401)

        categorias = Categoria.objects.filter(ativo=True).order_by('nome')
        dados = [
            {
                'id': categoria.pk,
                'nome': categoria.nome,
                'descricao': categoria.descricao or '',
                'ativo': categoria.ativo,
            }
            for categoria in categorias
        ]

        return self.json_response(dados)


@method_decorator(csrf_exempt, name='dispatch')
class CategoriaApiCadastrar(CategoriaApiMixin, View):
    def options(self, request):
        return self.json_response({})

    def post(self, request):
        if self.get_admin(request) is None:
            return self.json_response({'erro': 'Acesso restrito a administradores.'}, status=403)

        try:
            dados = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return self.json_response({'erro': 'JSON invalido.'}, status=400)

        nome = (dados.get('nome') or '').strip()

        if not nome:
            return self.json_response({'erro': 'Informe o nome da categoria.'}, status=400)

        categoria = Categoria.objects.create(
            nome=nome,
            descricao=(dados.get('descricao') or '').strip(),
            ativo=bool(dados.get('ativo', True)),
        )

        return self.json_response({
            'id': categoria.pk,
            'nome': categoria.nome,
            'descricao': categoria.descricao or '',
            'ativo': categoria.ativo,
        }, status=201)
