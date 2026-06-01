from django.forms import ModelForm

from product.models import Produto

from .models import ItemPedido, Pagamento, Pedido


class PedidoForm(ModelForm):
    class Meta:
        model = Pedido
        fields = ['status', 'observacao']


class ItemPedidoForm(ModelForm):
    class Meta:
        model = ItemPedido
        fields = ['produto', 'quantidade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)


class PagamentoForm(ModelForm):
    class Meta:
        model = Pagamento
        fields = ['forma', 'status', 'valor', 'codigo_transacao', 'pago_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor'].required = False
        self.fields['pago_em'].required = False
