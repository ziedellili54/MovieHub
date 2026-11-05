import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { AdminLoginComponent } from './components/admin-login/admin-login';
import { RegisterComponent } from './components/register/register';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password';
import { DashboardComponent } from './components/dashboard/dashboard';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { ApiBrowserComponent } from './components/api-browser/api-browser';
import { LogoutComponent } from './components/logout/logout.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'admin/login', component: AdminLoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: 'logout', component: LogoutComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'admin/dashboard', component: AdminDashboardComponent, canActivate: [authGuard] },
  { path: 'api-browser', component: ApiBrowserComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'login' }
];

