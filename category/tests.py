from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


from .forms import CategoriaForm
from .models import Categoria


def autenticar(client, usuario):
    client.defaults['HTTP_HOST'] = 'localhost'
    client.force_login(usuario)


class TestesModelCategoria(TestCase):
    # Classe de testes para o modelo Categoria

    def setUp(self):
        self.instancia = Categoria(nome='Notebooks', descricao='Produtos portateis')

    def test_str(self):
        self.assertEqual(str(self.instancia), 'Notebooks')


class TestesFormCategoria(TestCase):
    # Classe de testes para o formulario CategoriaForm

    def test_form_valido(self):
        dados = {
            'nome': 'Smartphones',
            'descricao': 'Celulares e acessorios',
            'ativo': 'on',
        }
        form = CategoriaForm(data=dados)
        self.assertTrue(form.is_valid())


class TestesViewListarCategorias(TestCase):
    # Classe de testes para a view CategoriaListar

    def setUp(self):
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('categoria_listar')
        Categoria.objects.create(nome='Notebooks', descricao='Produtos portateis')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.get('categorias')), 1)


class TestesViewCriarCategorias(TestCase):
    # Classe de testes para a view CategoriaCadastrar

    def setUp(self):
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('categoria_cadastrar')

    def test_get_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), CategoriaForm)

    def test_get_nao_autenticado(self):
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'{reverse("login")}?next={self.url}')

    def test_post(self):
        dados = {
            'nome': 'Monitores',
            'descricao': 'Telas para computador',
            'ativo': 'on',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('categoria_listar'))
        self.assertEqual(Categoria.objects.count(), 1)
        self.assertEqual(Categoria.objects.first().nome, 'Monitores')


class TestesViewEditarCategorias(TestCase):
    # Classe de testes para a view CategoriaEditar

    def setUp(self):
        self.instancia = Categoria.objects.create(nome='Notebooks', descricao='Produtos portateis')
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('categoria_editar', kwargs={'id': self.instancia.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), Categoria)
        self.assertIsInstance(response.context.get('form'), CategoriaForm)
        self.assertEqual(response.context.get('object').pk, self.instancia.pk)

    def test_post(self):
        dados = {
            'nome': 'Tablets',
            'descricao': 'Dispositivos moveis',
            'ativo': 'on',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('categoria_listar'))
        self.assertEqual(Categoria.objects.count(), 1)
        self.assertEqual(Categoria.objects.first().nome, 'Tablets')
        self.assertEqual(Categoria.objects.first().pk, self.instancia.pk)


class TestesViewDeletarCategorias(TestCase):
    # Classe de testes para a view CategoriaExcluir

    def setUp(self):
        self.instancia = Categoria.objects.create(nome='Notebooks', descricao='Produtos portateis')
        self.usuario = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.usuario)
        self.url = reverse('categoria_excluir', kwargs={'id': self.instancia.id})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('object'), Categoria)
        self.assertEqual(response.context.get('object').pk, self.instancia.pk)

    def test_post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('categoria_listar'))
        self.assertEqual(Categoria.objects.count(), 0)
