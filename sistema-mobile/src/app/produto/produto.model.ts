export class Produto {
  public id: number;
  public nome: string;
  public descricao: string;
  public preco: string;
  public categoria_id: number;
  public categoria: string;
  public nome_categoria: string;
  public modelo: string;
  public codigo_sku: string;
  public imagem: string;
  public imagem_url: string;
  public estoque: number;
  public garantia_meses: number;
  public ativo: boolean;

  constructor() {
    this.id = 0;
    this.nome = '';
    this.descricao = '';
    this.preco = '0.00';
    this.categoria_id = 0;
    this.categoria = '';
    this.nome_categoria = '';
    this.modelo = '';
    this.codigo_sku = '';
    this.imagem = '';
    this.imagem_url = '';
    this.estoque = 0;
    this.garantia_meses = 0;
    this.ativo = true;
  }
}
