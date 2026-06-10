from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .forms import CategoriaForm
from .models import Categoria
from .serializers import SerializadorCategoria


class CategoriaListar(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Categoria
    context_object_name = 'categorias'
    template_name = 'produtos/categoria_listar.html'

    def test_func(self):
        return self.request.user.is_staff


class CategoriaCadastrar(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('categoria_listar')

    def test_func(self):
        return self.request.user.is_staff


class CategoriaEditar(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('categoria_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff


class CategoriaExcluir(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Categoria
    template_name = 'produtos/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff


class CategoriaApiListar(ListAPIView):
    serializer_class = SerializadorCategoria
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Categoria.objects.filter(ativo=True).order_by('nome')


class CategoriaApiCadastrar(CreateAPIView):
    serializer_class = SerializadorCategoria
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Categoria.objects.all()


class CategoriaApiDetalharAtualizar(RetrieveUpdateAPIView):
    serializer_class = SerializadorCategoria
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Categoria.objects.all()


class CategoriaApiDeletar(DestroyAPIView):
    serializer_class = SerializadorCategoria
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Categoria.objects.all()
