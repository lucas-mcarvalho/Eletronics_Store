from django.urls import path

from .views import ProdutoApiCadastrar, ProdutoApiListar, ProdutoCadastrar, ProdutoEditar, ProdutoExcluir, ProdutoListar

urlpatterns = [
    path('', ProdutoListar.as_view(), name='produto_listar'),
    path('api/listar/', ProdutoApiListar.as_view(), name='produto_api_listar'),
    path('api/novo/', ProdutoApiCadastrar.as_view(), name='produto_api_cadastrar'),
    path('novo/', ProdutoCadastrar.as_view(), name='produto_cadastrar'),
    path('<int:id>/editar/', ProdutoEditar.as_view(), name='produto_editar'),
    path('<int:id>/excluir/', ProdutoExcluir.as_view(), name='produto_excluir'),
]
