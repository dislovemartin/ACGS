"""
crypto_service.py

This module provides cryptographic utilities for the AlphaEvolve Governance System,
such as hashing for data integrity, digital signatures for authenticity, and
potentially encryption for confidentiality of sensitive policy elements.

Classes:
    CryptoService: Provides cryptographic operations.

Functions:
    generate_key_pair: Generates an RSA public/private key pair.
    hash_data: Hashes data using SHA-256.
"""

 import hashlib
-from os import  # For API keys or secure paths, if needed in future
+from typing import Optional

 # For digital signatures - requires 'cryptography' library
 # Ensure 'cryptography' is in requirements.txt
 try:
     from cryptography.hazmat.primitives import hashes
     from cryptography.hazmat.primitives.asymmetric import rsa, padding
     from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    # Define dummy classes or functions if cryptography is not available
    # This allows the module to be imported but will raise errors on use.
    class rsa:
        @staticmethod
        def generate_private_key(public_exponent, key_size): pass
    class padding:
        @staticmethod
        def PSS(mgf, salt_length): pass
        @staticmethod
        def MGF1(algorithm): pass
    class hashes:
        class SHA256: pass
    class serialization:
        class Encoding:
            PEM = "pem"
        class PrivateFormat:
            PKCS8 = "pkcs8"
        class PublicFormat:
            SubjectPublicKeyInfo = "spki"
        @staticmethod
        def NoEncryption(): pass


from alphaevolve_gs_engine.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

def hash_data(data: str, algorithm: str = "sha256") -> str:
    """
    Hashes the given string data using the specified algorithm.

    Args:
        data (str): The string data to hash.
        algorithm (str): The hashing algorithm to use (default: "sha256").
                         Supported: "sha256", "sha512", "md5" (not recommended for security).

    Returns:
        str: The hexadecimal representation of the hash.
    
    Raises:
        ValueError: If an unsupported algorithm is specified.
    """
    data_bytes = data.encode('utf-8')
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    elif algorithm == "md5": # MD5 is generally not recommended for new security uses
        logger.warning("MD5 is used for hashing, which is not secure for many applications.")
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
    
    hasher.update(data_bytes)
    return hasher.hexdigest()


class CryptoService:
    """
    Provides services for cryptographic operations like signing and verification.
    Requires the 'cryptography' library.
    """

    def __init__(self, private_key_pem: Optional[bytes] = None, public_key_pem: Optional[bytes] = None):
        """
        Initializes the CryptoService.
        Can be initialized with existing keys or keys can be generated.

        Args:
            private_key_pem (Optional[bytes]): PEM encoded private key.
            public_key_pem (Optional[bytes]): PEM encoded public key.
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Cryptography library not found. Signing and verification will not work.")
            raise ImportError("Cryptography library is required for CryptoService. Please install 'cryptography'.")

        self.private_key = None
        self.public_key = None

        if private_key_pem:
            try:
                self.private_key = serialization.load_pem_private_key(
                    private_key_pem,
                    password=None # Assuming no password for simplicity
                )
                logger.info("Private key loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load private key: {e}", exc_info=True)
                raise
        
        if public_key_pem:
            try:
                self.public_key = serialization.load_pem_public_key(
                    public_key_pem
                )
                logger.info("Public key loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load public key: {e}", exc_info=True)
                raise
        
        # If a private key was loaded, derive the public key if not provided
        if self.private_key and not self.public_key:
            self.public_key = self.private_key.public_key()
            logger.info("Public key derived from private key.")


    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> tuple[bytes, bytes]:
        """
        Generates an RSA public/private key pair.

        Args:
            key_size (int): The size of the key in bits. Default is 2048.

        Returns:
            tuple[bytes, bytes]: A tuple containing (private_key_pem, public_key_pem).
        
        Raises:
            ImportError: If 'cryptography' library is not installed.
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography library is required to generate key pairs. Please install 'cryptography'.")

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        public_key = private_key.public_key()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        logger.info(f"Generated new RSA key pair with key size {key_size}.")
        return private_key_pem, public_key_pem

    def sign_message(self, message: str) -> bytes:
        """
        Signs a message using the private key.

        Args:
            message (str): The message to sign (will be UTF-8 encoded).

        Returns:
            bytes: The signature.
        
        Raises:
            ValueError: If the private key is not available.
            Exception: For errors during the signing process.
        """
        if not self.private_key:
            raise ValueError("Private key not loaded or generated. Cannot sign message.")
        
        message_bytes = message.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message_bytes,
                padding.PSS( # PSS is a recommended padding scheme
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH 
                ),
                hashes.SHA256() # Hash algorithm for the message itself
            )
            logger.debug(f"Message signed successfully: {message[:50]}...")
            return signature
        except Exception as e:
            logger.error(f"Error signing message: {e}", exc_info=True)
            raise

    def verify_signature(self, message: str, signature: bytes, public_key_pem: Optional[bytes] = None) -> bool:
        """
        Verifies a signature against a message using the public key.

        Args:
            message (str): The original message (will be UTF-8 encoded).
            signature (bytes): The signature to verify.
            public_key_pem (Optional[bytes]): PEM-encoded public key to use for verification.
                                            If None, uses the instance's public key.

        Returns:
            bool: True if the signature is valid, False otherwise.
        
        Raises:
            ValueError: If no public key is available or provided.
        """
        target_public_key = self.public_key
        if public_key_pem:
            try:
                target_public_key = serialization.load_pem_public_key(public_key_pem)
            except Exception as e:
                logger.error(f"Failed to load provided public key for verification: {e}", exc_info=True)
                return False # Cannot verify if key loading fails

        if not target_public_key:
            raise ValueError("Public key not available or provided. Cannot verify signature.")

        message_bytes = message.encode('utf-8')
        try:
            target_public_key.verify(
                signature,
                message_bytes,
                padding.PSS( # Must match the padding used for signing
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            logger.debug(f"Signature verified successfully for message: {message[:50]}...")
            return True
        except Exception: # Includes InvalidSignature
            logger.warning(f"Signature verification failed for message: {message[:50]}...", exc_info=False) # No need for stack trace on typical failures
            return False

# Example Usage (Illustrative)
if __name__ == "__main__":
    print(f"Cryptography library available: {CRYPTOGRAPHY_AVAILABLE}")

    # Hashing example
    data_to_hash = "This is a test string for hashing."
    hashed_data_sha256 = hash_data(data_to_hash, "sha256")
    print(f"\nOriginal Data: '{data_to_hash}'")
    print(f"SHA-256 Hash: {hashed_data_sha256}")

    hashed_data_md5 = hash_data(data_to_hash, "md5") # Example, but not recommended
    print(f"MD5 Hash: {hashed_data_md5}")
    
    try:
        hash_data(data_to_hash, "sha3-256") # Example of unsupported
    except ValueError as e:
        print(f"Error hashing: {e}")


    if CRYPTOGRAPHY_AVAILABLE:
        print("\n--- Digital Signature Example ---")
        # Generate a new key pair for this example
        priv_key_pem, pub_key_pem = CryptoService.generate_key_pair()
        # print(f"Generated Private Key (PEM):\n{priv_key_pem.decode()}")
        # print(f"Generated Public Key (PEM):\n{pub_key_pem.decode()}")

        # Initialize service with the generated private key (public key will be derived)
        crypto_service_signer = CryptoService(private_key_pem=priv_key_pem)
        
        # Initialize a separate service for verification (only needs public key)
        crypto_service_verifier = CryptoService(public_key_pem=pub_key_pem)

        message_to_sign = "This is a very important policy document."
        print(f"Original Message: '{message_to_sign}'")

        # Sign the message
        signature = crypto_service_signer.sign_message(message_to_sign)
        print(f"Signature (first 16 bytes as hex): {signature[:16].hex()}...")

        # Verify the signature
        is_valid = crypto_service_verifier.verify_signature(message_to_sign, signature)
        print(f"Signature valid? {is_valid}")

        # Verify with the correct public key directly
        is_valid_direct_key = crypto_service_verifier.verify_signature(
            message_to_sign, signature, public_key_pem=pub_key_pem
        )
        print(f"Signature valid (with direct key)? {is_valid_direct_key}")


        # Tamper with the message and try to verify
        tampered_message = "This is a very important policy document. (tampered)"
        is_valid_tampered = crypto_service_verifier.verify_signature(tampered_message, signature)
        print(f"Signature valid for tampered message? {is_valid_tampered}")

        # Example with external keys (e.g. loaded from files/env)
        # crypto_service_external = CryptoService(private_key_pem=b"...", public_key_pem=b"...")
    else:
        print("\nSkipping digital signature examples as 'cryptography' library is not installed.")
        print("To run these examples, please install it: pip install cryptography")

    # Example of initializing service without keys initially
    if CRYPTOGRAPHY_AVAILABLE:
        cs_no_keys = CryptoService() # Will raise error if trying to sign/verify without loading keys later
        try:
            cs_no_keys.sign_message("test")
        except ValueError as e:
            print(f"\nError when signing without key: {e}")
    else: # If CRYPTOGRAPHY_AVAILABLE is false, CryptoService() init itself will raise ImportError
        try:
            cs_no_keys_fail = CryptoService()
        except ImportError as e:
            print(f"\nError initializing CryptoService without 'cryptography' lib: {e}")
