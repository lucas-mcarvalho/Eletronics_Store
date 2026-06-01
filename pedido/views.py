from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from product.models import Produto
from usuario.mixins import AdminRequiredMixin, JWTLoginRequiredMixin

from .forms import ItemPedidoForm, PagamentoForm, PedidoForm
from .models import ItemPedido, Pagamento, Pedido


class PedidoQuerysetMixin:
    def get_queryset(self):
        queryset = Pedido.objects.select_related('usuario').prefetch_related('itens__produto')

        if self.request.jwt_user.is_staff:
            return queryset

        return queryset.filter(usuario=self.request.jwt_user).exclude(status=Pedido.STATUS_ABERTO)


def obter_carrinho(usuario):
    return (
        Pedido.objects.filter(usuario=usuario, status=Pedido.STATUS_ABERTO)
        .prefetch_related('itens__produto')
        .order_by('-criado_em')
        .first()
    )


def obter_ou_criar_carrinho(usuario):
    carrinho = obter_carrinho(usuario)

    if carrinho:
        return carrinho

    return Pedido.objects.create(usuario=usuario, status=Pedido.STATUS_ABERTO)


def obter_quantidade(request):
    try:
        quantidade = int(request.POST.get('quantidade') or 1)
    except ValueError:
        quantidade = 1

    if quantidade < 1:
        quantidade = 1

    return quantidade


class CarrinhoDetalhar(JWTLoginRequiredMixin, View):
    template_name = 'carrinho/detalhar.html'

    def get(self, request):
        carrinho = obter_carrinho(request.jwt_user)
        return render(request, self.template_name, {'carrinho': carrinho})


class AdicionarCarrinho(JWTLoginRequiredMixin, View):
    def post(self, request, produto_id):
        produto = get_object_or_404(Produto, id=produto_id, ativo=True, estoque__gt=0)
        quantidade = obter_quantidade(request)
        carrinho = obter_ou_criar_carrinho(request.jwt_user)

        item, _ = ItemPedido.objects.get_or_create(
            pedido=carrinho,
            produto=produto,
            defaults={
                'quantidade': 0,
                'preco_unitario': produto.preco,
            },
        )
        item.quantidade = min(item.quantidade + quantidade, produto.estoque)
        item.preco_unitario = produto.preco
        item.save()

        messages.success(request, 'Produto adicionado ao carrinho.')
        return redirect('carrinho_detalhar')


class AtualizarItemCarrinho(JWTLoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido.objects.select_related('pedido', 'produto'),
            id=item_id,
            pedido__usuario=request.jwt_user,
            pedido__status=Pedido.STATUS_ABERTO,
        )
        quantidade = obter_quantidade(request)

        if item.produto.estoque < 1:
            item.delete()
            messages.error(request, 'Produto sem estoque e removido do carrinho.')
            return redirect('carrinho_detalhar')

        if quantidade > item.produto.estoque:
            quantidade = item.produto.estoque
            messages.error(request, 'Quantidade ajustada ao estoque disponivel.')

        item.quantidade = quantidade
        item.preco_unitario = item.produto.preco
        item.save()

        return redirect('carrinho_detalhar')


class RemoverItemCarrinho(JWTLoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido,
            id=item_id,
            pedido__usuario=request.jwt_user,
            pedido__status=Pedido.STATUS_ABERTO,
        )
        item.delete()
        messages.success(request, 'Item removido do carrinho.')

        return redirect('carrinho_detalhar')


class FinalizarCarrinho(JWTLoginRequiredMixin, View):
    def post(self, request):
        carrinho = obter_carrinho(request.jwt_user)

        if not carrinho or not carrinho.itens.exists():
            messages.error(request, 'Seu carrinho esta vazio.')
            return redirect('carrinho_detalhar')

        with transaction.atomic():
            carrinho = Pedido.objects.select_for_update().get(id=carrinho.id)
            itens = list(carrinho.itens.select_related('produto'))
            estoque_ajustado = False

            for item in itens:
                produto = Produto.objects.select_for_update().get(id=item.produto_id)

                if produto.estoque >= item.quantidade:
                    continue

                estoque_ajustado = True

                if produto.estoque > 0:
                    item.quantidade = produto.estoque
                    item.preco_unitario = produto.preco
                    item.save()
                else:
                    item.delete()

            if estoque_ajustado:
                messages.error(request, 'Alguns itens foram ajustados por falta de estoque.')
                return redirect('carrinho_detalhar')

            for item in itens:
                produto = Produto.objects.select_for_update().get(id=item.produto_id)
                produto.estoque -= item.quantidade
                produto.save()

            carrinho.status = Pedido.STATUS_FECHADO
            carrinho.observacao = 'Pedido finalizado sem metodo de pagamento.'
            carrinho.save()

        messages.success(request, 'Pedido finalizado com sucesso.')
        return redirect(reverse('pedido_detalhar', args=[carrinho.id]))


class PedidoListar(JWTLoginRequiredMixin, PedidoQuerysetMixin, ListView):
    model = Pedido
    context_object_name = 'pedidos'
    template_name = 'pedidos/pedido_listar.html'


class PedidoDetalhar(JWTLoginRequiredMixin, PedidoQuerysetMixin, DetailView):
    model = Pedido
    context_object_name = 'pedido'
    template_name = 'pedidos/pedido_detalhar.html'
    pk_url_kwarg = 'id'


class PedidoCadastrar(AdminRequiredMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_listar')

    def form_valid(self, form):
        form.instance.usuario = self.request.jwt_user
        return super().form_valid(form)


class PedidoEditar(AdminRequiredMixin, PedidoQuerysetMixin, UpdateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_listar')
    pk_url_kwarg = 'id'


class PedidoExcluir(AdminRequiredMixin, PedidoQuerysetMixin, DeleteView):
    model = Pedido
    template_name = 'pedidos/pedido_confirm_delete.html'
    success_url = reverse_lazy('pedido_listar')
    pk_url_kwarg = 'id'


class ItemPedidoCadastrar(AdminRequiredMixin, CreateView):
    model = ItemPedido
    form_class = ItemPedidoForm
    template_name = 'pedidos/item_pedido_form.html'

    def dispatch(self, request, *args, **kwargs):
        usuario = self.get_jwt_user(request)

        if usuario is None:
            return redirect(self.login_url)

        if not usuario.is_staff:
            return redirect('loja_home')

        request.jwt_user = usuario
        self.pedido = self.get_pedido()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.pedido
        return contexto

    def form_valid(self, form):
        form.instance.pedido = self.pedido
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.pedido.id])

    def get_pedido(self):
        queryset = Pedido.objects.all()

        if not self.request.jwt_user.is_staff:
            queryset = queryset.filter(usuario=self.request.jwt_user)

        return get_object_or_404(queryset, id=self.kwargs['pedido_id'])


class ItemPedidoEditar(AdminRequiredMixin, UpdateView):
    model = ItemPedido
    form_class = ItemPedidoForm
    template_name = 'pedidos/item_pedido_form.html'
    pk_url_kwarg = 'item_id'

    def get_queryset(self):
        queryset = ItemPedido.objects.select_related('pedido', 'produto')

        if self.request.jwt_user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.jwt_user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.object.pedido
        return contexto

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])


class ItemPedidoExcluir(AdminRequiredMixin, DeleteView):
    model = ItemPedido
    template_name = 'pedidos/item_pedido_confirm_delete.html'
    pk_url_kwarg = 'item_id'

    def get_queryset(self):
        queryset = ItemPedido.objects.select_related('pedido', 'produto')

        if self.request.jwt_user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.jwt_user)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])


class PagamentoCadastrar(AdminRequiredMixin, CreateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'pedidos/pagamento_form.html'

    def dispatch(self, request, *args, **kwargs):
        usuario = self.get_jwt_user(request)

        if usuario is None:
            return redirect(self.login_url)

        if not usuario.is_staff:
            return redirect('loja_home')

        request.jwt_user = usuario
        self.pedido = self.get_pedido()

        if hasattr(self.pedido, 'pagamento'):
            return redirect('pagamento_editar', pagamento_id=self.pedido.pagamento.id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.pedido
        return contexto

    def form_valid(self, form):
        form.instance.pedido = self.pedido
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.pedido.id])

    def get_pedido(self):
        queryset = Pedido.objects.all()

        if not self.request.jwt_user.is_staff:
            queryset = queryset.filter(usuario=self.request.jwt_user)

        return get_object_or_404(queryset, id=self.kwargs['pedido_id'])


class PagamentoEditar(AdminRequiredMixin, UpdateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'pedidos/pagamento_form.html'
    pk_url_kwarg = 'pagamento_id'

    def get_queryset(self):
        queryset = Pagamento.objects.select_related('pedido')

        if self.request.jwt_user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.jwt_user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.object.pedido
        return contexto

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])
