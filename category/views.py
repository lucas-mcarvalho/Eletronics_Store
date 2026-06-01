from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

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
