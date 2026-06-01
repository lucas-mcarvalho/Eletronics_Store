from secrets import token_hex

from django.db import models
from django.utils.text import slugify

from category.models import Categoria


class Produto(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)

    modelo = models.CharField(max_length=100, blank=True, null=True)
    codigo_sku = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    estoque = models.PositiveIntegerField(default=0)
    garantia_meses = models.PositiveIntegerField(default=12)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.codigo_sku:
            self.codigo_sku = self.gerar_codigo_sku()

        super().save(*args, **kwargs)

    def gerar_codigo_sku(self):
        prefixo = slugify(self.nome).upper().replace('-', '')[:20] or 'PROD'

        while True:
            codigo = f'{prefixo}-{token_hex(3).upper()}'

            if not Produto.objects.filter(codigo_sku=codigo).exists():
                return codigo
