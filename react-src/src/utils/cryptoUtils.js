/**
 * Client-side encryption utilities for React application
 */

/**
 * Derive an encryption key from a password
 * @param {string} password - The user's password
 * @param {Uint8Array} salt - Optional salt (if not provided, one will be generated)
 * @returns {Promise<{key: CryptoKey, salt: Uint8Array}>} The derived key and salt
 */
export async function deriveKeyFromPassword(password, salt = null) {
  // Generate salt if not provided
  if (!salt) {
    salt = window.crypto.getRandomValues(new Uint8Array(16));
  }
  
  // Convert password to buffer
  const encoder = new TextEncoder();
  const passwordBuffer = encoder.encode(password);
  
  // Import key material
  const keyMaterial = await window.crypto.subtle.importKey(
    'raw', 
    passwordBuffer,
    { name: 'PBKDF2' },
    false, 
    ['deriveBits', 'deriveKey']
  );
  
  // Derive the actual key
  const derivedKey = await window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    true, // extractable
    ['encrypt', 'decrypt']
  );
  
  return { key: derivedKey, salt };
}

/**
 * Encrypt file data with a password
 * @param {ArrayBuffer} fileData - The file data to encrypt
 * @param {string} password - The encryption password
 * @returns {Promise<{encryptedData: ArrayBuffer, salt: Uint8Array, iv: Uint8Array}>}
 */
export async function encryptFileWithPassword(fileData, password) {
  // Generate initialization vector for AES-GCM
  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  
  // Derive key from password
  const { key, salt } = await deriveKeyFromPassword(password);
  
  // Encrypt the file data
  const encryptedData = await window.crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv
    },
    key,
    fileData
  );
  
  return { encryptedData, salt, iv };
}

/**
 * Decrypt file data with a password
 * @param {ArrayBuffer} encryptedData - The encrypted file data
 * @param {string} password - The decryption password
 * @param {Uint8Array} salt - The salt used for key derivation
 * @param {Uint8Array} iv - The initialization vector used for encryption
 * @returns {Promise<ArrayBuffer>} The decrypted file data
 */
export async function decryptFileWithPassword(encryptedData, password, salt, iv) {
  // Derive key from password and salt
  const { key } = await deriveKeyFromPassword(password, salt);
  
  // Decrypt the data
  try {
    const decryptedData = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv
      },
      key,
      encryptedData
    );
    
    return decryptedData;
  } catch (error) {
    console.error('Decryption failed:', error);
    throw new Error('Incorrect password or corrupted file data');
  }
}

/**
 * Convert ArrayBuffer to Base64 string
 * @param {ArrayBuffer} buffer - The buffer to convert
 * @returns {string} Base64-encoded string
 */
export function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Convert Base64 string to ArrayBuffer
 * @param {string} base64 - The Base64 string to convert
 * @returns {ArrayBuffer} The decoded ArrayBuffer
 */
export function base64ToArrayBuffer(base64) {
  const binaryString = window.atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
} 