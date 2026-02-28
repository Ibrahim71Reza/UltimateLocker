import customtkinter
import secrets
import string
import os
import shutil # NEW: Tool to Zip and Unzip folders!
from zxcvbn import zxcvbn
from tkinter import filedialog 

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry("700x600") 
app.title("Ultimate Privacy Toolkit")

# ==========================================
# 1. PASSWORD GENERATOR LOGIC
# ==========================================
def update_slider_text(value): length_label.configure(text=f"Password Length: {int(value)}")
def check_strength(password):
    if password == "":
        strength_label.configure(text="Strength: Waiting...", text_color="white")
        return
    score = zxcvbn(password)['score']
    if score == 0: strength_label.configure(text="Strength: Very Weak", text_color="#FF4A4A")
    elif score == 1: strength_label.configure(text="Strength: Weak", text_color="#FF8C00")
    elif score == 2: strength_label.configure(text="Strength: Fair", text_color="#FFD700")
    elif score == 3: strength_label.configure(text="Strength: Strong", text_color="#00C851")
    elif score == 4: strength_label.configure(text="Strength: Very Strong!", text_color="#00FF00")

def on_user_typing(event): check_strength(password_display.get())
def create_password():
    length = int(length_slider.get())
    allowed_chars = ""
    if chk_upper.get() == 1: allowed_chars += string.ascii_uppercase
    if chk_lower.get() == 1: allowed_chars += string.ascii_lowercase
    if chk_numbers.get() == 1: allowed_chars += string.digits
    if chk_symbols.get() == 1: allowed_chars += "!@#$%^&*()-_=+"
    if allowed_chars == "": allowed_chars = string.ascii_lowercase; chk_lower.select()
    new_password = "".join(secrets.choice(allowed_chars) for _ in range(length))
    password_display.delete(0, "end"); password_display.insert(0, new_password); check_strength(new_password)

# ==========================================
# 2. FILE & FOLDER LOCKER LOGIC 
# ==========================================
selected_path = "" 
password_entries = [] 

def browse_file():
    global selected_path
    filename = filedialog.askopenfilename()
    if filename: 
        selected_path = filename
        path_label.configure(text=f"Selected: {selected_path}")

def browse_folder():
    global selected_path
    foldername = filedialog.askdirectory()
    if foldername:
        selected_path = foldername
        path_label.configure(text=f"Selected: {selected_path}")

def add_layer():
    if len(password_entries) < 5: 
        new_entry = customtkinter.CTkEntry(passwords_container, width=300, placeholder_text=f"Layer {len(password_entries) + 1} Password...", show="*")
        new_entry.pack(pady=5)
        password_entries.append(new_entry)
        if show_password_var.get() == 1: new_entry.configure(show="")

def remove_layer():
    if len(password_entries) > 1: 
        entry_to_remove = password_entries.pop() 
        entry_to_remove.destroy() 

def toggle_password_visibility():
    show_char = "" if show_password_var.get() == 1 else "*"
    for entry in password_entries: entry.configure(show=show_char)

# --- THE CRYPTO ENGINE ---
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return kdf.derive(password.encode())

def encrypt_action():
    global selected_path
    
    if selected_path.endswith(".locked"):
        locker_status_label.configure(text="Error: Already locked!", text_color="#FF8C00")
        return
        
    if selected_path == "" or not os.path.exists(selected_path):
        locker_status_label.configure(text="Error: Please select a valid file or folder.", text_color="#FF4A4A")
        return
        
    passwords = [entry.get() for entry in password_entries if entry.get() != ""]
    if len(passwords) == 0:
        locker_status_label.configure(text="Error: Please enter at least 1 password.", text_color="#FF4A4A")
        return

    try:
        # FOLDER HANDLING: Zip it up first!
        is_folder = os.path.isdir(selected_path)
        target_to_encrypt = selected_path

        if is_folder:
            locker_status_label.configure(text="Compressing folder... Please wait.", text_color="white")
            app.update()
            # This creates 'myfolder.zip'
            shutil.make_archive(selected_path, 'zip', selected_path)
            target_to_encrypt = selected_path + ".zip"

        locker_status_label.configure(text="Applying Encryption Layers...", text_color="white")
        app.update() 

        with open(target_to_encrypt, 'rb') as f:
            current_data = f.read()

        for pwd in passwords:
            salt = os.urandom(16)
            key = derive_key(pwd, salt)
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            current_data = salt + nonce + aesgcm.encrypt(nonce, current_data, None)

        # Name it differently so the app knows if it's a file or folder when unlocking
        if is_folder:
            locked_path = selected_path + ".folder.locked"
        else:
            locked_path = selected_path + ".file.locked"

        with open(locked_path, 'wb') as f:
            f.write(current_data)

        # CLEANUP: Delete originals
        if is_folder:
            os.remove(target_to_encrypt) # Delete the temp zip
            shutil.rmtree(selected_path) # Delete the original folder
        else:
            os.remove(selected_path) # Delete the original file

        selected_path = locked_path
        path_label.configure(text=f"Selected: {selected_path}")
        for entry in password_entries: entry.delete(0, 'end') 
        locker_status_label.configure(text=f"Success! Secured with {len(passwords)} layer(s).", text_color="#00FF00")

    except Exception as e:
        locker_status_label.configure(text=f"Encryption Failed: {str(e)}", text_color="#FF4A4A")

def decrypt_action():
    global selected_path
    
    if selected_path == "" or not selected_path.endswith(".locked"):
        locker_status_label.configure(text="Error: Please select a '.locked' file.", text_color="#FF4A4A")
        return
        
    passwords = [entry.get() for entry in password_entries if entry.get() != ""]
    if len(passwords) == 0:
        locker_status_label.configure(text="Error: Please enter passwords to unlock.", text_color="#FF4A4A")
        return

    try:
        locker_status_label.configure(text="Peeling Encryption Layers...", text_color="white")
        app.update()

        with open(selected_path, 'rb') as f:
            current_data = f.read()

        for pwd in reversed(passwords):
            salt = current_data[:16] 
            nonce = current_data[16:28] 
            encrypted_chunk = current_data[28:] 
            key = derive_key(pwd, salt)
            aesgcm = AESGCM(key)
            current_data = aesgcm.decrypt(nonce, encrypted_chunk, None) 

        # FOLDER HANDLING: Unzip it!
        is_folder = selected_path.endswith(".folder.locked")

        if is_folder:
            temp_zip_path = selected_path.replace(".folder.locked", ".zip")
            with open(temp_zip_path, 'wb') as f:
                f.write(current_data)
            
            locker_status_label.configure(text="Extracting folder...", text_color="white")
            app.update()
            
            original_folder_path = selected_path.replace(".folder.locked", "")
            shutil.unpack_archive(temp_zip_path, original_folder_path, 'zip')
            os.remove(temp_zip_path) # Cleanup temp zip
            original_path = original_folder_path
        else:
            original_path = selected_path.replace(".file.locked", "")
            with open(original_path, 'wb') as f:
                f.write(current_data)

        os.remove(selected_path) # Delete the locked file

        selected_path = original_path
        path_label.configure(text=f"Selected: {selected_path}")
        for entry in password_entries: entry.delete(0, 'end') 
        locker_status_label.configure(text="Success! Fully UNLOCKED.", text_color="#00FF00")

    except InvalidTag: 
        locker_status_label.configure(text="ACCESS DENIED: Wrong Password or Order!", text_color="#FF4A4A")
    except Exception as e:
        locker_status_label.configure(text="Decryption Failed. Wrong number of layers?", text_color="#FF4A4A")

# ==========================================
# 3. UI DESIGN 
# ==========================================
tabview = customtkinter.CTkTabview(app, width=650, height=550)
tabview.pack(pady=10)
tabview.add("Password Generator")
tabview.add("File Locker")

pass_tab = tabview.tab("Password Generator")
password_display = customtkinter.CTkEntry(pass_tab, width=450, font=("Helvetica", 24), justify="center")
password_display.pack(pady=20)
password_display.bind("<KeyRelease>", on_user_typing)
length_label = customtkinter.CTkLabel(pass_tab, text="Password Length: 16", font=("Helvetica", 16))
length_label.pack(pady=5)
length_slider = customtkinter.CTkSlider(pass_tab, from_=8, to=64, number_of_steps=56, command=update_slider_text)
length_slider.set(16)
length_slider.pack(pady=10)
checkbox_frame = customtkinter.CTkFrame(pass_tab, fg_color="transparent")
checkbox_frame.pack(pady=15)
chk_upper = customtkinter.CTkCheckBox(checkbox_frame, text="A-Z"); chk_upper.select(); chk_upper.pack(side="left", padx=10)
chk_lower = customtkinter.CTkCheckBox(checkbox_frame, text="a-z"); chk_lower.select(); chk_lower.pack(side="left", padx=10)
chk_numbers = customtkinter.CTkCheckBox(checkbox_frame, text="0-9"); chk_numbers.select(); chk_numbers.pack(side="left", padx=10)
chk_symbols = customtkinter.CTkCheckBox(checkbox_frame, text="!@#$"); chk_symbols.select(); chk_symbols.pack(side="left", padx=10)
generate_btn = customtkinter.CTkButton(pass_tab, text="Generate Password", font=("Helvetica", 16, "bold"), command=create_password)
generate_btn.pack(pady=20)
strength_label = customtkinter.CTkLabel(pass_tab, text="Strength: Waiting...", font=("Helvetica", 16))
strength_label.pack(pady=5)

file_tab = tabview.tab("File Locker")
title_label = customtkinter.CTkLabel(file_tab, text="Secure File & Folder Encryption", font=("Helvetica", 20, "bold"))
title_label.pack(pady=15)

browse_frame = customtkinter.CTkFrame(file_tab, fg_color="transparent")
browse_frame.pack(pady=5)
btn_select_file = customtkinter.CTkButton(browse_frame, text="Select File", command=browse_file)
btn_select_file.pack(side="left", padx=10)
btn_select_folder = customtkinter.CTkButton(browse_frame, text="Select Folder", command=browse_folder)
btn_select_folder.pack(side="left", padx=10)

path_label = customtkinter.CTkLabel(file_tab, text="Selected: None", font=("Helvetica", 12), text_color="gray")
path_label.pack(pady=5)

passwords_container = customtkinter.CTkFrame(file_tab, fg_color="transparent")
passwords_container.pack(pady=5)

show_password_var = customtkinter.IntVar(value=0) 
add_layer() 

layer_controls = customtkinter.CTkFrame(file_tab, fg_color="transparent")
layer_controls.pack(pady=5)
btn_add_layer = customtkinter.CTkButton(layer_controls, text="+ Add Layer", width=100, command=add_layer)
btn_add_layer.pack(side="left", padx=5)
btn_remove_layer = customtkinter.CTkButton(layer_controls, text="- Remove Layer", width=100, command=remove_layer, fg_color="#555555")
btn_remove_layer.pack(side="left", padx=5)

show_password_checkbox = customtkinter.CTkCheckBox(file_tab, text="Show Passwords", variable=show_password_var, command=toggle_password_visibility)
show_password_checkbox.pack(pady=10)

action_frame = customtkinter.CTkFrame(file_tab, fg_color="transparent")
action_frame.pack(pady=10)
btn_lock = customtkinter.CTkButton(action_frame, text="Lock (Encrypt)", fg_color="#FF4A4A", hover_color="#CC0000", command=encrypt_action)
btn_lock.pack(side="left", padx=10)
btn_unlock = customtkinter.CTkButton(action_frame, text="Unlock (Decrypt)", fg_color="#00C851", hover_color="#007E33", command=decrypt_action)
btn_unlock.pack(side="left", padx=10)

locker_status_label = customtkinter.CTkLabel(file_tab, text="", font=("Helvetica", 14))
locker_status_label.pack(pady=10)

app.mainloop()