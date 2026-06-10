export class ItemPedido {
  public id = 0;
  public produto_id = 0;
  public produto = '';
  public nome_produto = '';
  public quantidade = 0;
  public preco_unitario = '0.00';
  public subtotal = '0.00';
}

export class Pagamento {
  public id = 0;
  public forma = '';
  public nome_forma = '';
  public status = '';
  public nome_status = '';
  public valor = '0.00';
  public codigo_transacao = '';
  public pago_em = '';
}

export class Pedido {
  public id = 0;
  public nome_usuario = '';
  public status = '';
  public observacao = '';
  public valor_total = '0.00';
  public criado_em = '';
  public itens: ItemPedido[] = [];
  public pagamento?: Pagamento;
}
