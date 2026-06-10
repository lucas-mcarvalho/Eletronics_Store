from rest_framework.serializers import ModelSerializer, SerializerMethodField

from product.models import Produto


class SerializadorProduto(ModelSerializer):
    nome_categoria = SerializerMethodField()
    imagem_url = SerializerMethodField()

    class Meta:
        model = Produto
        exclude = ['categoria', 'imagem']

    def get_nome_categoria(self, instancia):
        return instancia.categoria.nome

    def get_imagem_url(self, instancia):
        if not instancia.imagem:
            return ''

        request = self.context.get('request')

        if request is None:
            return instancia.imagem.url

        return request.build_absolute_uri(instancia.imagem.url)


class SerializadorProdutoCompleto(ModelSerializer):
    nome_categoria = SerializerMethodField()
    imagem_url = SerializerMethodField()

    class Meta:
        model = Produto
        fields = '__all__'

    def get_nome_categoria(self, instancia):
        return instancia.categoria.nome

    def get_imagem_url(self, instancia):
        if not instancia.imagem:
            return ''

        request = self.context.get('request')

        if request is None:
            return instancia.imagem.url

        return request.build_absolute_uri(instancia.imagem.url)
