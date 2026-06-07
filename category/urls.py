from django.urls import path

from .views import (
    CategoriaApiCadastrar,
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
    path('nova/', CategoriaCadastrar.as_view(), name='categoria_cadastrar'),
    path('<int:id>/editar/', CategoriaEditar.as_view(), name='categoria_editar'),
    path('<int:id>/excluir/', CategoriaExcluir.as_view(), name='categoria_excluir'),
]
