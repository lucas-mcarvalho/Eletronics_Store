from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from category.models import Categoria
from pedido.models import Pedido
from product.models import Produto

from .forms import CadastroForm
from .jwt import JWT_COOKIE_NAME, buscar_usuario_por_token, gerar_token, validar_token


def autenticar(client, usuario):
    client.defaults['HTTP_HOST'] = 'localhost'
    client.cookies[JWT_COOKIE_NAME] = gerar_token(usuario)


class TestesJWT(TestCase):
    # Classe de testes para as funcoes de JWT

    def setUp(self):
        self.usuario = User.objects.create_user(username='cliente', password='12345@teste')

    def test_gerar_e_validar_token(self):
        token = gerar_token(self.usuario)
        payload = validar_token(token)

        self.assertEqual(payload.get('user_id'), self.usuario.id)
        self.assertEqual(payload.get('username'), self.usuario.username)

    def test_buscar_usuario_por_token(self):
        token = gerar_token(self.usuario)
        usuario = buscar_usuario_por_token(token)

        self.assertEqual(usuario, self.usuario)

    def test_token_invalido(self):
        self.assertIsNone(validar_token('token.invalido'))
        self.assertIsNone(buscar_usuario_por_token('token.invalido'))


class TestesFormCadastro(TestCase):
    # Classe de testes para o formulario CadastroForm

    def test_form_valido(self):
        dados = {
            'username': 'cliente',
            'email': 'CLIENTE@EXAMPLE.COM',
            'password1': 'SenhaForte123',
            'password2': 'SenhaForte123',
        }
        form = CadastroForm(data=dados)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('email'), 'cliente@example.com')

    def test_email_duplicado(self):
        User.objects.create_user(username='cliente', email='cliente@example.com', password='SenhaForte123')
        dados = {
            'username': 'outro',
            'email': 'CLIENTE@example.com',
            'password1': 'SenhaForte123',
            'password2': 'SenhaForte123',
        }
        form = CadastroForm(data=dados)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TestesViewLogin(TestCase):
    # Classe de testes para a view Login

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.usuario = User.objects.create_user(username='cliente', password='12345@teste')
        self.url = reverse('login')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_valido(self):
        dados = {
            'usuario': 'cliente',
            'senha': '12345@teste',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('loja_home'))
        self.assertIn(JWT_COOKIE_NAME, response.cookies)

    def test_post_invalido(self):
        dados = {
            'usuario': 'cliente',
            'senha': 'senha-errada',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('mensagem'), 'Usuario ou senha invalidos.')


class TestesViewCadastro(TestCase):
    # Classe de testes para a view Cadastro

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.url = reverse('cadastro')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context.get('form'), CadastroForm)

    def test_post(self):
        dados = {
            'username': 'cliente',
            'email': 'cliente@example.com',
            'password1': 'SenhaForte123',
            'password2': 'SenhaForte123',
        }
        response = self.client.post(self.url, dados)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('loja_home'))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().email, 'cliente@example.com')
        self.assertIn(JWT_COOKIE_NAME, response.cookies)


class TestesViewAdminHome(TestCase):
    # Classe de testes para a view AdminHome

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='12345@teste', is_staff=True)
        autenticar(self.client, self.admin)
        categoria = Categoria.objects.create(nome='Notebooks')
        Produto.objects.create(
            nome='Notebook Dell',
            descricao='Notebook para trabalho',
            preco='3500.00',
            categoria=categoria,
            estoque=5,
        )
        Pedido.objects.create(usuario=self.admin, status=Pedido.STATUS_FECHADO)
        self.url = reverse('admin_home')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('total_produtos'), 1)
        self.assertEqual(response.context.get('total_categorias'), 1)
        self.assertEqual(response.context.get('total_pedidos'), 1)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestesViewResetSenha(TestCase):
    # Classe de testes para as views de redefinicao de senha

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.usuario = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='12345@teste',
        )

    def test_get_password_reset(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_post_password_reset(self):
        response = self.client.post(reverse('password_reset'), {'email': 'cliente@example.com'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)

    def test_get_password_reset_done(self):
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)

    def test_get_password_reset_complete(self):
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
