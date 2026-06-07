import json

from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.utils.decorators import method_decorator

from category.models import Categoria
from usuario.jwt import JWT_COOKIE_NAME, buscar_usuario_por_token
from usuario.mixins import AdminRequiredMixin, JWTLoginRequiredMixin

from .forms import ProdutoForm
from .models import Produto


class LojaHome(JWTLoginRequiredMixin, ListView):
    model = Produto
    context_object_name = 'produtos'
    template_name = 'loja/home.html'

    def get_queryset(self):
        return Produto.objects.filter(ativo=True, estoque__gt=0).select_related('categoria')


class ProdutoListar(AdminRequiredMixin, ListView):
    model = Produto
    context_object_name = 'produtos'
    template_name = 'produtos/produto_listar.html'


class ProdutoCadastrar(AdminRequiredMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produto_listar')


class ProdutoEditar(AdminRequiredMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produto_listar')
    pk_url_kwarg = 'id'


class ProdutoExcluir(AdminRequiredMixin, DeleteView):
    model = Produto
    template_name = 'produtos/produto_confirm_delete.html'
    success_url = reverse_lazy('produto_listar')
    pk_url_kwarg = 'id'


class ProdutoApiMixin:
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

    def serialize_produto(self, produto):
        return {
            'id': produto.pk,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco),
            'categoria_id': produto.categoria_id,
            'categoria': produto.categoria.nome,
            'modelo': produto.modelo or '',
            'codigo_sku': produto.codigo_sku,
            'imagem': produto.imagem.url if produto.imagem else '',
            'estoque': produto.estoque,
            'garantia_meses': produto.garantia_meses,
            'ativo': produto.ativo,
        }


@method_decorator(csrf_exempt, name='dispatch')
class ProdutoApiListar(ProdutoApiMixin, View):
    def options(self, request):
        return self.json_response({})

    def get(self, request):
        usuario = self.get_usuario(request)

        if usuario is None:
            return self.json_response({'erro': 'Token invalido.'}, status=401)

        if usuario.is_staff:
            produtos = Produto.objects.select_related('categoria')
        else:
            produtos = Produto.objects.filter(ativo=True, estoque__gt=0).select_related('categoria')

        dados = [self.serialize_produto(produto) for produto in produtos]

        return self.json_response(dados)


@method_decorator(csrf_exempt, name='dispatch')
class ProdutoApiCadastrar(ProdutoApiMixin, View):
    def options(self, request):
        return self.json_response({})

    def post(self, request):
        if self.get_admin(request) is None:
            return self.json_response({'erro': 'Acesso restrito a administradores.'}, status=403)

        try:
            dados = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return self.json_response({'erro': 'JSON invalido.'}, status=400)

        campos_obrigatorios = ['nome', 'descricao', 'preco', 'categoria', 'estoque']
        faltando = [campo for campo in campos_obrigatorios if dados.get(campo) in (None, '')]

        if faltando:
            return self.json_response({'erro': f'Campos obrigatorios: {", ".join(faltando)}.'}, status=400)

        try:
            categoria = Categoria.objects.get(pk=dados.get('categoria'), ativo=True)
        except (Categoria.DoesNotExist, ValueError, TypeError):
            return self.json_response({'erro': 'Categoria invalida.'}, status=400)

        try:
            produto = Produto.objects.create(
                nome=str(dados.get('nome')).strip(),
                descricao=str(dados.get('descricao')).strip(),
                preco=dados.get('preco'),
                categoria=categoria,
                modelo=str(dados.get('modelo') or '').strip(),
                estoque=int(dados.get('estoque')),
                garantia_meses=int(dados.get('garantia_meses') or 12),
                ativo=bool(dados.get('ativo', True)),
            )
        except (ValueError, TypeError):
            return self.json_response({'erro': 'Preco, estoque ou garantia invalidos.'}, status=400)

        return self.json_response(self.serialize_produto(produto), status=201)
