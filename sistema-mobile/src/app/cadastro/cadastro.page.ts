import { HttpOptions, HttpResponse, CapacitorHttp } from '@capacitor/core';
import { Component } from '@angular/core';
import { LoadingController, NavController, ToastController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';

import { Usuario } from '../home/usuario.models';

@Component({
  selector: 'app-cadastro',
  standalone: false,
  templateUrl: './cadastro.page.html',
  styleUrls: ['./cadastro.page.scss'],
  providers: [Storage],
})
export class CadastroPage {
  public instancia = {
    username: '',
    email: '',
    password1: '',
    password2: '',
  };

  public mostrarSenha = false;
  private storageReady?: Promise<Storage>;

  constructor(
    private controleCarregamento: LoadingController,
    private controleToast: ToastController,
    private controleNavegacao: NavController,
    private storage: Storage,
  ) {}

  private getStorage(): Promise<Storage> {
    if (!this.storageReady) {
      this.storageReady = this.storage.create();
    }

    return this.storageReady;
  }

  public alternarSenha(): void {
    this.mostrarSenha = !this.mostrarSenha;
  }

  public async cadastrarUsuario(): Promise<void> {
    if (this.instancia.password1 !== this.instancia.password2) {
      await this.exibirToast('As senhas nao conferem.');
      return;
    }

    const loading = await this.controleCarregamento.create({
      message: 'Criando conta...',
      spinner: 'crescent',
    });
    await loading.present();

    const options: HttpOptions = {
      headers: { 'Content-Type': 'application/json' },
      url: 'http://127.0.0.1:8000/cadastro-api/',
      data: this.instancia,
    };

    CapacitorHttp.post(options)
      .then(async (resposta: HttpResponse) => {
        if (resposta.status === 201) {
          const usuario: Usuario = Object.assign(new Usuario(), resposta.data);
          const storage = await this.getStorage();
          await storage.set('usuario', usuario);

          await loading.dismiss();
          await this.exibirToast('Conta criada com sucesso!');
          this.controleNavegacao.navigateRoot('/produto');
          return;
        }

        await loading.dismiss();
        await this.exibirToast(resposta.data?.erro || 'Nao foi possivel criar a conta.');
      })
      .catch(async (erro: any) => {
        await loading.dismiss();
        await this.exibirToast(erro?.data?.erro || 'Erro ao criar conta. Verifique o backend.');
      });
  }

  private async exibirToast(mensagem: string): Promise<void> {
    const toast = await this.controleToast.create({
      message: mensagem,
      duration: 2400,
      position: 'bottom',
      color: 'dark',
    });

    await toast.present();
  }
}
