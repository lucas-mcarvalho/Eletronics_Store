from django.forms import ModelForm

from category.models import Categoria

from .models import Produto


class ProdutoForm(ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome',
            'descricao',
            'preco',
            'categoria',
            'modelo',
            'imagem',
            'estoque',
            'garantia_meses',
            'ativo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(ativo=True)
