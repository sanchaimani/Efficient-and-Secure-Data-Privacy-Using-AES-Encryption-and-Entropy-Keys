import json
import os
import numpy as np
import streamlit as st
from streamlit import session_state
import pdfplumber
import docx
import pyaes
import random
import pandas as pd
import base64
import hashlib
import zipfile
import io
from PIL import Image as PILImage
import tempfile
import secrets
import string

session_state = st.session_state
if "user_index" not in st.session_state:
    st.session_state["user_index"] = 0


class EntropyPoolManager:
    def __init__(self):
        self.pool = bytearray()
    
    def add_entropy(self, data):
        self.pool.extend(data)
    
    def generate_random_bytes(self, num_bytes):
        digest = hashlib.sha256(self.pool).digest()
        self.pool = bytearray()
        return digest[:num_bytes]


class EntropyAccumulator:
    def __init__(self):
        self.entropy = []

    def accumulate_entropy(self, data):
        self.entropy.append(data)

    def generate_random_key(self, length):
        combined_entropy = ''.join(self.entropy)
        key = hashlib.sha256(combined_entropy.encode()).digest()[:length]
        return key   


def generate_strong_entropy():
    """Generate a strong random entropy string"""
    # Generate 5 random words from a word list
    word_list = [
        "Dragon", "Quantum", "Mountain", "Ocean", "Phoenix", "Digital", "Cosmic", 
        "Neon", "Silent", "Electric", "Midnight", "Golden", "Shadow", "Crystal", 
        "Solar", "Forest", "Thunder", "Galaxy", "Nebula", "Infinity", "Eclipse", 
        "Horizon", "Velocity", "Mystic", "Vortex", "Pulse", "Radiant", "Zenith"
    ]
    
    # Select 5 random words
    selected_words = [secrets.choice(word_list) for _ in range(5)]
    
    # Add random numbers and special characters
    random_numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
    special_chars = secrets.choice("!@#$%^&*()_-+=[]{}|;:,.<>?")
    
    # Shuffle the components
    components = selected_words + [random_numbers, special_chars]
    secrets.SystemRandom().shuffle(components)
    
    # Join with random separators
    separators = ["", "-", "_", ".", ""]
    entropy_string = ""
    for i, component in enumerate(components):
        entropy_string += component
        if i < len(components) - 1:
            entropy_string += secrets.choice(separators)
    
    return entropy_string


def generateKey(user_input):
    entropy_accumulator = EntropyAccumulator()
    entropy_manager = EntropyPoolManager()
    entropy_manager.add_entropy(user_input.encode('utf-8'))
    random_bytes = entropy_manager.generate_random_bytes(16)
    entropy_accumulator.accumulate_entropy(random_bytes.hex())
    entropy_accumulator.accumulate_entropy("user_mouse_movement_data")
    entropy_accumulator.accumulate_entropy("system_network_activity_data")
    entropy_accumulator.accumulate_entropy("system_process_timing_data")
    random_key = entropy_accumulator.generate_random_key(16)
    return random_key


def encrypt_data(data, key):
    """Encrypt any data using AES-CTR"""
    aes = pyaes.AESModeOfOperationCTR(key)
    cipher_text = aes.encrypt(data)
    return base64.b64encode(cipher_text).decode("utf-8")


def decrypt_data(encrypted_data, key):
    """Decrypt data using AES-CTR"""
    try:
        cipher_text = base64.b64decode(encrypted_data)
        aes = pyaes.AESModeOfOperationCTR(key)
        decrypted_data = aes.decrypt(cipher_text)
        return decrypted_data
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")


def signup(json_file_path="data.json"):
    st.title("Signup Page")
    with st.form("signup_form"):
        st.write("Fill in the details below to create an account:")
        name = st.text_input("Name:")
        email = st.text_input("Email:")
        age = st.number_input("Age:", min_value=0, max_value=120)
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")

        if st.form_submit_button("Signup"):
            if password == confirm_password:
                user = create_account(name, email, age, password, json_file_path)
                session_state["logged_in"] = True
                session_state["user_info"] = user
            else:
                st.error("Passwords do not match. Please try again.")


def check_login(username, password, json_file_path="data.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)

        for user in data["users"]:
            if user["email"] == username and user["password"] == password:
                session_state["logged_in"] = True
                session_state["user_info"] = user
                st.success("Login successful!")
                return user

        st.error("Invalid credentials. Please try again.")
        return None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return None


def initialize_database():
    try:
        if not os.path.exists("data.json"):
            data = {"users": []}
            with open("data.json", "w") as json_file:
                json.dump(data, json_file)

    except Exception as e:
        print(f"Error initializing database: {e}")


def create_account(name, email, age, password, json_file_path="data.json"):
    try:
        if not os.path.exists(json_file_path) or os.stat(json_file_path).st_size == 0:
            data = {"users": []}
        else:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)

        user_info = {
            "name": name,
            "email": email,
            "age": age,
            "password": password,
            "files": [],
        }
        
        for user in data["users"]:
            if user["email"] == email:
                st.warning("An account with this email already exists. Please login.")
                return None
        data["users"].append(user_info)

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        st.success("Account created successfully! You can now login.")
        return user_info
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Error creating account: {e}")
        return None


def login(json_file_path="data.json"):
    st.title("Login Page")
    username = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    login_button = st.button("Login")

    if login_button:
        user = check_login(username, password, json_file_path)
        if user is not None:
            session_state["logged_in"] = True
            session_state["user_info"] = user
        else:
            st.error("Invalid credentials. Please try again.")


def render_dashboard(user_info, json_file_path="data.json"):
    try:
        st.title(f"Welcome to the Dashboard, {user_info['name']}!")
        st.subheader("User Information:")
        st.write(f"Name: {user_info['name']}")
        st.write(f"Age: {user_info['age']}")
        
    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")


def encrypt_file(file_data, key):
    """Encrypt file data using AES-CTR"""
    aes = pyaes.AESModeOfOperationCTR(key)
    cipher_text = aes.encrypt(file_data)
    return base64.b64encode(cipher_text).decode("utf-8")


def decrypt_file(encrypted_data, key):
    """Decrypt file data using AES-CTR"""
    try:
        cipher_text = base64.b64decode(encrypted_data)
        aes = pyaes.AESModeOfOperationCTR(key)
        decrypted_data = aes.decrypt(cipher_text)
        return decrypted_data
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")


def process_uploaded_file(uploaded_file, entropy_string, json_file_path):
    """Process and encrypt uploaded file"""
    try:
        # Read file data
        file_data = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        
        # Generate encryption key from entropy string
        file_key = generateKey(entropy_string)
        
        # Encrypt the file data
        encrypted_data = encrypt_file(file_data, file_key)
        
        # Save to user's data
        with open(json_file_path, "r+") as json_file:
            data = json.load(json_file)
            user_index = next(
                (i for i, user in enumerate(data["users"]) 
                 if user["email"] == session_state["user_info"]["email"]),
                None,
            )
            
            if user_index is not None:
                user_info = data["users"][user_index]
                if "files" not in user_info:
                    user_info["files"] = []
                
                # Check for duplicate names
                existing_names = [f["filename"] for f in user_info["files"]]
                if file_name in existing_names:
                    name_parts = os.path.splitext(file_name)
                    counter = 1
                    while f"{name_parts[0]}_{counter}{name_parts[1]}" in existing_names:
                        counter += 1
                    file_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                
                # Add file info
                file_info = {
                    "filename": file_name,
                    "file_type": file_type,
                    "encrypted_data": encrypted_data,
                    "upload_time": str(np.datetime64("now")),
                    "original_size": len(file_data),
                    "entropy_used": entropy_string  # Store the entropy used
                }
                user_info["files"].append(file_info)
                
                # Update session
                session_state["user_info"] = user_info
                
                # Save to JSON
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
                
                return file_info, file_key, entropy_string
        return None, None, None
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None


def main(json_file_path="data.json"):
    st.sidebar.title("Secure File Encryption System")
    page = st.sidebar.radio(
        "Navigation",
        ("Signup/Login", "Dashboard", "File Upload", "File Download"),
        key="navigation"
    )

    if page == "Signup/Login":
        st.title("Signup/Login Page")
        login_or_signup = st.radio(
            "Select an option", ("Login", "Signup"), key="login_signup"
        )
        if login_or_signup == "Login":
            login(json_file_path)
        else:
            signup(json_file_path)

    elif page == "Dashboard":
        if session_state.get("logged_in"):
            render_dashboard(session_state["user_info"])
        else:
            st.warning("Please login/signup to view the dashboard.")

    elif page == "File Upload":
        if session_state.get("logged_in"):
            st.title("File Upload & Encryption")
            
            # File uploader for multiple file types
            uploaded_file = st.file_uploader(
                "Upload a file to encrypt",
                type=["png", "jpg", "jpeg", "pdf", "txt", "docx"],
                key="file_uploader"
            )
            
            if uploaded_file is not None:
                # Display file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Name", uploaded_file.name)
                with col2:
                    st.metric("File Type", uploaded_file.type)
                with col3:
                    st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
                
                # Generate entropy automatically
                if 'generated_entropy' not in st.session_state:
                    st.session_state.generated_entropy = generate_strong_entropy()
                
                # Ask for decryption password
                st.subheader("Set Decryption Password")
                decryption_password = st.text_input(
                    "Enter a password for decryption:",
                    type="password",
                    help="You'll need this password to decrypt the file later"
                )
                
                confirm_password = st.text_input(
                    "Confirm decryption password:",
                    type="password"
                )
                
                # Encrypt button
                if st.button("Encrypt", type="primary") and decryption_password and decryption_password == confirm_password:
                    with st.spinner("Encrypting file..."):
                        # Use the generated entropy
                        entropy_string = st.session_state.generated_entropy
                        file_info, file_key, entropy_used = process_uploaded_file(
                            uploaded_file, entropy_string, json_file_path
                        )
                        
                        if file_info and file_key:
                            st.success("File encrypted successfully!")
                            
                            # Generate a MASTER KEY for encrypting metadata
                            master_key = secrets.token_bytes(16)  # Random 16-byte key
                            
                            # Create zip file with encrypted file, encrypted metadata
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                                # Add encrypted file
                                zip_file.writestr(
                                    f"encrypted_{file_info['filename']}", 
                                    file_info['encrypted_data']
                                )
                                
                                # Encrypt and add key file
                                encrypted_key_data = encrypt_data(file_key, master_key)
                                zip_file.writestr("encryption_key.enc", encrypted_key_data)
                                
                                # Encrypt and add entropy file
                                encrypted_entropy = encrypt_data(entropy_string.encode('utf-8'), master_key)
                                zip_file.writestr("entropy_string.enc", encrypted_entropy)
                                
                                # Encrypt and add info file
                                info = {
                                    "original_filename": file_info['filename'],
                                    "file_type": file_info['file_type'],
                                    "upload_time": file_info['upload_time'],
                                    "original_size": file_info['original_size']
                                }
                                info_json = json.dumps(info, indent=2).encode('utf-8')
                                encrypted_info = encrypt_data(info_json, master_key)
                                zip_file.writestr("file_info.enc", encrypted_info)
                                
                                # Encrypt MASTER KEY with password-derived key
                                # Create key from password
                                password_key = hashlib.sha256(decryption_password.encode('utf-8')).digest()[:16]
                                master_key_encrypted = encrypt_data(master_key, password_key)
                                zip_file.writestr("master_key.enc", master_key_encrypted)
                            
                            # Download button
                            zip_buffer.seek(0)
                            
                            # Clear the generated entropy for next upload
                            st.session_state.generated_entropy = generate_strong_entropy()
                            
                            # Create download button with success message
                            if st.download_button(
                                label=" Download Encrypted Package",
                                data=zip_buffer,
                                file_name=f"encrypted_{file_info['filename']}.zip",
                                mime="application/zip",
                                help="This zip contains encrypted file and encrypted metadata"
                            ):
                                st.success("Package downloaded! Keep it safe.")
                                st.warning("⚠️ Remember your decryption password! You'll need it to decrypt.")
                elif decryption_password and decryption_password != confirm_password:
                    st.error("Passwords do not match!")
                                
        else:
            st.warning("Please login/signup to access this page.")

    elif page == "File Download":
        if session_state.get("logged_in"):
            st.title("File Download & Decryption")
            st.info("Upload your encrypted zip package to decrypt the file.")
            
            # Upload encrypted zip
            encrypted_package = st.file_uploader(
                "Upload your encrypted zip package",
                type=["zip"],
                key="encrypted_package",
                help="Upload the zip file you downloaded from the File Upload section"
            )
            
            if encrypted_package:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    try:
                        # Extract zip
                        with zipfile.ZipFile(encrypted_package, 'r') as zip_ref:
                            zip_ref.extractall(tmp_dir)
                        
                        # Find files
                        extracted_files = os.listdir(tmp_dir)
                        
                        # Initialize variables
                        key_file = None
                        encrypted_file = None
                        entropy_file = None
                        info_file = None
                        master_key_file = None
                        
                        # Identify files
                        for file in extracted_files:
                            file_path = os.path.join(tmp_dir, file)
                            if file == "encryption_key.enc":
                                key_file = file_path
                            elif file.startswith("encrypted_"):
                                encrypted_file = file_path
                            elif file == "entropy_string.enc":
                                entropy_file = file_path
                            elif file == "file_info.enc":
                                info_file = file_path
                            elif file == "master_key.enc":
                                master_key_file = file_path
                        
                        # Check if all required files are present
                        missing_files = []
                        if not key_file:
                            missing_files.append("encryption_key.enc")
                        if not encrypted_file:
                            missing_files.append("encrypted file")
                        if not entropy_file:
                            missing_files.append("entropy_string.enc")
                        if not master_key_file:
                            missing_files.append("master_key.enc")
                        
                        if missing_files:
                            st.error(f"Invalid package format. Missing: {', '.join(missing_files)}")
                            st.info("Please upload the complete zip package downloaded from File Upload.")
                        else:
                            # Ask for decryption password
                            st.subheader("Enter Decryption Password")
                            decryption_password = st.text_input(
                                "Enter the decryption password you set during encryption:",
                                type="password",
                                key="decryption_password"
                            )
                            
                            if decryption_password:
                                try:
                                    # Create key from password
                                    password_key = hashlib.sha256(decryption_password.encode('utf-8')).digest()[:16]
                                    
                                    # Read the encrypted master key
                                    with open(master_key_file, 'r') as f:
                                        encrypted_master_key = f.read()
                                    
                                    # Decrypt master key using password
                                    master_key = decrypt_data(encrypted_master_key, password_key)
                                    
                                    # Read other encrypted files
                                    with open(key_file, 'r') as f:
                                        encrypted_key_data = f.read()
                                    
                                    with open(entropy_file, 'r') as f:
                                        encrypted_entropy_data = f.read()
                                    
                                    with open(info_file, 'r') as f:
                                        encrypted_info_data = f.read()
                                    
                                    with open(encrypted_file, 'r') as f:
                                        encrypted_file_data = f.read()
                                    
                                    # Decrypt all metadata using master key
                                    decrypted_key = decrypt_data(encrypted_key_data, master_key)
                                    decrypted_entropy = decrypt_data(encrypted_entropy_data, master_key).decode('utf-8')
                                    decrypted_info = decrypt_data(encrypted_info_data, master_key).decode('utf-8')
                                    info = json.loads(decrypted_info)
                                    
                                    original_filename = info.get('original_filename', 'decrypted_file')
                                    file_type = info.get('file_type', 'application/octet-stream')
                                    
                                    st.success("✅ Password verified! Ready to decrypt file.")
                                    
                                    # Decrypt button
                                    if st.button(" Decrypt File", type="primary", use_container_width=True):
                                        with st.spinner("Decrypting file..."):
                                            try:
                                                # Decrypt the file
                                                decrypted_data = decrypt_file(encrypted_file_data, decrypted_key)
                                                
                                                st.success("✅ File decrypted successfully!")
                                                
                                                # Create download button
                                                st.download_button(
                                                    label=f"📥 Download {original_filename}",
                                                    data=decrypted_data,
                                                    file_name=original_filename,
                                                    mime=file_type,
                                                    use_container_width=True,
                                                    help="Click to download the decrypted file"
                                                )
                                                
                                            except Exception as e:
                                                st.error(f"❌ File decryption failed: {str(e)}")
                                    
                                except Exception as e:
                                    st.error(f"❌ Incorrect password or corrupted package: {str(e)}")
                            
                    except zipfile.BadZipFile:
                        st.error("Invalid zip file. Please upload a valid encrypted package.")
                    except Exception as e:
                        st.error(f"Error processing package: {str(e)}")
                
        else:
            st.warning("Please login/signup to access this page.")


if __name__ == "__main__":
    initialize_database()
    main()