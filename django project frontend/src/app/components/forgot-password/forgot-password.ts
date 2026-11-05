import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-forgot-password',
  imports: [FormsModule, CommonModule, RouterLink],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.css'
})
export class ForgotPasswordComponent {
  private http = inject(HttpClient);
  private router = inject(Router);
  
  step: 'email' | 'code' | 'password' = 'email';
  
  email = '';
  code = '';
  newPassword = '';
  confirmPassword = '';
  
  loading = false;
  successMessage = '';
  errorMessage = '';
  
  private apiUrl = 'http://localhost:8000/api/password-reset';

  onRequestCode() {
    if (!this.email.trim()) {
      this.errorMessage = 'Veuillez entrer votre email';
      return;
    }
    
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    
    this.http.post(`${this.apiUrl}/request/`, { email: this.email }).subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.successMessage = res.message;
          this.step = 'code';
        } else {
          this.errorMessage = res.error || 'Erreur lors de l\'envoi du code';
        }
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.error || 'Erreur de connexion au serveur';
      }
    });
  }

  onVerifyCode() {
    if (!this.code.trim()) {
      this.errorMessage = 'Veuillez entrer le code de vérification';
      return;
    }
    
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    
    this.http.post(`${this.apiUrl}/verify-code/`, { 
      email: this.email, 
      code: this.code 
    }).subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.successMessage = res.message;
          this.step = 'password';
        } else {
          this.errorMessage = res.error || 'Code invalide';
        }
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.error || 'Code invalide ou expiré';
      }
    });
  }

  onResetPassword() {
    if (!this.newPassword.trim() || !this.confirmPassword.trim()) {
      this.errorMessage = 'Veuillez remplir tous les champs';
      return;
    }
    
    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'Les mots de passe ne correspondent pas';
      return;
    }
    
    if (this.newPassword.length < 8) {
      this.errorMessage = 'Le mot de passe doit contenir au moins 8 caractères';
      return;
    }
    
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    
    this.http.post(`${this.apiUrl}/reset/`, { 
      email: this.email, 
      code: this.code,
      new_password: this.newPassword
    }).subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.successMessage = res.message + ' - Redirection vers la page de connexion...';
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 2000);
        } else {
          this.errorMessage = res.error || 'Erreur lors de la réinitialisation';
        }
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.error || 'Erreur lors de la réinitialisation';
      }
    });
  }

  goBack() {
    if (this.step === 'code') {
      this.step = 'email';
      this.code = '';
    } else if (this.step === 'password') {
      this.step = 'code';
      this.newPassword = '';
      this.confirmPassword = '';
    }
    this.errorMessage = '';
    this.successMessage = '';
  }
}
