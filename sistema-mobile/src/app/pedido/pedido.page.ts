import { Component, OnInit } from '@angular/core';
import { LoadingController, NavController, ToastController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';

import { Usuario } from '../home/usuario.models';
import { ApiService } from '../services/api.service';
import { Pedido } from './pedido.model';

@Component({
  selector: 'app-pedido',
  templateUrl: './pedido.page.html',
  styleUrls: ['./pedido.page.scss'],
  providers: [Storage],
  standalone: false,
})
export class PedidoPage implements OnInit {
  public usuario: Usuario = new Usuario();
  public pedidos: Pedido[] = [];
  public carregando = false;
  private storageReady?: Promise<Storage>;

  constructor(
    private api: ApiService,
    private storage: Storage,
    private loadingController: LoadingController,
    private toastController: ToastController,
    private navController: NavController,
  ) {}

  async ngOnInit(): Promise<void> {
    const storage = await this.getStorage();
    const registro = await storage.get('usuario');

    if (!registro) {
      this.navController.navigateRoot('/home');
      return;
    }

    this.usuario = Object.assign(new Usuario(), registro);
    await this.carregarPedidos();
  }

  private getStorage(): Promise<Storage> {
    if (!this.storageReady) {
      this.storageReady = this.storage.create();
    }

    return this.storageReady;
  }

  public async carregarPedidos(event?: CustomEvent): Promise<void> {
    this.carregando = true;
    const loading = await this.loadingController.create({
      message: 'Carregando pedidos...',
      spinner: 'crescent',
    });
    await loading.present();

    try {
      const resposta = await this.api.get('/pedidos/api/listar/', this.usuario);

      if (resposta.status === 200 && Array.isArray(resposta.data)) {
        this.pedidos = resposta.data.map((pedido: any) => Object.assign(new Pedido(), pedido));
      } else {
        await this.toast('Nao foi possivel carregar os pedidos.');
      }
    } catch (error) {
      await this.toast('Erro ao carregar pedidos. Verifique o backend.');
    } finally {
      this.carregando = false;
      await loading.dismiss();

      if (event?.target && 'complete' in event.target) {
        (event.target as HTMLIonRefresherElement).complete();
      }
    }
  }

  public formatarValor(valor: string): string {
    return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  public voltar(): void {
    this.navController.navigateBack('/produto');
  }

  private async toast(message: string): Promise<void> {
    const toast = await this.toastController.create({
      message,
      duration: 2200,
      position: 'bottom',
      color: 'dark',
    });

    await toast.present();
  }
}
