import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class TokenManager:
    """
    Manages JWT token generation, validation, and refresh operations.
    """
    
    def __init__(self, app=None):
        """
        Initialize the TokenManager.
        
        Args:
            app: Optional Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the TokenManager with a Flask application.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        # Set default config values if not already set
        app.config.setdefault('JWT_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', 30 * 60)  # 30 minutes
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', 7 * 24 * 60 * 60)  # 7 days
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        
        logger.info("TokenManager initialized")
    
    def generate_access_token(self, file_uuid=None, admin=False):
        """
        Generate a short-lived access token.
        
        Args:
            file_uuid: Optional UUID of file for download authorization
            admin: Boolean indicating if this is an admin token
            
        Returns:
            str: JWT access token
        """
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                seconds=self.app.config['JWT_ACCESS_TOKEN_EXPIRES']
            ),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        
        # Add specific claims based on token purpose
        if file_uuid:
            payload['file_uuid'] = file_uuid
            
        if admin:
            payload['admin'] = True
        
        logger.info(f"Generating access token: {payload}")
        
        return jwt.encode(
            payload,
            self.app.config['JWT_SECRET_KEY'],
            algorithm=self.app.config['JWT_ALGORITHM']
        )
    
    def generate_refresh_token(self):
        """
        Generate a long-lived refresh token.
        
        Returns:
            str: JWT refresh token
        """
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                seconds=self.app.config['JWT_REFRESH_TOKEN_EXPIRES']
            ),
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh'
        }
        
        logger.info("Generating refresh token")
        
        return jwt.encode(
            payload,
            self.app.config['JWT_SECRET_KEY'],
            algorithm=self.app.config['JWT_ALGORITHM']
        )
    
    def generate_download_token(self, file_uuid, password_verified=False, file_type=None):
        """
        Generate a token specifically for file download.
        
        Args:
            file_uuid: UUID of file for download
            password_verified: Boolean indicating if password verification has been completed
            file_type: Optional file type information
            
        Returns:
            str: JWT download token with limited lifetime
        """
        # Download tokens are valid for only 10 minutes
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            'iat': datetime.datetime.utcnow(),
            'type': 'download',
            'file_uuid': file_uuid,
            'password_verified': password_verified
        }
        
        if file_type:
            payload['file_type'] = file_type
            
        logger.info(f"Generating download token for file: {file_uuid}")
        
        return jwt.encode(
            payload,
            self.app.config['JWT_SECRET_KEY'],
            algorithm=self.app.config['JWT_ALGORITHM']
        )
    
    def verify_token(self, token, token_type=None):
        """
        Verify a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Optional type of token to verify ('access', 'refresh', 'download')
            
        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.app.config['JWT_SECRET_KEY'],
                algorithms=[self.app.config['JWT_ALGORITHM']]
            )
            
            # If token_type is specified, verify that the token matches the expected type
            if token_type and payload.get('type') != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
                return None
                
            logger.info(f"Token verified successfully: {payload.get('type')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

# Decorators for protecting routes

def token_required(token_manager):
    """
    Decorator to protect routes with JWT access token.
    
    Args:
        token_manager: TokenManager instance
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            if not token:
                logger.warning("No token provided")
                return jsonify({'success': False, 'message': 'Token is missing'}), 401
            
            # Verify token
            payload = token_manager.verify_token(token, 'access')
            if not payload:
                logger.warning("Invalid token")
                return jsonify({'success': False, 'message': 'Token is invalid or expired'}), 401
            
            # Add payload to request for access in the route
            request.token_payload = payload
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_token_required(token_manager):
    """
    Decorator to protect admin routes with JWT access token having admin privileges.
    
    Args:
        token_manager: TokenManager instance
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            if not token:
                logger.warning("No admin token provided")
                return jsonify({'success': False, 'message': 'Admin token is missing'}), 401
            
            # Verify token
            payload = token_manager.verify_token(token, 'access')
            if not payload:
                logger.warning("Invalid admin token")
                return jsonify({'success': False, 'message': 'Admin token is invalid or expired'}), 401
            
            # Check admin privilege
            if not payload.get('admin', False):
                logger.warning("Non-admin token used for admin route")
                return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
            
            # Add payload to request for access in the route
            request.token_payload = payload
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def download_token_required(token_manager):
    """
    Decorator to protect download routes with JWT download token.
    
    Args:
        token_manager: TokenManager instance
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from query parameter or header
            token = request.args.get('token')
            
            if not token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                logger.warning("No download token provided")
                return jsonify({'success': False, 'message': 'Download token is missing'}), 401
            
            # Verify token
            payload = token_manager.verify_token(token, 'download')
            if not payload:
                logger.warning("Invalid download token")
                return jsonify({'success': False, 'message': 'Download token is invalid or expired'}), 401
            
            # Check password verification
            if not payload.get('password_verified', False):
                logger.warning("Password not verified for download")
                return jsonify({'success': False, 'message': 'Password verification required'}), 403
            
            # Check file_uuid matches the one in URL
            file_uuid = kwargs.get('file_uuid')
            if file_uuid and file_uuid != payload.get('file_uuid'):
                logger.warning(f"File UUID mismatch. URL: {file_uuid}, Token: {payload.get('file_uuid')}")
                return jsonify({'success': False, 'message': 'Token is not valid for this file'}), 403
            
            # Add payload to request for access in the route
            request.token_payload = payload
            
            return f(*args, **kwargs)
        return decorated
    return decorator 