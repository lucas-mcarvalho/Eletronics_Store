import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpResponse } from '@capacitor/core';
import { FormsModule } from '@angular/forms';
import { IonicModule, LoadingController, NavController, ToastController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';

import { Usuario } from '../home/usuario.models';
import { ItemPedido, Pedido } from '../pedido/pedido.model';
import { ApiService } from '../services/api.service';
import { Produto } from './produto.model';

@Component({
  selector: 'app-produto',
  standalone: true,
  imports: [IonicModule, CommonModule, FormsModule],
  templateUrl: './produto.page.html',
  styleUrls: ['./produto.page.scss'],
  providers: [Storage],
})
export class ProdutoPage implements OnInit {
  public usuario: Usuario = new Usuario();
  public produtos: Produto[] = [];
  public carrinho: Pedido = new Pedido();
  public carregandoLista = false;
  public carregandoCarrinho = false;
  public mensagemErro = '';
  public termoBusca = '';
  public abaAtual: 'catalogo' | 'carrinho' = 'catalogo';
  public slideDestaqueAtual = 0;
  public adicionandoProdutoId = 0;
  public itemAtualizandoId = 0;
  public itemRemovendoId = 0;
  public finalizandoCarrinho = false;
  public formaPagamento = 'pix';

  private storageReady?: Promise<Storage>;

  constructor(
    private storage: Storage,
    private controleCarregamento: LoadingController,
    private controleToast: ToastController,
    private controleNavegacao: NavController,
    private api: ApiService,
  ) {}

  async ngOnInit(): Promise<void> {
    const storage = await this.getStorage();
    const registro = await storage.get('usuario');

    if (registro) {
      this.usuario = Object.assign(new Usuario(), registro);
      return;
    }

    this.controleNavegacao.navigateRoot('/home');
  }

  async ionViewWillEnter(): Promise<void> {
    if (this.usuario.token) {
      await this.carregarDados();
    }
  }

  get produtosFiltrados(): Produto[] {
    const termo = this.termoBusca.trim().toLowerCase();

    if (!termo) {
      return this.produtos;
    }

    return this.produtos.filter((produto) => {
      return (
        produto.nome.toLowerCase().includes(termo) ||
        this.nomeCategoriaProduto(produto).toLowerCase().includes(termo) ||
        produto.codigo_sku.toLowerCase().includes(termo)
      );
    });
  }

  get totalItensCarrinho(): number {
    return this.carrinho.itens.reduce((total, item) => total + Number(item.quantidade || 0), 0);
  }

  get carrinhoTemItens(): boolean {
    return this.totalItensCarrinho > 0;
  }

  get produtosDestaque(): Produto[] {
    return this.produtos.filter((produto) => produto.estoque > 0).slice(0, 6);
  }

  get produtoDestaqueAtual(): Produto | undefined {
    const destaques = this.produtosDestaque;

    if (destaques.length === 0) {
      return undefined;
    }

    return destaques[Math.min(this.slideDestaqueAtual, destaques.length - 1)];
  }

  private getStorage(): Promise<Storage> {
    if (!this.storageReady) {
      this.storageReady = this.storage.create();
    }

    return this.storageReady;
  }

  async consultarProdutosSistemaWeb(): Promise<void> {
    this.carregandoLista = true;
    this.mensagemErro = '';

    const loading = await this.controleCarregamento.create({
      message: 'Carregando produtos...',
      spinner: 'crescent',
    });

    await loading.present();

    this.api.get('/produtos/api/listar/', this.usuario)
      .then(async (resposta: HttpResponse) => {
        if (resposta.status === 200 && Array.isArray(resposta.data)) {
          this.produtos = resposta.data
            .map((produto: any) => Object.assign(new Produto(), produto))
            .filter((produto: Produto) => produto.ativo && produto.estoque > 0);
          this.normalizarSlideDestaque();
        } else {
          this.produtos = [];
          this.mensagemErro = 'Nao foi possivel carregar os produtos cadastrados.';
          await this.exibirToast(this.mensagemErro);
        }

        await loading.dismiss();
        this.carregandoLista = false;
      })
      .catch(async (error) => {
        await loading.dismiss();
        this.carregandoLista = false;
        this.produtos = [];
        this.mensagemErro = 'Erro ao consultar produtos. Verifique o backend.';
        await this.exibirToast(this.mensagemErro);
        console.error('Erro ao consultar produtos:', error);
      });
  }

  async carregarDados(): Promise<void> {
    await this.consultarProdutosSistemaWeb();
    await this.carregarCarrinho();
  }

  obterImagem(url?: string): string {
    if (!url) {
      return 'assets/icon/favicon.png';
    }

    const imagemUrl = url.startsWith('http://') || url.startsWith('https://') ? url : this.api.url(url);
    return this.anexarTokenImagem(imagemUrl);
  }

  imagemProduto(produto: Produto): string {
    return this.obterImagem(produto.imagem_url || produto.imagem);
  }

  nomeCategoriaProduto(produto: Produto): string {
    return produto.nome_categoria || produto.categoria || '';
  }

  async carregarCarrinho(): Promise<void> {
    this.carregandoCarrinho = true;

    try {
      const resposta = await this.api.get('/pedidos/api/carrinho/', this.usuario);

      if (resposta.status === 200) {
        this.atualizarCarrinhoLocal(resposta.data);
      }
    } catch (error) {
      console.error('Erro ao carregar carrinho:', error);
      await this.exibirToast('Erro ao carregar carrinho. Verifique o backend.');
    } finally {
      this.carregandoCarrinho = false;
    }
  }

  async adicionarAoCarrinho(produto: Produto): Promise<void> {
    this.adicionandoProdutoId = produto.id;

    try {
      const resposta = await this.api.post('/pedidos/api/carrinho/adicionar/', {
        produto_id: produto.id,
        quantidade: 1,
      }, this.usuario);

      if (resposta.status === 201) {
        this.atualizarCarrinhoLocal(resposta.data);
        await this.exibirToast('Produto adicionado ao carrinho.');
        return;
      }

      await this.exibirToast(resposta.data?.erro || 'Nao foi possivel adicionar ao carrinho.');
    } catch (error) {
      console.error('Erro ao adicionar ao carrinho:', error);
      await this.exibirToast('Erro ao adicionar ao carrinho. Verifique o backend.');
    } finally {
      this.adicionandoProdutoId = 0;
    }
  }

  mudarDestaque(delta: number): void {
    const total = this.produtosDestaque.length;

    if (total < 2) {
      return;
    }

    this.slideDestaqueAtual = (this.slideDestaqueAtual + delta + total) % total;
  }

  selecionarDestaque(index: number): void {
    if (index < 0 || index >= this.produtosDestaque.length) {
      return;
    }

    this.slideDestaqueAtual = index;
  }

  async atualizarItemCarrinho(item: ItemPedido, quantidade: number): Promise<void> {
    if (quantidade < 1) {
      quantidade = 1;
    }

    this.itemAtualizandoId = item.id;

    try {
      const resposta = await this.api.post(`/pedidos/api/carrinho/itens/${item.id}/atualizar/`, {
        quantidade,
      }, this.usuario);

      if (resposta.status === 200) {
        this.atualizarCarrinhoLocal(resposta.data);
        return;
      }

      if (resposta.data?.carrinho) {
        this.atualizarCarrinhoLocal(resposta.data.carrinho);
      }

      await this.exibirToast(resposta.data?.erro || 'Nao foi possivel atualizar o carrinho.');
    } catch (error) {
      console.error('Erro ao atualizar carrinho:', error);
      await this.exibirToast('Erro ao atualizar carrinho. Verifique o backend.');
    } finally {
      this.itemAtualizandoId = 0;
    }
  }

  async alterarQuantidadeCarrinho(item: ItemPedido, delta: number): Promise<void> {
    await this.atualizarItemCarrinho(item, Number(item.quantidade || 0) + delta);
  }

  async removerItemCarrinho(item: ItemPedido): Promise<void> {
    this.itemRemovendoId = item.id;

    try {
      const resposta = await this.api.post(`/pedidos/api/carrinho/itens/${item.id}/remover/`, {}, this.usuario);

      if (resposta.status === 200) {
        this.atualizarCarrinhoLocal(resposta.data);
        await this.exibirToast('Item removido do carrinho.');
        return;
      }

      await this.exibirToast(resposta.data?.erro || 'Nao foi possivel remover o item.');
    } catch (error) {
      console.error('Erro ao remover item:', error);
      await this.exibirToast('Erro ao remover item. Verifique o backend.');
    } finally {
      this.itemRemovendoId = 0;
    }
  }

  async finalizarCarrinhoAtual(): Promise<void> {
    if (!this.carrinhoTemItens) {
      await this.exibirToast('Seu carrinho esta vazio.');
      return;
    }

    this.finalizandoCarrinho = true;

    try {
      const resposta = await this.api.post('/pedidos/api/carrinho/finalizar/', {
        forma_pagamento: this.formaPagamento,
      }, this.usuario);

      if (resposta.status === 201) {
        this.carrinho = new Pedido();
        this.abaAtual = 'catalogo';
        await this.exibirToast('Pedido finalizado e pagamento aprovado!');
        await this.consultarProdutosSistemaWeb();
        this.controleNavegacao.navigateForward('/pedido');
        return;
      }

      await this.exibirToast(resposta.data?.erro || 'Nao foi possivel finalizar o carrinho.');
    } catch (error) {
      console.error('Erro ao finalizar carrinho:', error);
      await this.exibirToast('Erro ao finalizar carrinho. Verifique o backend.');
    } finally {
      this.finalizandoCarrinho = false;
    }
  }

  async abrirPedidos(): Promise<void> {
    this.controleNavegacao.navigateForward('/pedido');
  }

  abrirCarrinho(): void {
    this.abaAtual = 'carrinho';
  }

  formatarPreco(produto: Produto): string {
    const valor = Number(produto.preco || 0);
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  formatarValor(valor: string | number): string {
    return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  async atualizarLista(event?: CustomEvent): Promise<void> {
    await this.carregarDados();

    if (event?.target && 'complete' in event.target) {
      (event.target as HTMLIonRefresherElement).complete();
    }
  }

  async sair(): Promise<void> {
    const storage = await this.getStorage();
    await storage.remove('usuario');
    this.controleNavegacao.navigateRoot('/home');
  }

  private async exibirToast(mensagem: string): Promise<void> {
    const toast = await this.controleToast.create({
      message: mensagem,
      duration: 2000,
      position: 'bottom',
      color: 'dark',
    });

    await toast.present();
  }

  private atualizarCarrinhoLocal(dados: any): void {
    this.carrinho = Object.assign(new Pedido(), dados || {});
    this.carrinho.itens = Array.isArray(dados?.itens)
      ? dados.itens.map((item: any) => Object.assign(new ItemPedido(), item))
      : [];
  }

  private normalizarSlideDestaque(): void {
    if (this.slideDestaqueAtual >= this.produtosDestaque.length) {
      this.slideDestaqueAtual = 0;
    }
  }

  private anexarTokenImagem(url: string): string {
    if (!this.usuario.token || !url.includes('/media/produtos/')) {
      return url;
    }

    const separador = url.includes('?') ? '&' : '?';
    return `${url}${separador}token=${encodeURIComponent(this.usuario.token)}`;
  }
}
