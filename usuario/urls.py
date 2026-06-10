from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from .views import AdminHome, Cadastro, CadastroApi, EsqueciSenhaApi, Login, LoginApi, Logout, RedefinirSenhaApi

urlpatterns = [
    path('', Login.as_view(), name='login'),
    path('autenticacao-api/', LoginApi.as_view(), name='autenticacao_api'),
    path('login-api/', LoginApi.as_view(), name='login_api'),
    path('cadastro-api/', CadastroApi.as_view(), name='cadastro_api'),
    path('senha/esqueci-api/', EsqueciSenhaApi.as_view(), name='password_reset_api'),
    path('senha/redefinir-api/', RedefinirSenhaApi.as_view(), name='password_reset_confirm_api'),
    path('cadastro/', Cadastro.as_view(), name='cadastro'),
    path(
        'senha/esqueci/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset_form.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'senha/enviada/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'senha/concluida/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('painel/', AdminHome.as_view(), name='admin_home'),
    path('logout/', Logout.as_view(), name='logout'),
]
