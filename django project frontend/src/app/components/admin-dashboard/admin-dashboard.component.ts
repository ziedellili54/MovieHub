import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { DashboardComponent } from '../dashboard/dashboard';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-admin-dashboard',
  imports: [FormsModule, CommonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: '../dashboard/dashboard.css',
  standalone: true
})
export class AdminDashboardComponent extends DashboardComponent implements OnInit {
  private adminAuthService = inject(AuthService);

  override ngOnInit() {
    console.log('🔧 AdminDashboardComponent initialized');
    console.log('📋 Session storage role:', sessionStorage.getItem('role'));
    console.log('📋 Is logged in:', this.adminAuthService.isLoggedIn());
    console.log('📋 Is admin:', this.adminAuthService.isAdmin());
    
    // Call parent initialization
    // Parent will handle all the data loading and role checks
    super.ngOnInit();
  }
}
