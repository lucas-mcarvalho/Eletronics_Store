from django.urls import path

from .views import CategoriaCadastrar, CategoriaEditar, CategoriaExcluir, CategoriaListar

urlpatterns = [
    path('', CategoriaListar.as_view(), name='categoria_listar'),
    path('nova/', CategoriaCadastrar.as_view(), name='categoria_cadastrar'),
    path('<int:id>/editar/', CategoriaEditar.as_view(), name='categoria_editar'),
    path('<int:id>/excluir/', CategoriaExcluir.as_view(), name='categoria_excluir'),
]
