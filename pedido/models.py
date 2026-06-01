from decimal import Decimal

from django.conf import settings
from django.db import models

from product.models import Produto


class Pedido(models.Model):
    STATUS_ABERTO = 'aberto'
    STATUS_FECHADO = 'fechado'
    STATUS_CANCELADO = 'cancelado'

    STATUS_CHOICES = [
        (STATUS_ABERTO, 'Aberto'),
        (STATUS_FECHADO, 'Fechado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTO)
    observacao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Pedido #{self.pk}'

    @property
    def valor_total(self):
        if not self.pk:
            return Decimal('0.00')

        total = Decimal('0.00')

        for item in self.itens.all():
            total += item.subtotal

        return total


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='itens_pedido')
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'

    @property
    def subtotal(self):
        preco = self.preco_unitario or Decimal('0.00')
        return preco * self.quantidade

    def save(self, *args, **kwargs):
        if self.preco_unitario is None and self.produto_id:
            self.preco_unitario = self.produto.preco

        super().save(*args, **kwargs)


class Pagamento(models.Model):
    FORMA_PIX = 'pix'
    FORMA_CARTAO = 'cartao'
    FORMA_BOLETO = 'boleto'
    FORMA_DINHEIRO = 'dinheiro'

    FORMA_CHOICES = [
        (FORMA_PIX, 'Pix'),
        (FORMA_CARTAO, 'Cartao'),
        (FORMA_BOLETO, 'Boleto'),
        (FORMA_DINHEIRO, 'Dinheiro'),
    ]

    STATUS_PENDENTE = 'pendente'
    STATUS_APROVADO = 'aprovado'
    STATUS_RECUSADO = 'recusado'
    STATUS_CANCELADO = 'cancelado'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_RECUSADO, 'Recusado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pagamento')
    forma = models.CharField(max_length=20, choices=FORMA_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_transacao = models.CharField(max_length=120, blank=True, null=True)
    pago_em = models.DateTimeField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Pagamento do {self.pedido}'

    def save(self, *args, **kwargs):
        if not self.valor and self.pedido_id:
            self.valor = self.pedido.valor_total

        super().save(*args, **kwargs)
