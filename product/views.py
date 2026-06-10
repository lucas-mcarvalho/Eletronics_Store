from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.urls import reverse_lazy
from django.utils._os import safe_join
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .forms import ProdutoForm
from .models import Produto
from .serializers import SerializadorProduto, SerializadorProdutoCompleto


class LojaHome(LoginRequiredMixin, ListView):
    model = Produto
    context_object_name = 'produtos'
    template_name = 'loja/home.html'

    def get_queryset(self):
        return Produto.objects.filter(ativo=True, estoque__gt=0).select_related('categoria')


class ProdutoListar(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Produto
    context_object_name = 'produtos'
    template_name = 'produtos/produto_listar.html'

    def test_func(self):
        return self.request.user.is_staff


class ProdutoCadastrar(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produto_listar')

    def test_func(self):
        return self.request.user.is_staff


class ProdutoEditar(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produto_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff


class ProdutoExcluir(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Produto
    template_name = 'produtos/produto_confirm_delete.html'
    success_url = reverse_lazy('produto_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff


class ProdutoImagemProtegida(View):
    def get_usuario_por_token(self, request):
        authorization = request.headers.get('Authorization', '')

        if authorization.startswith('Token '):
            token = authorization.removeprefix('Token ').strip()
        else:
            token = request.GET.get('token')

        if not token:
            return None

        try:
            return Token.objects.select_related('user').get(key=token).user
        except Token.DoesNotExist:
            return None

    def get(self, request, caminho):
        usuario = request.user if request.user.is_authenticated else self.get_usuario_por_token(request)

        if usuario is None:
            raise Http404()

        try:
            caminho_arquivo = safe_join(settings.MEDIA_ROOT, 'produtos', caminho)
        except SuspiciousFileOperation as exc:
            raise Http404() from exc

        if not Produto.objects.filter(imagem=f'produtos/{caminho}').exists():
            raise Http404()

        try:
            return FileResponse(open(caminho_arquivo, 'rb'))
        except FileNotFoundError as exc:
            raise Http404() from exc


class ProdutoApiListar(ListAPIView):
    serializer_class = SerializadorProduto
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Produto.objects.select_related('categoria')

        return Produto.objects.filter(ativo=True, estoque__gt=0).select_related('categoria')


class ProdutoApiCadastrar(CreateAPIView):
    serializer_class = SerializadorProdutoCompleto
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Produto.objects.select_related('categoria')


class ProdutoApiDetalharAtualizar(RetrieveUpdateAPIView):
    serializer_class = SerializadorProdutoCompleto
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Produto.objects.select_related('categoria')


class ProdutoApiDeletar(DestroyAPIView):
    serializer_class = SerializadorProduto
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Produto.objects.select_related('categoria')
