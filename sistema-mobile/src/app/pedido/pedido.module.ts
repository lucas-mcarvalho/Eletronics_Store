import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';

import { PedidoPage } from './pedido.page';
import { PedidoPageRoutingModule } from './pedido-routing.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, PedidoPageRoutingModule],
  declarations: [PedidoPage],
})
export class PedidoPageModule {}
