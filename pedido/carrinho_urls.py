from django.urls import path

from .views import (
    AdicionarCarrinho,
    AtualizarItemCarrinho,
    CarrinhoDetalhar,
    FinalizarCarrinho,
    RemoverItemCarrinho,
)

urlpatterns = [
    path('', CarrinhoDetalhar.as_view(), name='carrinho_detalhar'),
    path('adicionar/<int:produto_id>/', AdicionarCarrinho.as_view(), name='adicionar_carrinho'),
    path('itens/<int:item_id>/atualizar/', AtualizarItemCarrinho.as_view(), name='atualizar_item_carrinho'),
    path('itens/<int:item_id>/remover/', RemoverItemCarrinho.as_view(), name='remover_item_carrinho'),
    path('finalizar/', FinalizarCarrinho.as_view(), name='finalizar_carrinho'),
]
