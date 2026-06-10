import { Injectable } from '@angular/core';
import { CapacitorHttp, HttpOptions, HttpResponse } from '@capacitor/core';

import { environment } from '../../environments/environment';
import { Usuario } from '../home/usuario.models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  public baseUrl = environment.apiUrl;

  public url(path: string): string {
    return `${this.baseUrl}${path.startsWith('/') ? '' : '/'}${path}`;
  }

  public headers(usuario?: Usuario): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (usuario?.token) {
      headers['Authorization'] = `Token ${usuario.token}`;
    }

    return headers;
  }

  public get(path: string, usuario?: Usuario): Promise<HttpResponse> {
    const options: HttpOptions = {
      headers: this.headers(usuario),
      url: this.url(path),
    };

    return CapacitorHttp.get(options);
  }

  public post(path: string, data: unknown, usuario?: Usuario): Promise<HttpResponse> {
    const options: HttpOptions = {
      headers: this.headers(usuario),
      url: this.url(path),
      data,
    };

    return CapacitorHttp.post(options);
  }
}
