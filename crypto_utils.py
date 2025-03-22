import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Set a default encryption key from environment or generate one
def get_master_key():
    """Get or generate a master encryption key"""
    # Try to get from environment
    key = os.environ.get('MASTER_ENCRYPTION_KEY')
    
    if not key:
        # Generate a key if not provided
        key = Fernet.generate_key()
        print(f"WARNING: Generated new master encryption key: {key.decode()}")
        print("Set this in your environment variables to ensure data consistency")
        return key
    
    # If it's a string, ensure it's base64 encoded with the right length
    if isinstance(key, str):
        try:
            # If it's already a valid base64 key, this will succeed
            decoded = base64.urlsafe_b64decode(key)
            if len(decoded) == 32:
                return key.encode()
                
            # If it's not 32 bytes, re-encode it properly
            print(f"WARNING: Key length is not 32 bytes, regenerating proper key")
            # Pad or truncate to 32 bytes
            decoded = decoded.ljust(32, b'0')[:32]
            # Re-encode to base64
            key = base64.urlsafe_b64encode(decoded)
            return key
        except Exception as e:
            print(f"WARNING: Invalid base64 key format: {e}, regenerating proper key")
            # If not a valid base64 string, convert to bytes and pad to 32 bytes
            key_bytes = key.encode('utf-8')
            # Pad or truncate to 32 bytes
            key_bytes = key_bytes.ljust(32, b'0')[:32]
            # Encode to base64 for Fernet
            key = base64.urlsafe_b64encode(key_bytes)
            return key
    
    # If already bytes, ensure it's a valid Fernet key
    try:
        # If it's bytes but not a valid key
        if isinstance(key, bytes):
            # Verify if it's already a valid Fernet key
            try:
                Fernet(key)
                return key
            except Exception:
                # If not, try to ensure it's properly encoded
                decoded = base64.urlsafe_b64decode(key)
                if len(decoded) != 32:
                    decoded = decoded.ljust(32, b'0')[:32]
                    key = base64.urlsafe_b64encode(decoded)
                else:
                    # If it was 32 bytes but not valid, re-encode
                    key = base64.urlsafe_b64encode(decoded)
                # Final verification
                try:
                    Fernet(key)
                    return key
                except Exception:
                    # If still failing, generate a new key
                    print(f"WARNING: Could not create valid key, generating new one")
                    key = Fernet.generate_key()
                    return key
    except Exception as e:
        # Generate a new valid key
        print(f"WARNING: Invalid key format: {str(e)}, generating a new key")
        key = Fernet.generate_key()
        return key
    
    # Final validation
    try:
        Fernet(key)
        return key
    except Exception:
        # Last resort - generate a brand new key
        print(f"WARNING: Final validation failed, generating a new key")
        return Fernet.generate_key()

# Encryption for database fields
def encrypt_db_field(data, master_key=None):
    """Encrypt a database field using Fernet symmetric encryption"""
    if not data:
        return None
    
    # Use provided key or get master key
    key = master_key or get_master_key()
    f = Fernet(key)
    
    # Return encrypted data
    return f.encrypt(data.encode()).decode() if isinstance(data, str) else f.encrypt(data)

def decrypt_db_field(encrypted_data, master_key=None):
    """Decrypt a database field encrypted with Fernet"""
    if not encrypted_data:
        print("Warning: Attempt to decrypt None or empty data")
        return None
    
    # Use provided key or get master key
    try:
        key = master_key or get_master_key()
        f = Fernet(key)
        
        # Return decrypted data
        try:
            if isinstance(encrypted_data, str):
                # Ensure proper encoding for string data
                try:
                    decrypted = f.decrypt(encrypted_data.encode())
                    return decrypted.decode()
                except UnicodeDecodeError:
                    # If we can't decode as string, return bytes
                    return f.decrypt(encrypted_data.encode())
            else:
                # For bytes data
                return f.decrypt(encrypted_data)
        except Exception as e:
            print(f"Decryption error: {e}. Returning original data as fallback.")
            # As a fallback for corrupted data, return the original
            if isinstance(encrypted_data, str):
                return encrypted_data
            elif isinstance(encrypted_data, bytes):
                try:
                    return encrypted_data.decode()
                except:
                    return str(encrypted_data)
            return str(encrypted_data)
    except Exception as e:
        print(f"Key initialization error in decrypt_db_field: {e}")
        # Return original data as fallback
        if isinstance(encrypted_data, str):
            return encrypted_data
        elif isinstance(encrypted_data, bytes):
            try:
                return encrypted_data.decode()
            except:
                return str(encrypted_data)
        return str(encrypted_data)

# File encryption/decryption
def encrypt_file(file_path, encrypted_path=None, key=None):
    """Encrypt a file with Fernet symmetric encryption"""
    try:
        # Use provided key or get master key
        encryption_key = key or get_master_key()
        f = Fernet(encryption_key)
        
        # Default output path
        output_path = encrypted_path or f"{file_path}.encrypted"
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = f.encrypt(file_data)
        
        with open(output_path, 'wb') as file:
            file.write(encrypted_data)
            
        # Verify the file was written
        if not os.path.exists(output_path):
            raise IOError(f"Failed to write encrypted file to {output_path}")
            
        print(f"Successfully encrypted {file_path} to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in encrypt_file: {e}")
        # If an encryption error occurs, return the original file path
        # This allows the system to continue working even if encryption fails
        return file_path

def decrypt_file(encrypted_path, output_path=None, key=None):
    """Decrypt a file encrypted with Fernet"""
    try:
        # Use provided key or get master key
        encryption_key = key or get_master_key()
        f = Fernet(encryption_key)
        
        # Default output path
        if not output_path:
            output_path = encrypted_path.replace('.encrypted', '') if encrypted_path.endswith('.encrypted') else f"{encrypted_path}.decrypted"
        
        with open(encrypted_path, 'rb') as file:
            encrypted_data = file.read()
        
        try:
            decrypted_data = f.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
                
            print(f"Successfully decrypted {encrypted_path} to {output_path}")
            return output_path
        except Exception as e:
            print(f"File decryption error: {e}")
            
            # If decryption fails, check if we can return the original
            if os.path.exists(encrypted_path) and not encrypted_path.endswith('.encrypted'):
                print(f"Decryption failed, returning original file path: {encrypted_path}")
                # If this wasn't actually encrypted, copy it to output path
                if output_path and output_path != encrypted_path:
                    import shutil
                    shutil.copy2(encrypted_path, output_path)
                    return output_path
                return encrypted_path
            return None
    except Exception as e:
        print(f"Error in decrypt_file: {e}")
        return None

# Password-based encryption for client-side operations
def derive_key_from_password(password, salt=None):
    """Derive an encryption key from a password using PBKDF2"""
    if not salt:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_with_password(data, password, salt=None):
    """Encrypt data using a password-derived key"""
    key, salt = derive_key_from_password(password, salt)
    f = Fernet(key)
    
    encrypted_data = f.encrypt(data if isinstance(data, bytes) else data.encode())
    return encrypted_data, salt

def decrypt_with_password(encrypted_data, password, salt):
    """Decrypt data using a password-derived key"""
    try:
        key, _ = derive_key_from_password(password, salt)
        f = Fernet(key)
        
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        print(f"Password-based decryption error: {str(e)}")
        # Re-raise the exception to indicate decryption failure
        raise Exception(f"Decryption failed: {str(e)}") 