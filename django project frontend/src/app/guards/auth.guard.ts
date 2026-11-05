/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ AUTH GUARD - Route Protection (Prevents Unauthorized Access)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Protects routes from unauthorized access
    - Checks if user is logged in before allowing access to route
    - Redirects to login page if not authenticated
    - Different redirection for admin vs user routes

HOW IT WORKS:
    1. User tries to navigate to protected route (e.g., /dashboard)
    2. Angular calls this guard BEFORE activating route
    3. Guard checks: Is user logged in? (authService.isLoggedIn())
    4. If YES: Allow access (return true)
    5. If NO: Redirect to login page (return false)

USED IN:
    app.routes.ts - Applied to routes that need authentication
    
    Example:
    {
      path: 'dashboard',
      component: DashboardComponent,
      canActivate: [authGuard]  ← This guard protects the route
    }

AUTHENTICATION CHECK:
    - Uses AuthService.isLoggedIn()
    - Checks if JWT access token exists in sessionStorage
    - Does NOT validate token (backend does that on API calls)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Route guard function - Protects routes from unauthorized access
 * 
 * @param route - ActivatedRouteSnapshot (contains route info)
 * @param state - RouterStateSnapshot (contains URL being accessed)
 * @returns boolean - true = allow access, false = block access
 * 
 * EXECUTION FLOW:
 *   User navigates to /dashboard
 *     ↓
 *   Angular checks: Does route have canActivate: [authGuard]?
 *     ↓
 *   YES → Call authGuard(route, state)
 *     ↓
 *   authGuard checks: authService.isLoggedIn()?
 *     ↓
 *   If TRUE → return true → Angular activates route → Show dashboard
 *   If FALSE → redirect to login → return false → Block route
 * 
 * EXAMPLE SCENARIOS:
 * 
 *   Scenario 1: Logged in user navigates to /dashboard
 *     1. authService.isLoggedIn() → true (has token)
 *     2. return true
 *     3. Angular shows dashboard
 * 
 *   Scenario 2: Not logged in user tries /dashboard
 *     1. authService.isLoggedIn() → false (no token)
 *     2. router.navigate(['/login'])
 *     3. return false
 *     4. User redirected to login page
 * 
 *   Scenario 3: Not logged in user tries /admin/dashboard
 *     1. authService.isLoggedIn() → false
 *     2. state.url.includes('/admin') → true
 *     3. router.navigate(['/admin/login'])  ← Different login page!
 *     4. return false
 */
export const authGuard: CanActivateFn = (route, state) => {
  // ═══════════════════════════════════════════════════════════════════════
  // INJECT DEPENDENCIES
  // ═══════════════════════════════════════════════════════════════════════
  const authService = inject(AuthService);
  // Get AuthService instance to check authentication status
  
  const router = inject(Router);
  // Get Router instance to redirect if not authenticated

  // ═══════════════════════════════════════════════════════════════════════
  // CHECK AUTHENTICATION
  // ═══════════════════════════════════════════════════════════════════════
  if (authService.isLoggedIn()) {
    // USER IS LOGGED IN
    // ✓ Has valid access token in sessionStorage
    // ✓ Allow access to protected route
    return true;
    // Angular will activate the route and show the component
  }

  // ═══════════════════════════════════════════════════════════════════════
  // USER NOT LOGGED IN - REDIRECT TO LOGIN
  // ═══════════════════════════════════════════════════════════════════════
  // state.url = The URL user is trying to access
  // Example: "/dashboard", "/admin/dashboard", "/profile"
  
  if (state.url.includes('/admin')) {
    // ADMIN ROUTE - Redirect to admin login page
    // Example: User tries /admin/dashboard → Redirect to /admin/login
    router.navigate(['/admin/login']);
  } else {
    // USER ROUTE - Redirect to regular login page
    // Example: User tries /dashboard → Redirect to /login
    router.navigate(['/login']);
  }
  
  // Return false = Block access to requested route
  return false;
};

/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 AUTH GUARD SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Prevent unauthorized users from accessing protected routes

HOW TO USE IN ROUTES:
    {
      path: 'dashboard',
      component: DashboardComponent,
      canActivate: [authGuard]  ← Add this line
    }

PROTECTED ROUTES EXAMPLES:
    ✓ /dashboard → Requires login
    ✓ /profile → Requires login
    ✓ /favorites → Requires login
    ✓ /admin/dashboard → Requires admin login
    ✓ /admin/users → Requires admin login

UNPROTECTED ROUTES (No guard):
    ✓ /login → Anyone can access
    ✓ /register → Anyone can access
    ✓ / (home) → Anyone can access

LIMITATIONS:
    - Only checks if token EXISTS
    - Doesn't validate if token is VALID or EXPIRED
    - Backend validates token on every API request
    - If token expired: API returns 401, frontend handles it

SECURITY:
    - Frontend protection only (can be bypassed by savvy users)
    - Real security happens on backend (JWT validation)
    - This just improves UX (don't show protected pages to non-users)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/
