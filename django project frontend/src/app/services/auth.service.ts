/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 AUTHENTICATION SERVICE - User Login/Register/JWT Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Handles all authentication operations for Angular frontend:
    - User login (JWT tokens)
    - User registration
    - Logout (clear tokens)
    - Token storage and retrieval
    - Authentication state checks

BACKEND CONNECTIONS:
    - POST /api/login/ → Django CustomLoginView (accounts/views.py)
    - POST /api/register/ → Django CustomRegisterView (accounts/views.py)

TOKEN STORAGE:
    Uses sessionStorage (NOT localStorage)
    - sessionStorage = data cleared when tab closes
    - localStorage = data persists across sessions
    Why sessionStorage? Better security, each tab independent

USED BY:
    - login.component.ts → Calls login()
    - register.component.ts → Calls register()
    - auth.guard.ts → Calls isLoggedIn()
    - auth.interceptor.ts → Calls getAccessToken()
    - All components → Calls getUsername(), isAdmin()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'  // Singleton service (one instance for entire app)
})
export class AuthService {
  // ═══════════════════════════════════════════════════════════════════════
  // DEPENDENCIES
  // ═══════════════════════════════════════════════════════════════════════
  private http = inject(HttpClient);
  // Angular's HTTP client for making API requests
  // inject() is new Angular way (replaces constructor injection)
  
  private apiUrl = 'http://localhost:8000/api';
  // Django backend base URL
  // Production: Change to actual domain (https://moviehub.com/api)

  // ═══════════════════════════════════════════════════════════════════════
  // METHOD 1: login() - User/Admin Login with JWT
  // ═══════════════════════════════════════════════════════════════════════
  /**
   * Login user and store JWT tokens
   * 
   * @param credentials - {username: string, password: string}
   * @param sessionId - Optional session ID (for analytics)
   * @returns Observable<any> - Response from backend
   * 
   * REQUEST FLOW:
   *   1. User types username/password in login form
   *   2. Component calls: authService.login({username, password})
   *   3. POST /api/login/ with credentials
   *   4. Django validates credentials (accounts/views.py CustomLoginView)
   *   5. Backend checks password: user.check_password()
   *   6. If valid: Returns {access, refresh, username, role}
   *   7. If invalid: Returns 401 error
   * 
   * RESPONSE HANDLING (tap operator):
   *   - tap() = Do something with response without modifying it
   *   - Saves tokens to sessionStorage
   *   - Component can then redirect user to dashboard
   * 
   * USAGE EXAMPLE:
   *   this.authService.login({username: 'john', password: 'pass123'})
   *     .subscribe({
   *       next: (response) => {
   *         console.log('Login successful!', response);
   *         this.router.navigate(['/dashboard']);
   *       },
   *       error: (err) => {
   *         console.error('Login failed', err);
   *         alert('Invalid credentials');
   *       }
   *     });
   */
  login(credentials: any, sessionId?: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/login/`, credentials).pipe(
      tap(response => {
        // tap() = Side effect (save tokens without changing response)
        
        if (response.access) {
          // LOGIN SUCCESSFUL - Save tokens and user info
          
          // Generate or use provided session ID for analytics tracking
          const sid = sessionId || this.generateSessionId();
          
          // ─────────────────────────────────────────────────────────────
          // SAVE TO SESSION STORAGE (cleared when tab closes)
          // ─────────────────────────────────────────────────────────────
          sessionStorage.setItem('session_id', sid);
          // Example: "session_1704438600_abc123"
          // Used by: analytics.service.ts to link activities
          
          sessionStorage.setItem('access_token', response.access);
          // JWT access token (expires in 1 hour)
          // Format: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
          // Used by: auth.interceptor.ts to add to every API request
          
          sessionStorage.setItem('refresh_token', response.refresh);
          // JWT refresh token (expires in 7 days)
          // Used to: Get new access token when old one expires
          
          sessionStorage.setItem('username', response.username || credentials.username);
          // User's username (e.g., "john", "admin")
          // Used by: Display in navbar, analytics tracking
          
          sessionStorage.setItem('role', response.role || 'user');
          // User's role: "user" or "admin"
          // Used by: Show/hide admin features, route guards
        }
      })
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // HELPER METHOD: generateSessionId() - Create unique session ID
  // ═══════════════════════════════════════════════════════════════════════
  /**
   * Generate unique session ID for analytics tracking
   * 
   * @returns string - Unique session identifier
   * 
   * FORMAT: "session_<timestamp>_<random>"
   * Example: "session_1704438600_abc123"
   * 
   * USED BY:
   *   - login() if no sessionId provided
   *   - analytics.service.ts to link user activities to session
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    // Date.now() = Current timestamp (1704438600)
    // Math.random().toString(36) = Random alphanumeric string
    // .substring(2, 9) = Take 7 characters after "0."
  }

  // ═══════════════════════════════════════════════════════════════════════
  // METHOD 2: register() - New User Registration
  // ═══════════════════════════════════════════════════════════════════════
  /**
   * Register new user account
   * 
   * @param userData - {username, email, password, confirm_password}
   * @returns Observable<any> - Response from backend
   * 
   * REQUEST FLOW:
   *   1. User fills registration form
   *   2. Component calls: authService.register(formData)
   *   3. POST /api/register/ with user data
   *   4. Django creates new User in MongoDB (accounts/views.py)
   *   5. Password hashed with: user.set_password()
   *   6. Returns {message, user_id} if successful
   *   7. User can now login with these credentials
   * 
   * BACKEND VALIDATION:
   *   - Username must be unique
   *   - Email must be unique
   *   - Password must match confirm_password
   *   - All required fields provided
   * 
   * USAGE EXAMPLE:
   *   this.authService.register({
   *     username: 'john',
   *     email: 'john@email.com',
   *     password: 'pass123',
   *     confirm_password: 'pass123'
   *   }).subscribe({
   *     next: () => {
   *       alert('Registration successful! Please login.');
   *       this.router.navigate(['/login']);
   *     },
   *     error: (err) => {
   *       alert('Registration failed: ' + err.error.message);
   *     }
   *   });
   */
  register(userData: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/register/`, userData);
    // No tap() needed - registration doesn't automatically log in
    // User must login separately after registration
  }

  // ═══════════════════════════════════════════════════════════════════════
  // METHOD 3: logout() - Clear Session and Tokens
  // ═══════════════════════════════════════════════════════════════════════
  /**
   * Logout user by clearing all session data
   * 
   * WHAT IT DOES:
   *   - Removes all tokens from sessionStorage
   *   - Removes username and role
   *   - Removes session_id
   *   - User becomes "not logged in"
   * 
   * NOTE: No API call to backend
   *   - JWT tokens are stateless (backend doesn't track them)
   *   - Simply removing token = logged out
   *   - If user has token saved elsewhere, it still works until expiration
   * 
   * CALLED BY:
   *   - Logout button click
   *   - Auto-logout on token expiration
   *   - Session timeout
   * 
   * USAGE EXAMPLE:
   *   logout() {
   *     this.authService.logout();
   *     this.router.navigate(['/login']);
   *   }
   */
  logout(): void {
    sessionStorage.removeItem('session_id');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('role');
    // After this, isLoggedIn() returns false
    // auth.guard.ts will redirect to login page
  }

  // ═══════════════════════════════════════════════════════════════════════
  // GETTER METHODS - Retrieve Stored Auth Data
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Get JWT access token from sessionStorage
   * 
   * @returns string | null - JWT token or null if not logged in
   * 
   * USED BY:
   *   - auth.interceptor.ts → Adds to Authorization header
   *   - Components → Check if user is logged in
   * 
   * TOKEN FORMAT:
   *   "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTA3Zj..."
   *   
   * SENT TO BACKEND AS:
   *   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   */
  getAccessToken(): string | null {
    return sessionStorage.getItem('access_token');
  }

  /**
   * Get current user's username
   * 
   * @returns string | null - Username or null if not logged in
   * 
   * USED BY:
   *   - Navbar → Display "Welcome, John"
   *   - Components → Pass to API requests
   *   - Analytics → Track user activities
   * 
   * Example: "john", "admin", "jane"
   */
  getUsername(): string | null {
    return sessionStorage.getItem('username');
  }

  /**
   * Get current user's role
   * 
   * @returns string | null - "user" or "admin" or null
   * 
   * USED BY:
   *   - Components → Show/hide admin features
   *   - Route guards → Protect admin routes
   *   - UI → Change layout based on role
   */
  getUserRole(): string | null {
    return sessionStorage.getItem('role');
  }

  /**
   * Check if current user is admin
   * 
   * @returns boolean - true if admin, false otherwise
   * 
   * USED BY:
   *   - Admin dashboard → Allow access
   *   - Delete buttons → Show only to admins
   *   - User management → Admin-only features
   * 
   * USAGE EXAMPLE:
   *   <button *ngIf="authService.isAdmin()">Delete User</button>
   */
  isAdmin(): boolean {
    return this.getUserRole() === 'admin';
  }

  /**
   * Check if user is logged in
   * 
   * @returns boolean - true if logged in, false otherwise
   * 
   * HOW IT WORKS:
   *   - Checks if access_token exists in sessionStorage
   *   - !! converts to boolean (null → false, string → true)
   * 
   * USED BY:
   *   - auth.guard.ts → Protect routes
   *   - Components → Show login/logout button
   *   - Navbar → Change menu items
   * 
   * LIMITATION:
   *   - Doesn't check if token is valid or expired
   *   - Just checks if token exists
   *   - Backend validates token on each request
   * 
   * USAGE EXAMPLE:
   *   <div *ngIf="authService.isLoggedIn()">
   *     <button (click)="logout()">Logout</button>
   *   </div>
   *   <div *ngIf="!authService.isLoggedIn()">
   *     <a routerLink="/login">Login</a>
   *   </div>
   */
  isLoggedIn(): boolean {
    return !!this.getAccessToken();
    // !! = Convert to boolean
    // null → false (not logged in)
    // "eyJ..." → true (logged in)
  }
}

/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 AUTH SERVICE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METHODS:
    login(credentials) → POST /api/login/ → Save tokens
    register(userData) → POST /api/register/ → Create user
    logout() → Clear sessionStorage → User logged out
    getAccessToken() → Get JWT token
    getUsername() → Get current username
    getUserRole() → Get "user" or "admin"
    isAdmin() → Check if admin
    isLoggedIn() → Check if logged in

STORAGE (sessionStorage):
    - session_id → "session_1704438600_abc123"
    - access_token → "eyJhbGc..." (JWT, expires 1h)
    - refresh_token → "eyJhbGc..." (JWT, expires 7d)
    - username → "john"
    - role → "user" or "admin"

AUTHENTICATION FLOW:
    1. User enters credentials
    2. login() sends POST /api/login/
    3. Django validates (accounts/views.py)
    4. Returns JWT tokens
    5. Saved to sessionStorage
    6. auth.interceptor.ts adds token to all requests
    7. auth.guard.ts protects routes
    8. Backend validates token on each request

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/
