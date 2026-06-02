from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from category.models import Categoria
from usuario.jwt import JWT_COOKIE_NAME, gerar_token

from .forms import ProdutoForm
from .models import Produto


def autenticar(client, usuario):
    client.defaults['HTTP_HOST'] = 'localhost'
    client.cookies[JWT_COOKIE_NAME] = gerar_token(usuario)


class TestesModelProduto(TestCase):
    # Classe de testes para o modelo Produto

    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.instancia = Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco='3500.00',
            categoria=self.categoria,
            modelo='Inspiron',
            estoque=5,
        )

    def test_str(self):
        self.assertEqual(str(self.instancia), 'Notebook Dell')

    def test_codigo_sku_gerado(self):
        self.assertTrue(self.instancia.codigo_sku.startswith('NOTEBOOKDELL-'))


class TestesFormProduto(TestCase):
    # Classe de testes para o formulario ProdutoForm

    def setUp(self):
        self.categoria_ativa = Categoria.objects.create(nome='Notebooks', ativo=True)
        self.categoria_inativa = Categoria.objects.create(nome='Antigos', ativo=False)

    def test_form_valido(self):
        dados = {
            'nome': 'Mouse Gamer',
            'descricao': 'Mouse com sensor optico',
            'preco': '199.90',
            'categoria': self.categoria_ativa.id,
            'modelo': 'MG100',
            'estoque': 10,
            'garantia_meses': 12,
            'ativo': 'on',
        }
        form = ProdutoForm(data=dados)
        self.assertTrue(form.is_valid())

    def test_form_exibe_apenas_categorias_ativas(self):
        form = ProdutoForm()
        self.assertIn(self.categoria_ativa, form.fields['categoria'].queryset)
        self.assertNotIn(self.categoria_inativa, form.fields['categoria'].queryset)


class TestesViewLojaHome(TestCase):
    # Classe de testes para a view LojaHome

    def setUp(self):
        self.usuario = User.objects.create_user(username='cliente', password='12345@teste')
        autenticar(self.client, self.usuario)
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.produto_ativo = Produto.objects.create(
            nome='Notebook Ativo',
            descricao='Produto disponivel',
            preco='3000.00',
            categoria=self.categoria,
            estoque=3,
            ativo=True,
        )
        Produto.objects.create(
            nome='Notebook Sem Estoque',
            descricao='Produto indisponivel',
            preco='2500.00',
            categoria=self.categoria,
            estoque=0,
            ativo=True,
        )
        Produto.objects.create(
            nome='Notebook Inativo',
            descricao='Produto inativo',
            preco='2000.00',
            categoria=self.categoria,
            estoque=2,
            ativo=False,
        )
        self.url = reverse('loja_home')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.get('produtos')), 1)
        self.assertEqual(response.context.get('produtos')[0], self.produto_ativo)


class TestesViewListarProdutos(TestCase):
    # Classe de testes para a view ProdutoListar

    def setUp(self):
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.categoria = Categoria.objects.create(nome='Notebooks')
        Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco='3500.00',
            categoria=self.categoria,
            estoque=5,
        )
        self.url = reverse('produto_listar')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.get('produtos')), 1)


class TestesViewCriarProdutos(TestCase):
    # Classe de testes para a view ProdutoCadastrar

    def setUp(self):
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.url = reverse('produto_cadastrar')

    def test_get_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), ProdutoForm)

    def test_get_nao_autenticado(self):
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_post(self):
        dados = {
            'nome': 'Teclado Mecanico',
            'descricao': 'Teclado com switches azuis',
            'preco': '299.90',
            'categoria': self.categoria.id,
            'modelo': 'TK100',
            'estoque': 8,
            'garantia_meses': 12,
            'ativo': 'on',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('produto_listar'))
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Produto.objects.first().nome, 'Teclado Mecanico')


class TestesViewEditarProdutos(TestCase):
    # Classe de testes para a view ProdutoEditar

    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.instancia = Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco='3500.00',
            categoria=self.categoria,
            estoque=5,
        )
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('produto_editar', kwargs={'id': self.instancia.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), Produto)
        self.assertIsInstance(response.context.get('form'), ProdutoForm)
        self.assertEqual(response.context.get('object').pk, self.instancia.pk)

    def test_post(self):
        dados = {
            'nome': 'Notebook Lenovo',
            'descricao': 'Notebook atualizado',
            'preco': '4200.00',
            'categoria': self.categoria.id,
            'modelo': 'ThinkPad',
            'estoque': 4,
            'garantia_meses': 24,
            'ativo': 'on',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('produto_listar'))
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Produto.objects.first().nome, 'Notebook Lenovo')
        self.assertEqual(Produto.objects.first().pk, self.instancia.pk)


class TestesViewDeletarProdutos(TestCase):
    # Classe de testes para a view ProdutoExcluir

    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Notebooks')
        self.instancia = Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco='3500.00',
            categoria=self.categoria,
            estoque=5,
        )
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('produto_excluir', kwargs={'id': self.instancia.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), Produto)
        self.assertEqual(response.context.get('object').pk, self.instancia.pk)

    def test_post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('produto_listar'))
        self.assertEqual(Produto.objects.count(), 0)
