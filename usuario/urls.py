from django.urls import path

from .views import AdminHome, Cadastro, Login, Logout

urlpatterns = [
    path('', Login.as_view(), name='login'),
    path('cadastro/', Cadastro.as_view(), name='cadastro'),
    path('painel/', AdminHome.as_view(), name='admin_home'),
    path('logout/', Logout.as_view(), name='logout'),
]
