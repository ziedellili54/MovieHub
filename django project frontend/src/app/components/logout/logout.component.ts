import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-logout',
  template: `
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial;">
      <div style="text-align: center;">
        <h2>Logging out...</h2>
        <p>Redirecting to login page...</p>
      </div>
    </div>
  `
})
export class LogoutComponent implements OnInit {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    // Clear everything
    sessionStorage.clear();
    localStorage.clear();
    this.authService.logout();
    
    // Redirect to login
    setTimeout(() => {
      this.router.navigate(['/login']);
    }, 1000);
  }
}
