from django.contrib import admin

from .models import Produto


class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome',
        'categoria',
        'preco',
        'codigo_sku',
        'estoque',
        'garantia_meses',
        'ativo'
    )
    search_fields = ['nome', 'codigo_sku', 'modelo']
    list_filter = ['categoria', 'ativo']


admin.site.register(Produto, ProdutoAdmin)
