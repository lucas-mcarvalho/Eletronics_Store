from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

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
