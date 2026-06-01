from django.urls import path

from .views import (
    ItemPedidoCadastrar,
    ItemPedidoEditar,
    ItemPedidoExcluir,
    PagamentoCadastrar,
    PagamentoEditar,
    PedidoCadastrar,
    PedidoDetalhar,
    PedidoEditar,
    PedidoExcluir,
    PedidoListar,
)

urlpatterns = [
    path('', PedidoListar.as_view(), name='pedido_listar'),
    path('novo/', PedidoCadastrar.as_view(), name='pedido_cadastrar'),
    path('<int:id>/', PedidoDetalhar.as_view(), name='pedido_detalhar'),
    path('<int:id>/editar/', PedidoEditar.as_view(), name='pedido_editar'),
    path('<int:id>/excluir/', PedidoExcluir.as_view(), name='pedido_excluir'),
    path('<int:pedido_id>/itens/novo/', ItemPedidoCadastrar.as_view(), name='item_pedido_cadastrar'),
    path('itens/<int:item_id>/editar/', ItemPedidoEditar.as_view(), name='item_pedido_editar'),
    path('itens/<int:item_id>/excluir/', ItemPedidoExcluir.as_view(), name='item_pedido_excluir'),
    path('<int:pedido_id>/pagamento/novo/', PagamentoCadastrar.as_view(), name='pagamento_cadastrar'),
    path('pagamentos/<int:pagamento_id>/editar/', PagamentoEditar.as_view(), name='pagamento_editar'),
]
