from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views.generic import View
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CadastroForm


def get_redirect_usuario(user):
    if user.is_staff:
        return 'admin_home'

    return 'loja_home'


class Login(View):
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(get_redirect_usuario(request.user))

        return render(request, self.template_name)

    def post(self, request):
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        user = authenticate(request, username=usuario, password=senha)

        if user is None:
            return render(
                request,
                self.template_name,
                {'mensagem': 'Usuario ou senha invalidos.'},
            )

        if not user.is_active:
            return render(
                request,
                self.template_name,
                {'mensagem': 'Sua conta esta desativada.'},
            )

        auth_login(request, user)
        return redirect(get_redirect_usuario(user))


class LoginApi(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={
                'request': request,
            },
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'id': user.id,
            'nome': user.first_name,
            'email': user.email,
            'token': token.key,
            'username': user.get_username(),
            'is_staff': user.is_staff,
        })


class CadastroApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = CadastroForm({
            'username': request.data.get('username', ''),
            'email': request.data.get('email', ''),
            'password1': request.data.get('password1', ''),
            'password2': request.data.get('password2', ''),
        })

        if not form.is_valid():
            erros = []

            for mensagens in form.errors.values():
                erros.extend(mensagens)

            return Response({'erro': ' '.join(erros)}, status=status.HTTP_400_BAD_REQUEST)

        user = form.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'id': user.pk,
            'nome': user.first_name,
            'username': user.get_username(),
            'email': user.email,
            'is_staff': user.is_staff,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class EsqueciSenhaApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()

        if not email:
            return Response({'erro': 'Informe o e-mail.'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user is None:
            return Response({'mensagem': 'Se o e-mail existir, enviaremos as instrucoes.'})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
        mensagem = render_to_string('password_reset_email.html', {
            'email': user.email,
            'domain': request.get_host(),
            'site_name': 'Eletronics Store',
            'uid': uid,
            'user': user,
            'token': token,
            'protocol': 'https' if request.is_secure() else 'http',
        })

        send_mail(
            subject='Redefinicao de senha | Eletronics Store',
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({
            'mensagem': 'Se o e-mail existir, enviaremos as instrucoes.',
            'reset_url': reset_url if settings.DEBUG else '',
        })


class RedefinirSenhaApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid') or request.data.get('uidb64')
        token = request.data.get('token')
        senha = request.data.get('password') or request.data.get('senha') or request.data.get('new_password1')
        confirmar = request.data.get('password2') or request.data.get('senha2') or request.data.get('new_password2')

        if not uid or not token or not senha or not confirmar:
            return Response({'erro': 'Informe uid, token, password e password2.'}, status=status.HTTP_400_BAD_REQUEST)

        if senha != confirmar:
            return Response({'erro': 'As senhas nao conferem.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = get_user_model().objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            return Response({'erro': 'Token invalido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'erro': 'Token invalido.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(senha)
        user.save()
        Token.objects.filter(user=user).delete()

        return Response({'mensagem': 'Senha redefinida com sucesso.'})


class Cadastro(View):
    template_name = 'cadastro.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CadastroForm()})

    def post(self, request):
        form = CadastroForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        user = form.save()
        auth_login(request, user)
        return redirect('loja_home')


class AdminHome(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'admin_home.html'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        from category.models import Categoria
        from pedido.models import Pedido
        from product.models import Produto

        contexto = {
            'total_produtos': Produto.objects.count(),
            'total_categorias': Categoria.objects.count(),
            'total_pedidos': Pedido.objects.count(),
            'pedidos_recentes': Pedido.objects.select_related('usuario')[:5],
        }

        return render(request, self.template_name, contexto)


class Logout(View):
    def get(self, request):
        auth_logout(request)
        return redirect('login')
