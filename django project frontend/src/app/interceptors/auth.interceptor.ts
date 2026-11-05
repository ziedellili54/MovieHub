/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 AUTH INTERCEPTOR - Automatic JWT Token Injection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Automatically adds JWT token to ALL HTTP requests
    - Intercepts every outgoing HTTP request
    - Adds "Authorization: Bearer <token>" header
    - No need to manually add token in every service method

HOW IT WORKS:
    1. Service makes HTTP request (e.g., http.get('/api/movies/'))
    2. Request passes through this interceptor BEFORE being sent
    3. Interceptor gets token from localStorage
    4. Clones request and adds Authorization header
    5. Sends modified request to backend
    6. Backend validates token (backend/settings.py → JWTAuthentication)

WITHOUT INTERCEPTOR (Manual approach - BAD):
    every method needs:
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    });
    return this.http.get('/api/movies/', { headers });

WITH INTERCEPTOR (Automatic - GOOD):
    just write:
    return this.http.get('/api/movies/');
    
    Token automatically added! ✨

BACKEND CONNECTION:
    - backend/settings.py → REST_FRAMEWORK → JWTAuthentication
    - Django REST Framework validates the token
    - If valid: Request allowed, user identified
    - If invalid/missing: 401 Unauthorized error

CONFIGURED IN:
    app.config.ts - Registered as HTTP interceptor provider

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

import { HttpInterceptorFn } from '@angular/common/http';

/**
 * HTTP Interceptor function - Adds JWT token to all requests
 * 
 * @param req - HttpRequest (the outgoing request)
 * @param next - HttpHandler (passes request to next interceptor or backend)
 * @returns Observable<HttpEvent<unknown>> - The HTTP response
 * 
 * EXECUTION FLOW:
 *   Component/Service calls:
 *     this.http.get('http://localhost:8000/api/movies/')
 *       ↓
 *   Request passes through authInterceptor
 *       ↓
 *   Get token from localStorage: localStorage.getItem('access_token')
 *       ↓
 *   If token exists:
 *     Clone request + Add header: Authorization: Bearer eyJ0eXAiOiJ...
 *       ↓
 *   If no token:
 *     Send request unchanged (for public endpoints like login)
 *       ↓
 *   next(req) → Send request to backend
 *       ↓
 *   Django receives request with Authorization header
 *       ↓
 *   Django validates token (JWTAuthentication)
 *       ↓
 *   If valid: Process request
 *   If invalid: Return 401 Unauthorized
 * 
 * EXAMPLE REQUESTS:
 * 
 *   Example 1: GET movies (logged in)
 *     Original request:
 *       GET http://localhost:8000/api/movies/
 *     
 *     After interceptor:
 *       GET http://localhost:8000/api/movies/
 *       Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
 *     
 *     Backend: ✓ Token valid → Returns movies
 * 
 *   Example 2: POST login (not logged in)
 *     Original request:
 *       POST http://localhost:8000/api/login/
 *       Body: {username: 'john', password: 'pass123'}
 *     
 *     After interceptor:
 *       POST http://localhost:8000/api/login/
 *       Body: {username: 'john', password: 'pass123'}
 *       (No Authorization header - no token in localStorage yet)
 *     
 *     Backend: ✓ Login endpoint doesn't require token
 * 
 *   Example 3: DELETE movie (admin)
 *     Original request:
 *       DELETE http://localhost:8000/api/movies/delete/abc123/
 *     
 *     After interceptor:
 *       DELETE http://localhost:8000/api/movies/delete/abc123/
 *       Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
 *     
 *     Backend: ✓ Token valid + user is admin → Deletes movie
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // ═══════════════════════════════════════════════════════════════════════
  // GET JWT TOKEN FROM LOCAL STORAGE
  // ═══════════════════════════════════════════════════════════════════════
  const token = localStorage.getItem('access_token');
  // Retrieves JWT access token saved during login
  // Example token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  // If not logged in: token = null
  
  // ⚠️ NOTE: Using localStorage instead of sessionStorage
  // WHY? Need to check auth.service.ts - they use sessionStorage there
  // TODO: Should change to sessionStorage.getItem('access_token') for consistency
  
  // ═══════════════════════════════════════════════════════════════════════
  // ADD AUTHORIZATION HEADER IF TOKEN EXISTS
  // ═══════════════════════════════════════════════════════════════════════
  if (token) {
    // TOKEN EXISTS - User is logged in
    
    // Clone the request and add authorization header
    // WHY CLONE? HttpRequest is immutable (can't modify directly)
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
        // Authorization header format: "Bearer <JWT_TOKEN>"
        // "Bearer" is the standard prefix for JWT tokens
        // 
        // Full header example:
        //   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiNTA3Zi4uLg
        //
        // Backend reads this header:
        //   1. Extracts token after "Bearer "
        //   2. Validates signature with SECRET_KEY
        //   3. Decodes payload to get user_id
        //   4. Allows request if valid, rejects if invalid
      }
    });
    // req now has Authorization header attached
  }
  // If no token: req unchanged (for public endpoints: login, register)
  
  // ═══════════════════════════════════════════════════════════════════════
  // PASS REQUEST TO NEXT HANDLER
  // ═══════════════════════════════════════════════════════════════════════
  return next(req);
  // Sends request to:
  //   - Next interceptor (if any)
  //   - OR backend server (if last interceptor)
  //
  // Returns Observable<HttpResponse> to original caller
};

/*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 AUTH INTERCEPTOR SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
    Automatically inject JWT token into ALL HTTP requests

HOW IT WORKS:
    1. Every HTTP request passes through this interceptor
    2. Gets token from localStorage
    3. If token exists: Adds "Authorization: Bearer <token>" header
    4. If no token: Sends request unchanged
    5. Backend validates token

BENEFITS:
    ✓ No need to manually add token to every request
    ✓ Centralized token management
    ✓ Clean service code (just http.get(), http.post(), etc.)
    ✓ Easy to modify token logic in one place

TOKEN STORAGE:
    ⚠️ ISSUE: Interceptor uses localStorage
                auth.service.ts uses sessionStorage
    
    SHOULD BE: sessionStorage.getItem('access_token')
    TO MATCH: auth.service.ts login() method
    
    CURRENT BEHAVIOR: May not work correctly due to mismatch!

BACKEND VALIDATION:
    backend/settings.py:
      REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
          'rest_framework_simplejwt.authentication.JWTAuthentication',
        )
      }
    
    Django REST Framework:
      1. Receives request with Authorization header
      2. Extracts token after "Bearer "
      3. Validates using SIGNING_KEY (SECRET_KEY)
      4. Checks expiration (1 hour for access tokens)
      5. If valid: Allows request, sets request.user
      6. If invalid: Returns 401 Unauthorized

SECURITY:
    - Token sent in Authorization header (NOT in URL or body)
    - HTTPS should be used in production (prevent token theft)
    - Access token expires after 1 hour (short lifetime = more secure)
    - Refresh token can get new access token (7 day lifetime)

EXAMPLE BACKEND ROUTES THAT NEED TOKEN:
    ✓ GET /api/movies/ (ListMoviesView)
    ✓ POST /api/movies/add/ (AddMovieView - admin)
    ✓ DELETE /api/movies/delete/{id}/ (DeleteMovieView - admin)
    ✓ GET /api/favorites/{username}/ (FavoritesView)
    ✓ POST /api/analytics/track/ (TrackActivityView)

EXAMPLE ROUTES THAT DON'T NEED TOKEN:
    ✓ POST /api/login/ (CustomLoginView)
    ✓ POST /api/register/ (CustomRegisterView)
    (These work fine even if token is sent - just ignored)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/
