import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpResponse } from '@capacitor/core';
import { FormsModule } from '@angular/forms';
import { IonicModule, LoadingController, NavController, ToastController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';

import { Usuario } from '../home/usuario.models';
import { ApiService } from '../services/api.service';
import { Categoria, Produto } from './produto.model';

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
  public categorias: Categoria[] = [];
  public carregandoLista = false;
  public mensagemErro = '';
  public termoBusca = '';
  public abaAtual: 'catalogo' | 'categoria' | 'produto' = 'catalogo';
  public salvandoCategoria = false;
  public salvandoProduto = false;
  public finalizandoProdutoId = 0;
  public formaPagamento = 'pix';
  public novaCategoria: Categoria = new Categoria();
  public novoProduto = {
    nome: '',
    descricao: '',
    preco: '',
    categoria: 0,
    modelo: '',
    estoque: 0,
    garantia_meses: 12,
    ativo: true,
  };

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

  get usuarioAdmin(): boolean {
    return this.usuario.is_staff;
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
          this.produtos = resposta.data.map((produto: any) => Object.assign(new Produto(), produto));
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

  async consultarCategoriasSistemaWeb(): Promise<void> {
    try {
      const resposta = await this.api.get('/categorias/api/listar/', this.usuario);

      if (resposta.status === 200 && Array.isArray(resposta.data)) {
        this.categorias = resposta.data.map((categoria: any) => Object.assign(new Categoria(), categoria));
      }
    } catch (error) {
      console.error('Erro ao consultar categorias:', error);
    }
  }

  async carregarDados(): Promise<void> {
    await this.consultarCategoriasSistemaWeb();
    await this.consultarProdutosSistemaWeb();
  }

  async cadastrarCategoria(): Promise<void> {
    if (!this.novaCategoria.nome.trim()) {
      await this.exibirToast('Informe o nome da categoria.');
      return;
    }

    this.salvandoCategoria = true;

    try {
      const resposta = await this.api.post('/categorias/api/nova/', this.novaCategoria, this.usuario);

      if (resposta.status === 201) {
        await this.exibirToast('Categoria cadastrada com sucesso!');
        this.novaCategoria = new Categoria();
        await this.consultarCategoriasSistemaWeb();
        this.abaAtual = 'produto';
      } else {
        await this.exibirToast(resposta.data?.erro || 'Nao foi possivel cadastrar a categoria.');
      }
    } catch (error) {
      console.error('Erro ao cadastrar categoria:', error);
      await this.exibirToast('Erro ao cadastrar categoria. Verifique o backend.');
    } finally {
      this.salvandoCategoria = false;
    }
  }

  async cadastrarProduto(): Promise<void> {
    if (!this.novoProduto.nome || !this.novoProduto.descricao || !this.novoProduto.preco || !this.novoProduto.categoria) {
      await this.exibirToast('Preencha nome, descricao, preco e categoria.');
      return;
    }

    this.salvandoProduto = true;

    try {
      const resposta = await this.api.post('/produtos/api/novo/', this.novoProduto, this.usuario);

      if (resposta.status === 201) {
        await this.exibirToast('Produto cadastrado com sucesso!');
        this.novoProduto = {
          nome: '',
          descricao: '',
          preco: '',
          categoria: 0,
          modelo: '',
          estoque: 0,
          garantia_meses: 12,
          ativo: true,
        };
        await this.consultarProdutosSistemaWeb();
        this.abaAtual = 'catalogo';
      } else {
        await this.exibirToast(resposta.data?.erro || 'Nao foi possivel cadastrar o produto.');
      }
    } catch (error) {
      console.error('Erro ao cadastrar produto:', error);
      await this.exibirToast('Erro ao cadastrar produto. Verifique o backend.');
    } finally {
      this.salvandoProduto = false;
    }
  }

  obterImagem(url?: string): string {
    if (!url) {
      return 'assets/icon/favicon.png';
    }

    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }

    return this.api.url(url);
  }

  imagemProduto(produto: Produto): string {
    return this.obterImagem(produto.imagem_url || produto.imagem);
  }

  nomeCategoriaProduto(produto: Produto): string {
    return produto.nome_categoria || produto.categoria || '';
  }

  async comprarProduto(produto: Produto): Promise<void> {
    this.finalizandoProdutoId = produto.id;

    try {
      const resposta = await this.api.post('/pedidos/api/finalizar-produto/', {
        produto_id: produto.id,
        quantidade: 1,
        forma_pagamento: this.formaPagamento,
      }, this.usuario);

      if (resposta.status === 201) {
        await this.exibirToast('Pedido finalizado e pagamento aprovado!');
        await this.carregarDados();
        return;
      }

      await this.exibirToast(resposta.data?.erro || 'Nao foi possivel finalizar o pedido.');
    } catch (error) {
      console.error('Erro ao finalizar pedido:', error);
      await this.exibirToast('Erro ao finalizar pedido. Verifique o backend.');
    } finally {
      this.finalizandoProdutoId = 0;
    }
  }

  async abrirPedidos(): Promise<void> {
    this.controleNavegacao.navigateForward('/pedido');
  }

  formatarPreco(produto: Produto): string {
    const valor = Number(produto.preco || 0);
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
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
}
