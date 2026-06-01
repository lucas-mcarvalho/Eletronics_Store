from django.contrib import admin

from .models import Categoria


class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'ativo', 'criado_em', 'atualizado_em')
    search_fields = ['nome']
    list_filter = ['ativo']


admin.site.register(Categoria, CategoriaAdmin)
