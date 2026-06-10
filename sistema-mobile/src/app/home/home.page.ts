import { HttpResponse } from '@capacitor/core';
import { Component } from '@angular/core';
import { LoadingController, ToastController, NavController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular'
import { Usuario } from './usuario.models';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-home',
  standalone: false,
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
  providers: [Storage],
})
export class HomePage {

  public instancia: { username: string; password: string } = {
    username: '',
    password: '',
  };

  public mostrarSenha = false;
  private storageReady?: Promise<Storage>;

  constructor(
    public controleCarregamento: LoadingController,
    public controleToast: ToastController,
    private storage: Storage,
    public controleNavegacao: NavController,
    private api: ApiService,
  ) {}

  private getStorage(): Promise<Storage> {
    if (!this.storageReady) {
      this.storageReady = this.storage.create();
    }

    return this.storageReady;
  }

  public async entrar(): Promise<void> {
    if (!this.instancia.username || !this.instancia.password) {
      await this.exibirToast('Informe usuário e senha para continuar.');
      return;
    }

    const carregando = await this.controleCarregamento.create({
      message: 'Entrando...',
      duration: 900,
      spinner: 'crescent',
    });

    await carregando.present();
    await carregando.onDidDismiss();

    await this.exibirToast(`Bem-vindo(a), ${this.instancia.username}!`);
  }

  // Inicializa interface com efeito de carregamento
  async autenticarUsuario() {
    const loading = await this.controleCarregamento.create({message: 'Autenticando...'});
    await loading.present();

    // Define informações do cabeçalho da requisição
    // Autentica usuário junto a API do sistema web
    this.api.post('/autenticacao-api/', this.instancia)
      .then(async (resposta: HttpResponse) => {
        // Verifica se a requisição foi processada com sucesso
        if(resposta.status === 200) {

          // Armazena localmente as credencias do usuário
          let usuario: Usuario = Object.assign(new Usuario(), resposta.data);
          const storage = await this.getStorage();
          await storage.set('usuario', usuario);

          // Finaliza autenticação e redireciona para interface inicial
          loading.dismiss();
          this.controleNavegacao.navigateRoot('/produto');
        } else {

          // Finaliza autenticação e apresente mensagem de erro
          loading.dismiss();
          this.apresenta_mensagem(resposta.status);
        }
      })
      .catch(async (erro: any) => {
        console.log(erro);
        loading.dismiss();
        this.apresenta_mensagem(erro?.status);
      });
  }

  async apresenta_mensagem(codigo: number) {
    const mensagem = await this.controleToast.create({
      message: `Falha ao autenticar usuário: código ${codigo}`,
      cssClass: 'ion-text-center',
      duration: 2000
    });
    mensagem.present();
  }

  public alternarSenha(): void {
    this.mostrarSenha = !this.mostrarSenha;
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
