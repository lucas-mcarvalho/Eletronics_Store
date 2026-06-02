from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from category.models import Categoria
from product.models import Produto
from usuario.jwt import JWT_COOKIE_NAME, gerar_token

from .forms import ItemPedidoForm, PagamentoForm, PedidoForm
from .models import ItemPedido, Pagamento, Pedido
from .views import obter_quantidade


def autenticar(client, usuario):
    client.defaults['HTTP_HOST'] = 'localhost'
    client.cookies[JWT_COOKIE_NAME] = gerar_token(usuario)


class BasePedidoTestCase(TestCase):
    # Classe base para criar os objetos utilizados nos testes de pedido

    def setUp(self):
        self.usuario = User.objects.create_user(username='cliente', password='12345@teste')
        self.admin = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.produto = Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco=Decimal('3500.00'),
            categoria=self.categoria,
            estoque=5,
        )


class TestesModelPedido(BasePedidoTestCase):
    # Classe de testes para os modelos Pedido, ItemPedido e Pagamento

    def test_valor_total(self):
        pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        ItemPedido.objects.create(pedido=pedido, produto=self.produto, quantidade=2, preco_unitario=Decimal('3500.00'))

        self.assertEqual(pedido.valor_total, Decimal('7000.00'))

    def test_subtotal_item(self):
        pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        item = ItemPedido.objects.create(pedido=pedido, produto=self.produto, quantidade=3, preco_unitario=Decimal('3500.00'))

        self.assertEqual(item.subtotal, Decimal('10500.00'))

    def test_preco_unitario_preenchido_automaticamente(self):
        pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        item = ItemPedido.objects.create(pedido=pedido, produto=self.produto, quantidade=1)

        self.assertEqual(item.preco_unitario, self.produto.preco)

    def test_valor_pagamento_preenchido_automaticamente(self):
        pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        ItemPedido.objects.create(pedido=pedido, produto=self.produto, quantidade=2, preco_unitario='3500.00')
        pagamento = Pagamento.objects.create(pedido=pedido, forma=Pagamento.FORMA_PIX)

        self.assertEqual(pagamento.valor, Decimal('7000.00'))


class TestesFormPedido(BasePedidoTestCase):
    # Classe de testes para os formularios de pedido

    def test_form_pedido_valido(self):
        dados = {
            'status': Pedido.STATUS_ABERTO,
            'observacao': 'Pedido de teste',
        }
        form = PedidoForm(data=dados)
        self.assertTrue(form.is_valid())

    def test_form_item_pedido_valido(self):
        dados = {
            'produto': self.produto.id,
            'quantidade': 2,
        }
        form = ItemPedidoForm(data=dados)
        self.assertTrue(form.is_valid())

    def test_form_pagamento_valido(self):
        dados = {
            'forma': Pagamento.FORMA_PIX,
            'status': Pagamento.STATUS_APROVADO,
            'valor': '3500.00',
            'codigo_transacao': 'ABC123',
            'pago_em': '',
        }
        form = PagamentoForm(data=dados)
        self.assertTrue(form.is_valid())


class TestesFuncaoObterQuantidade(TestCase):
    # Classe de testes para a funcao obter_quantidade

    def test_quantidade_valida(self):
        request = type('Request', (), {'POST': {'quantidade': '3'}})()
        self.assertEqual(obter_quantidade(request), 3)

    def test_quantidade_invalida_retorna_um(self):
        request = type('Request', (), {'POST': {'quantidade': 'abc'}})()
        self.assertEqual(obter_quantidade(request), 1)

    def test_quantidade_menor_que_um_retorna_um(self):
        request = type('Request', (), {'POST': {'quantidade': '-5'}})()
        self.assertEqual(obter_quantidade(request), 1)


class TestesViewCarrinhoDetalhar(BasePedidoTestCase):
    # Classe de testes para a view CarrinhoDetalhar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.url = reverse('carrinho_detalhar')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('carrinho'), self.pedido)


class TestesViewAdicionarCarrinho(BasePedidoTestCase):
    # Classe de testes para a view AdicionarCarrinho

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.url = reverse('adicionar_carrinho', kwargs={'produto_id': self.produto.id})

    def test_post_cria_item_no_carrinho(self):
        response = self.client.post(self.url, {'quantidade': 2})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('carrinho_detalhar'))
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(ItemPedido.objects.count(), 1)
        self.assertEqual(ItemPedido.objects.first().quantidade, 2)

    def test_post_limita_quantidade_ao_estoque(self):
        response = self.client.post(self.url, {'quantidade': 10})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ItemPedido.objects.first().quantidade, self.produto.estoque)


class TestesViewAtualizarItemCarrinho(BasePedidoTestCase):
    # Classe de testes para a view AtualizarItemCarrinho

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.item = ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=1)
        self.url = reverse('atualizar_item_carrinho', kwargs={'item_id': self.item.id})

    def test_post_atualiza_quantidade(self):
        response = self.client.post(self.url, {'quantidade': 3})
        self.item.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('carrinho_detalhar'))
        self.assertEqual(self.item.quantidade, 3)

    def test_post_limita_quantidade_ao_estoque(self):
        response = self.client.post(self.url, {'quantidade': 10})
        self.item.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.item.quantidade, self.produto.estoque)


class TestesViewRemoverItemCarrinho(BasePedidoTestCase):
    # Classe de testes para a view RemoverItemCarrinho

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.item = ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=1)
        self.url = reverse('remover_item_carrinho', kwargs={'item_id': self.item.id})

    def test_post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('carrinho_detalhar'))
        self.assertEqual(ItemPedido.objects.count(), 0)


class TestesViewFinalizarCarrinho(BasePedidoTestCase):
    # Classe de testes para a view FinalizarCarrinho

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.item = ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=2)
        self.url = reverse('finalizar_carrinho')

    def test_post_finaliza_pedido(self):
        response = self.client.post(self.url)
        self.pedido.refresh_from_db()
        self.produto.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(self.pedido.status, Pedido.STATUS_FECHADO)
        self.assertEqual(self.produto.estoque, 3)


class TestesViewListarPedidos(BasePedidoTestCase):
    # Classe de testes para a view PedidoListar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido_fechado = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_FECHADO)
        Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        outro_usuario = User.objects.create_user(username='outro', password='12345@teste')
        Pedido.objects.create(usuario=outro_usuario, status=Pedido.STATUS_FECHADO)
        self.url = reverse('pedido_listar')

    def test_get_cliente(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.get('pedidos')), 1)
        self.assertEqual(response.context.get('pedidos')[0], self.pedido_fechado)


class TestesViewDetalharPedido(BasePedidoTestCase):
    # Classe de testes para a view PedidoDetalhar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.usuario)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_FECHADO)
        self.url = reverse('pedido_detalhar', kwargs={'id': self.pedido.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('pedido'), Pedido)
        self.assertEqual(response.context.get('pedido').pk, self.pedido.pk)


class TestesViewCriarPedidos(BasePedidoTestCase):
    # Classe de testes para a view PedidoCadastrar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.url = reverse('pedido_cadastrar')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), PedidoForm)

    def test_post(self):
        dados = {
            'status': Pedido.STATUS_FECHADO,
            'observacao': 'Pedido criado pelo admin',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_listar'))
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(Pedido.objects.first().usuario, self.admin)


class TestesViewEditarPedidos(BasePedidoTestCase):
    # Classe de testes para a view PedidoEditar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.url = reverse('pedido_editar', kwargs={'id': self.pedido.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), PedidoForm)
        self.assertEqual(response.context.get('object').pk, self.pedido.pk)

    def test_post(self):
        dados = {
            'status': Pedido.STATUS_FECHADO,
            'observacao': 'Pedido atualizado',
        }
        response = self.client.post(self.url, dados)
        self.pedido.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_listar'))
        self.assertEqual(self.pedido.status, Pedido.STATUS_FECHADO)


class TestesViewDeletarPedidos(BasePedidoTestCase):
    # Classe de testes para a view PedidoExcluir

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.url = reverse('pedido_excluir', kwargs={'id': self.pedido.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), Pedido)
        self.assertEqual(response.context.get('object').pk, self.pedido.pk)

    def test_post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_listar'))
        self.assertEqual(Pedido.objects.count(), 0)


class TestesViewCriarItensPedido(BasePedidoTestCase):
    # Classe de testes para a view ItemPedidoCadastrar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.url = reverse('item_pedido_cadastrar', kwargs={'pedido_id': self.pedido.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), ItemPedidoForm)
        self.assertEqual(response.context.get('pedido'), self.pedido)

    def test_post(self):
        dados = {
            'produto': self.produto.id,
            'quantidade': 2,
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(ItemPedido.objects.count(), 1)
        self.assertEqual(ItemPedido.objects.first().pedido, self.pedido)


class TestesViewEditarItensPedido(BasePedidoTestCase):
    # Classe de testes para a view ItemPedidoEditar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.item = ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=1)
        self.url = reverse('item_pedido_editar', kwargs={'item_id': self.item.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), ItemPedidoForm)
        self.assertEqual(response.context.get('pedido'), self.pedido)

    def test_post(self):
        dados = {
            'produto': self.produto.id,
            'quantidade': 4,
        }
        response = self.client.post(self.url, dados)
        self.item.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(self.item.quantidade, 4)


class TestesViewDeletarItensPedido(BasePedidoTestCase):
    # Classe de testes para a view ItemPedidoExcluir

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_ABERTO)
        self.item = ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=1)
        self.url = reverse('item_pedido_excluir', kwargs={'item_id': self.item.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), ItemPedido)
        self.assertEqual(response.context.get('object').pk, self.item.pk)

    def test_post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(ItemPedido.objects.count(), 0)


class TestesViewCriarPagamento(BasePedidoTestCase):
    # Classe de testes para a view PagamentoCadastrar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_FECHADO)
        ItemPedido.objects.create(pedido=self.pedido, produto=self.produto, quantidade=1)
        self.url = reverse('pagamento_cadastrar', kwargs={'pedido_id': self.pedido.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), PagamentoForm)
        self.assertEqual(response.context.get('pedido'), self.pedido)

    def test_post(self):
        dados = {
            'forma': Pagamento.FORMA_PIX,
            'status': Pagamento.STATUS_APROVADO,
            'valor': '',
            'codigo_transacao': 'ABC123',
            'pago_em': '',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(Pagamento.objects.count(), 1)
        self.assertEqual(Pagamento.objects.first().pedido, self.pedido)


class TestesViewEditarPagamento(BasePedidoTestCase):
    # Classe de testes para a view PagamentoEditar

    def setUp(self):
        super().setUp()
        autenticar(self.client, self.admin)
        self.pedido = Pedido.objects.create(usuario=self.usuario, status=Pedido.STATUS_FECHADO)
        self.pagamento = Pagamento.objects.create(
            pedido=self.pedido,
            forma=Pagamento.FORMA_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=Decimal('3500.00'),
        )
        self.url = reverse('pagamento_editar', kwargs={'pagamento_id': self.pagamento.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), PagamentoForm)
        self.assertEqual(response.context.get('pedido'), self.pedido)

    def test_post(self):
        dados = {
            'forma': Pagamento.FORMA_CARTAO,
            'status': Pagamento.STATUS_APROVADO,
            'valor': '3500.00',
            'codigo_transacao': 'XYZ789',
            'pago_em': '',
        }
        response = self.client.post(self.url, dados)
        self.pagamento.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pedido_detalhar', args=[self.pedido.id]))
        self.assertEqual(self.pagamento.forma, Pagamento.FORMA_CARTAO)
        self.assertEqual(self.pagamento.status, Pagamento.STATUS_APROVADO)
