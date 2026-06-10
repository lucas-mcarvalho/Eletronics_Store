import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';

import { EsqueciSenhaPage } from './esqueci-senha.page';
import { EsqueciSenhaPageRoutingModule } from './esqueci-senha-routing.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, EsqueciSenhaPageRoutingModule],
  declarations: [EsqueciSenhaPage],
})
export class EsqueciSenhaPageModule {}
