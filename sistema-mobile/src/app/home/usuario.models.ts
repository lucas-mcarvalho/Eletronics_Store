export class Usuario {
    public id: number;
    public username: string;
    public email: string;
    public token: string;
    public is_staff: boolean;

    constructor() {
        this.id = 0;
        this.username = '';
        this.email = '';
        this.token = '';
        this.is_staff = false;
    }
}
