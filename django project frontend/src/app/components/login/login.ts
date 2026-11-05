import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  private authService = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  credentials = {
    username: '',
    password: ''
  };
  errorMessage = '';
  successMessage = '';
  loading = false;

  onSubmit() {
    const cleanUsername = (this.credentials.username || '').trim();
    const cleanPassword = (this.credentials.password || '').trim();

    if (!cleanUsername || !cleanPassword) {
      this.errorMessage = 'Please enter both username and password.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService.login({ username: cleanUsername, password: cleanPassword }).subscribe({
      next: (response) => {
        const role = response.role;
        if (role === 'admin') {
          this.successMessage = '✓ Admin logged in — redirecting to Admin Dashboard...';
          this.cdr.detectChanges();
          this.router.navigate(['/admin/dashboard']);
          return;
        }
        this.successMessage = '✓ Logged in — redirecting...';
        this.cdr.detectChanges();
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.error || 'Login failed. Please check your credentials.';
        this.cdr.detectChanges();
      }
    });
  }
}
