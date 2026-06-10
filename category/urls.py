from django.urls import path

from .views import (
    CategoriaApiCadastrar,
    CategoriaApiDeletar,
    CategoriaApiDetalharAtualizar,
    CategoriaApiListar,
    CategoriaCadastrar,
    CategoriaEditar,
    CategoriaExcluir,
    CategoriaListar,
)

urlpatterns = [
    path('', CategoriaListar.as_view(), name='categoria_listar'),
    path('api/listar/', CategoriaApiListar.as_view(), name='categoria_api_listar'),
    path('api/nova/', CategoriaApiCadastrar.as_view(), name='categoria_api_cadastrar'),
    path('api/editar/<int:pk>/', CategoriaApiDetalharAtualizar.as_view(), name='categoria_api_editar'),
    path('api/deletar/<int:pk>/', CategoriaApiDeletar.as_view(), name='categoria_api_deletar'),
    path('nova/', CategoriaCadastrar.as_view(), name='categoria_cadastrar'),
    path('<int:id>/editar/', CategoriaEditar.as_view(), name='categoria_editar'),
    path('<int:id>/excluir/', CategoriaExcluir.as_view(), name='categoria_excluir'),
]
