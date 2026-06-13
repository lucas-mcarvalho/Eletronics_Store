from rest_framework.serializers import ModelSerializer, SerializerMethodField

from pedido.models import ItemPedido, Pagamento, Pedido


class SerializadorItemPedido(ModelSerializer):
    produto = SerializerMethodField()
    produto_id = SerializerMethodField()
    produto_estoque = SerializerMethodField()
    nome_produto = SerializerMethodField()
    subtotal = SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = ['id', 'produto_id', 'produto', 'produto_estoque', 'nome_produto', 'quantidade', 'preco_unitario', 'subtotal']

    def get_produto_id(self, instancia):
        return instancia.produto_id

    def get_produto(self, instancia):
        return instancia.produto.nome

    def get_produto_estoque(self, instancia):
        return instancia.produto.estoque

    def get_nome_produto(self, instancia):
        return instancia.produto.nome

    def get_subtotal(self, instancia):
        return str(instancia.subtotal)


class SerializadorPagamento(ModelSerializer):
    nome_forma = SerializerMethodField()
    nome_status = SerializerMethodField()

    class Meta:
        model = Pagamento
        fields = '__all__'

    def get_nome_forma(self, instancia):
        return instancia.get_forma_display()

    def get_nome_status(self, instancia):
        return instancia.get_status_display()


class SerializadorPedido(ModelSerializer):
    nome_usuario = SerializerMethodField()
    valor_total = SerializerMethodField()
    itens = SerializadorItemPedido(many=True, read_only=True)
    pagamento = SerializadorPagamento(read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ['usuario']

    def get_nome_usuario(self, instancia):
        return instancia.usuario.get_username()

    def get_valor_total(self, instancia):
        return str(instancia.valor_total)
