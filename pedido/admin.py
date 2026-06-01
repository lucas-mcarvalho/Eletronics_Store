from django.contrib import admin

from .models import ItemPedido, Pagamento, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


class PagamentoInline(admin.StackedInline):
    model = Pagamento
    extra = 0
    max_num = 1


class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'status', 'valor_total', 'criado_em')
    list_filter = ('status', 'criado_em')
    search_fields = ('id', 'usuario__username')
    inlines = [ItemPedidoInline, PagamentoInline]


class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'produto', 'quantidade', 'preco_unitario', 'subtotal')
    list_filter = ('produto',)
    search_fields = ('pedido__id', 'produto__nome')


class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'forma', 'status', 'valor', 'pago_em')
    list_filter = ('forma', 'status')
    search_fields = ('pedido__id', 'codigo_transacao')


admin.site.register(Pedido, PedidoAdmin)
admin.site.register(ItemPedido, ItemPedidoAdmin)
admin.site.register(Pagamento, PagamentoAdmin)
