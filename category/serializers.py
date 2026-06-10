from rest_framework.serializers import ModelSerializer

from category.models import Categoria


class SerializadorCategoria(ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
