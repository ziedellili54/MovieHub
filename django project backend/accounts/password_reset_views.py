"""
Password Reset with Email Verification Code
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import User
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from datetime import datetime, timedelta
from pymongo import MongoClient
import os

# Store verification codes temporarily (in production, use Redis or database)
verification_codes = {}

class RequestPasswordResetView(APIView):
    """
    Step 1: User enters email, receives verification code
    POST /api/password-reset/request/
    Body: { "email": "user@example.com" }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip()
        
        if not email:
            return Response({
                'success': False,
                'error': 'Email requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security)
            return Response({
                'success': True,
                'message': 'Si un compte existe avec cet email, un code de vérification a été envoyé.'
            })
        
        # Generate 6-digit verification code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Store code with expiry (10 minutes)
        verification_codes[email] = {
            'code': code,
            'expires_at': datetime.now() + timedelta(minutes=10),
            'username': user.username
        }
        
        # Send email with verification code
        try:
            subject = 'Code de réinitialisation - MovieHub'
            message = f"""
Bonjour {user.username},

Vous avez demandé la réinitialisation de votre mot de passe.

Votre code de vérification est : {code}

Ce code expirera dans 10 minutes.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe MovieHub
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            print(f"✅ Verification code sent to {email}: {code}")
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return Response({
                'success': False,
                'error': 'Erreur lors de l\'envoi de l\'email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': 'Code de vérification envoyé à votre email'
        })


class VerifyCodeView(APIView):
    """
    Step 2: Verify the code entered by user
    POST /api/password-reset/verify-code/
    Body: { "email": "user@example.com", "code": "123456" }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip()
        code = request.data.get('code', '').strip()
        
        if not email or not code:
            return Response({
                'success': False,
                'error': 'Email et code requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if code exists and is valid
        if email not in verification_codes:
            return Response({
                'success': False,
                'error': 'Code invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        stored_data = verification_codes[email]
        
        # Check if code has expired
        if datetime.now() > stored_data['expires_at']:
            del verification_codes[email]
            return Response({
                'success': False,
                'error': 'Code expiré. Demandez un nouveau code.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if code matches
        if stored_data['code'] != code:
            return Response({
                'success': False,
                'error': 'Code incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Code vérifié avec succès',
            'username': stored_data['username']
        })


class ResetPasswordView(APIView):
    """
    Step 3: Reset password after code verification
    POST /api/password-reset/reset/
    Body: { "email": "user@example.com", "code": "123456", "new_password": "newpass123" }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip()
        code = request.data.get('code', '').strip()
        new_password = request.data.get('new_password', '').strip()
        
        if not email or not code or not new_password:
            return Response({
                'success': False,
                'error': 'Tous les champs sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(new_password) < 8:
            return Response({
                'success': False,
                'error': 'Le mot de passe doit contenir au moins 8 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify code again
        if email not in verification_codes:
            return Response({
                'success': False,
                'error': 'Code invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        stored_data = verification_codes[email]
        
        # Check expiry
        if datetime.now() > stored_data['expires_at']:
            del verification_codes[email]
            return Response({
                'success': False,
                'error': 'Code expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check code
        if stored_data['code'] != code:
            return Response({
                'success': False,
                'error': 'Code incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update password in MongoDB
        try:
            user = User.objects.get(email=email)
            
            # IMPORTANT: Hash the password before storing!
            user.set_password(new_password)
            user.save()
            
            # Remove used code
            del verification_codes[email]
            
            print(f"✅ Password reset successful for {email}")
            
            return Response({
                'success': True,
                'message': 'Mot de passe réinitialisé avec succès'
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la réinitialisation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
