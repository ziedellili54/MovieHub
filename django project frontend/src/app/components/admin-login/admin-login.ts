import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-admin-login',
  imports: [FormsModule, RouterModule, CommonModule],
  templateUrl: './admin-login.html',
  styleUrl: './admin-login.css'
})
export class AdminLoginComponent {
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
      this.errorMessage = 'Please enter administrator username and password.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService.login({ username: cleanUsername, password: cleanPassword }).subscribe({
      next: (response) => {
        if (response.role !== 'admin') {
          this.loading = false;
          this.errorMessage = 'Access denied. You need Administrator privileges to log in here.';
          this.authService.logout();
          this.cdr.detectChanges();
          return;
        }

        this.successMessage = '✓ Admin Authentication successful — redirecting...';
        this.cdr.detectChanges();
        this.router.navigate(['/admin/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.error || 'Admin authentication failed.';
        this.cdr.detectChanges();
      }
    });
  }
}
