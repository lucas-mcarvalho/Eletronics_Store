import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from product.models import Produto

from .forms import ItemPedidoForm, PagamentoForm, PedidoForm
from .models import ItemPedido, Pagamento, Pedido
from .serializers import SerializadorPedido


def filtrar_pedidos_para_usuario(queryset, usuario):
    if usuario.is_staff:
        return queryset

    return queryset.filter(usuario=usuario).exclude(status=Pedido.STATUS_ABERTO)


def obter_pedido_api(usuario, pedido_id):
    pedidos = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto')

    if not usuario.is_staff:
        pedidos = pedidos.filter(usuario=usuario)

    try:
        return pedidos.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        return None


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


def criar_pagamento_simulado(pedido, forma):
    return Pagamento.objects.get_or_create(
        pedido=pedido,
        defaults={
            'forma': forma,
            'status': Pagamento.STATUS_PENDENTE,
            'valor': pedido.valor_total,
            'codigo_transacao': f'SIM-{uuid.uuid4().hex[:12].upper()}',
        },
    )


def atualizar_status_pagamento(pagamento, status):
    pagamento.status = status
    pagamento.pago_em = timezone.now() if status == Pagamento.STATUS_APROVADO else None
    pagamento.save()


def serializar_pagamento(pagamento):
    return {
        'id': pagamento.pk,
        'pedido_id': pagamento.pedido_id,
        'forma': pagamento.forma,
        'status': pagamento.status,
        'valor': str(pagamento.valor),
        'codigo_transacao': pagamento.codigo_transacao or '',
        'pago_em': pagamento.pago_em.isoformat() if pagamento.pago_em else None,
        'criado_em': pagamento.criado_em.isoformat(),
        'atualizado_em': pagamento.atualizado_em.isoformat(),
    }


class CarrinhoDetalhar(LoginRequiredMixin, View):
    template_name = 'carrinho/detalhar.html'

    def get(self, request):
        carrinho = obter_carrinho(request.user)
        return render(request, self.template_name, {'carrinho': carrinho})


class AdicionarCarrinho(LoginRequiredMixin, View):
    def post(self, request, produto_id):
        produto = get_object_or_404(Produto, id=produto_id, ativo=True, estoque__gt=0)
        quantidade = obter_quantidade(request)
        carrinho = obter_ou_criar_carrinho(request.user)

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


class AtualizarItemCarrinho(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido.objects.select_related('pedido', 'produto'),
            id=item_id,
            pedido__usuario=request.user,
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


class RemoverItemCarrinho(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido,
            id=item_id,
            pedido__usuario=request.user,
            pedido__status=Pedido.STATUS_ABERTO,
        )
        item.delete()
        messages.success(request, 'Item removido do carrinho.')

        return redirect('carrinho_detalhar')


class FinalizarCarrinho(LoginRequiredMixin, View):
    def post(self, request):
        carrinho = obter_carrinho(request.user)
        forma_pagamento = request.POST.get('forma_pagamento')
        formas_validas = [opcao[0] for opcao in Pagamento.FORMA_CHOICES]

        if not carrinho or not carrinho.itens.exists():
            messages.error(request, 'Seu carrinho esta vazio.')
            return redirect('carrinho_detalhar')

        if forma_pagamento not in formas_validas:
            messages.error(request, 'Escolha uma forma de pagamento valida.')
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
            carrinho.observacao = 'Pedido finalizado com pagamento simulado aprovado.'
            carrinho.save()
            pagamento, _ = criar_pagamento_simulado(carrinho, forma_pagamento)
            atualizar_status_pagamento(pagamento, Pagamento.STATUS_APROVADO)

        messages.success(request, 'Pedido finalizado e pagamento aprovado com sucesso.')
        return redirect(reverse('pedido_detalhar', args=[carrinho.id]))


class PedidoListar(LoginRequiredMixin, ListView):
    model = Pedido
    context_object_name = 'pedidos'
    template_name = 'pedidos/pedido_listar.html'

    def get_queryset(self):
        queryset = Pedido.objects.select_related('usuario').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(queryset, self.request.user)


class PedidoApiListar(ListAPIView):
    serializer_class = SerializadorPedido
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pedidos = (
            Pedido.objects.select_related('usuario', 'pagamento')
            .prefetch_related('itens__produto')
            .order_by('-criado_em')
        )

        if self.request.user.is_staff:
            return pedidos

        return pedidos.filter(usuario=self.request.user).exclude(status=Pedido.STATUS_ABERTO)


class PedidoApiCadastrar(CreateAPIView):
    serializer_class = SerializadorPedido
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class PedidoApiDetalharAtualizar(RetrieveUpdateAPIView):
    serializer_class = SerializadorPedido
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pedidos = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(pedidos, self.request.user)


class PedidoApiDeletar(DestroyAPIView):
    serializer_class = SerializadorPedido
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pedidos = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(pedidos, self.request.user)


class PedidoApiFinalizarProduto(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        produto_id = request.data.get('produto_id')
        forma_pagamento = request.data.get('forma_pagamento')
        formas_validas = [opcao[0] for opcao in Pagamento.FORMA_CHOICES]

        try:
            quantidade = int(request.data.get('quantidade') or 1)
        except (TypeError, ValueError):
            quantidade = 1

        if quantidade < 1:
            quantidade = 1

        if forma_pagamento not in formas_validas:
            return Response({'erro': 'Forma de pagamento invalida.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            produto = get_object_or_404(
                Produto.objects.select_for_update(),
                id=produto_id,
                ativo=True,
                estoque__gt=0,
            )

            if quantidade > produto.estoque:
                return Response({'erro': 'Quantidade maior que o estoque disponivel.'}, status=status.HTTP_400_BAD_REQUEST)

            pedido = Pedido.objects.create(
                usuario=request.user,
                status=Pedido.STATUS_FECHADO,
                observacao='Pedido mobile com pagamento simulado aprovado.',
            )
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=produto.preco,
            )
            produto.estoque -= quantidade
            produto.save()
            pagamento, _ = criar_pagamento_simulado(pedido, forma_pagamento)
            atualizar_status_pagamento(pagamento, Pagamento.STATUS_APROVADO)

        pedido = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto').get(id=pedido.id)
        return Response(SerializadorPedido(pedido).data, status=status.HTTP_201_CREATED)


class CarrinhoApiDetalhar(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carrinho = obter_carrinho(request.user)

        if not carrinho:
            return Response({
                'id': 0,
                'status': Pedido.STATUS_ABERTO,
                'valor_total': '0.00',
                'itens': [],
            })

        return Response(SerializadorPedido(carrinho).data)


class CarrinhoApiAdicionar(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        produto_id = request.data.get('produto_id')

        try:
            quantidade = int(request.data.get('quantidade') or 1)
        except (TypeError, ValueError):
            quantidade = 1

        if quantidade < 1:
            quantidade = 1

        produto = get_object_or_404(Produto, id=produto_id, ativo=True, estoque__gt=0)
        carrinho = obter_ou_criar_carrinho(request.user)

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

        carrinho = Pedido.objects.prefetch_related('itens__produto').get(id=carrinho.id)
        return Response(SerializadorPedido(carrinho).data, status=status.HTTP_201_CREATED)


class CarrinhoApiAtualizarItem(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido.objects.select_related('pedido', 'produto'),
            id=item_id,
            pedido__usuario=request.user,
            pedido__status=Pedido.STATUS_ABERTO,
        )

        try:
            quantidade = int(request.data.get('quantidade') or 1)
        except (TypeError, ValueError):
            quantidade = 1

        if quantidade < 1:
            quantidade = 1

        if item.produto.estoque < 1:
            item.delete()
            carrinho = obter_ou_criar_carrinho(request.user)
            return Response({
                'erro': 'Produto sem estoque e removido do carrinho.',
                'carrinho': SerializadorPedido(carrinho).data,
            }, status=status.HTTP_400_BAD_REQUEST)

        if quantidade > item.produto.estoque:
            quantidade = item.produto.estoque

        item.quantidade = quantidade
        item.preco_unitario = item.produto.preco
        item.save()

        carrinho = Pedido.objects.prefetch_related('itens__produto').get(id=item.pedido_id)
        return Response(SerializadorPedido(carrinho).data)


class CarrinhoApiRemoverItem(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        item = get_object_or_404(
            ItemPedido,
            id=item_id,
            pedido__usuario=request.user,
            pedido__status=Pedido.STATUS_ABERTO,
        )
        pedido_id = item.pedido_id
        item.delete()

        carrinho = Pedido.objects.prefetch_related('itens__produto').get(id=pedido_id)
        return Response(SerializadorPedido(carrinho).data)


class CarrinhoApiFinalizar(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        carrinho = obter_carrinho(request.user)
        forma_pagamento = request.data.get('forma_pagamento')
        formas_validas = [opcao[0] for opcao in Pagamento.FORMA_CHOICES]

        if not carrinho or not carrinho.itens.exists():
            return Response({'erro': 'Seu carrinho esta vazio.'}, status=status.HTTP_400_BAD_REQUEST)

        if forma_pagamento not in formas_validas:
            return Response({'erro': 'Escolha uma forma de pagamento valida.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            carrinho = Pedido.objects.select_for_update().get(id=carrinho.id)
            itens = list(carrinho.itens.select_related('produto'))

            for item in itens:
                produto = Produto.objects.select_for_update().get(id=item.produto_id)

                if produto.estoque < item.quantidade:
                    return Response({
                        'erro': f'Estoque insuficiente para {produto.nome}.',
                    }, status=status.HTTP_400_BAD_REQUEST)

            for item in itens:
                produto = Produto.objects.select_for_update().get(id=item.produto_id)
                produto.estoque -= item.quantidade
                produto.save()

            carrinho.status = Pedido.STATUS_FECHADO
            carrinho.observacao = 'Pedido mobile finalizado pelo carrinho com pagamento simulado aprovado.'
            carrinho.save()
            pagamento, _ = criar_pagamento_simulado(carrinho, forma_pagamento)
            atualizar_status_pagamento(pagamento, Pagamento.STATUS_APROVADO)

        pedido = Pedido.objects.select_related('usuario', 'pagamento').prefetch_related('itens__produto').get(id=carrinho.id)
        return Response(SerializadorPedido(pedido).data, status=status.HTTP_201_CREATED)


class PagamentoApiSimular(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pedido_id):
        pedido = obter_pedido_api(request.user, pedido_id)

        if pedido is None:
            return Response({'erro': 'Pedido nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        pagamento = getattr(pedido, 'pagamento', None)

        if pagamento is None:
            return Response({'erro': 'Pagamento nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializar_pagamento(pagamento))

    def post(self, request, pedido_id):
        pedido = obter_pedido_api(request.user, pedido_id)

        if pedido is None:
            return Response({'erro': 'Pedido nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if pedido.status == Pedido.STATUS_ABERTO:
            return Response({'erro': 'Finalize o carrinho antes de pagar.'}, status=status.HTTP_400_BAD_REQUEST)

        forma = request.data.get('forma')
        formas_validas = [opcao[0] for opcao in Pagamento.FORMA_CHOICES]

        if forma not in formas_validas:
            return Response({
                'erro': 'Forma de pagamento invalida.',
                'formas_validas': formas_validas,
            }, status=status.HTTP_400_BAD_REQUEST)

        pagamento, criado = criar_pagamento_simulado(pedido, forma)

        if not criado:
            return Response({
                'mensagem': 'Este pedido ja possui pagamento.',
                'pagamento': serializar_pagamento(pagamento),
            })

        return Response(serializar_pagamento(pagamento), status=status.HTTP_201_CREATED)


class PagamentoApiAtualizarStatus(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    novo_status = None

    def post(self, request, pedido_id):
        pedido = obter_pedido_api(request.user, pedido_id)

        if pedido is None:
            return Response({'erro': 'Pedido nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        pagamento = getattr(pedido, 'pagamento', None)

        if pagamento is None:
            return Response({'erro': 'Pagamento nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        atualizar_status_pagamento(pagamento, self.novo_status)

        return Response(serializar_pagamento(pagamento))


class PagamentoApiAprovar(PagamentoApiAtualizarStatus):
    novo_status = Pagamento.STATUS_APROVADO


class PagamentoApiRecusar(PagamentoApiAtualizarStatus):
    novo_status = Pagamento.STATUS_RECUSADO


class PagamentoApiCancelar(PagamentoApiAtualizarStatus):
    novo_status = Pagamento.STATUS_CANCELADO


class PedidoDetalhar(LoginRequiredMixin, DetailView):
    model = Pedido
    context_object_name = 'pedido'
    template_name = 'pedidos/pedido_detalhar.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        queryset = Pedido.objects.select_related('usuario').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(queryset, self.request.user)


class PedidoCadastrar(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_listar')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class PedidoEditar(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Pedido.objects.select_related('usuario').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(queryset, self.request.user)


class PedidoExcluir(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Pedido
    template_name = 'pedidos/pedido_confirm_delete.html'
    success_url = reverse_lazy('pedido_listar')
    pk_url_kwarg = 'id'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Pedido.objects.select_related('usuario').prefetch_related('itens__produto')
        return filtrar_pedidos_para_usuario(queryset, self.request.user)


class ItemPedidoCadastrar(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ItemPedido
    form_class = ItemPedidoForm
    template_name = 'pedidos/item_pedido_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.get_pedido()
        return contexto

    def form_valid(self, form):
        form.instance.pedido = self.get_pedido()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.get_pedido().id])

    def get_pedido(self):
        if hasattr(self, 'pedido'):
            return self.pedido

        queryset = Pedido.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)

        self.pedido = get_object_or_404(queryset, id=self.kwargs['pedido_id'])
        return self.pedido


class ItemPedidoEditar(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ItemPedido
    form_class = ItemPedidoForm
    template_name = 'pedidos/item_pedido_form.html'
    pk_url_kwarg = 'item_id'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = ItemPedido.objects.select_related('pedido', 'produto')

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.object.pedido
        return contexto

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])


class ItemPedidoExcluir(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ItemPedido
    template_name = 'pedidos/item_pedido_confirm_delete.html'
    pk_url_kwarg = 'item_id'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = ItemPedido.objects.select_related('pedido', 'produto')

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.user)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])


class PagamentoCadastrar(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'pedidos/pagamento_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and self.test_func():
            pedido = self.get_pedido()

            if hasattr(pedido, 'pagamento'):
                return redirect('pagamento_editar', pagamento_id=pedido.pagamento.id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.get_pedido()
        return contexto

    def form_valid(self, form):
        form.instance.pedido = self.get_pedido()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.get_pedido().id])

    def get_pedido(self):
        if hasattr(self, 'pedido'):
            return self.pedido

        queryset = Pedido.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)

        self.pedido = get_object_or_404(queryset, id=self.kwargs['pedido_id'])
        return self.pedido


class PagamentoEditar(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'pedidos/pagamento_form.html'
    pk_url_kwarg = 'pagamento_id'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Pagamento.objects.select_related('pedido')

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(pedido__usuario=self.request.user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['pedido'] = self.object.pedido
        return contexto

    def get_success_url(self):
        return reverse('pedido_detalhar', args=[self.object.pedido_id])
