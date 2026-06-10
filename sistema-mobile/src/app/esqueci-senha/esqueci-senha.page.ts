import { Component } from '@angular/core';
import { LoadingController, NavController, ToastController } from '@ionic/angular';

import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-esqueci-senha',
  templateUrl: './esqueci-senha.page.html',
  styleUrls: ['./esqueci-senha.page.scss'],
  standalone: false,
})
export class EsqueciSenhaPage {
  public email = '';

  constructor(
    private api: ApiService,
    private loadingController: LoadingController,
    private toastController: ToastController,
    private navController: NavController,
  ) {}

  public async enviar(): Promise<void> {
    if (!this.email.trim()) {
      await this.toast('Informe seu e-mail.');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Enviando...',
      spinner: 'crescent',
    });
    await loading.present();

    try {
      const resposta = await this.api.post('/senha/esqueci-api/', { email: this.email.trim() });

      if (resposta.status === 200) {
        await this.toast('Se o e-mail existir, enviaremos as instrucoes.');
        this.navController.navigateRoot('/home');
        return;
      }

      await this.toast(resposta.data?.erro || 'Nao foi possivel enviar o e-mail.');
    } catch (error) {
      await this.toast('Erro ao enviar e-mail. Verifique o backend.');
    } finally {
      await loading.dismiss();
    }
  }

  private async toast(message: string): Promise<void> {
    const toast = await this.toastController.create({
      message,
      duration: 2400,
      position: 'bottom',
      color: 'dark',
    });

    await toast.present();
  }
}
