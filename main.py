import customtkinter
import secrets
import string
import os
import shutil
import json 
from zxcvbn import zxcvbn
from tkinter import filedialog 

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry("750x700") # Made slightly taller to fit the change password menu
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
# 2. PASSWORD VAULT LOGIC (FIXED)
# ==========================================
VAULT_FILE = "vault.enc"
is_vault_unlocked = False
vault_master_key = None
vault_salt = None 
vault_data = {"entries": []} 
vault_pass_hidden = True # NEW: Tracks if the Eye is open or closed

def save_vault_to_disk():
    global vault_data, vault_master_key, vault_salt
    if not is_vault_unlocked or vault_master_key is None or vault_salt is None: return
    
    json_data = json.dumps(vault_data).encode('utf-8')
    aesgcm = AESGCM(vault_master_key)
    nonce = os.urandom(12)
    encrypted_data = aesgcm.encrypt(nonce, json_data, None)
    
    with open(VAULT_FILE, 'wb') as f:
        f.write(vault_salt + nonce + encrypted_data)

def unlock_vault():
    global is_vault_unlocked, vault_master_key, vault_salt, vault_data
    master_pass = vault_password_entry.get()
    
    if master_pass == "":
        vault_status_label.configure(text="Error: Enter a Master Password", text_color="#FF4A4A")
        return

    if not os.path.exists(VAULT_FILE):
        vault_salt = os.urandom(16) 
        vault_master_key = derive_key(master_pass, vault_salt) 
        is_vault_unlocked = True
        vault_data = {"entries": []}
        save_vault_to_disk() 
        
        vault_status_label.configure(text="New Vault Created & Unlocked!", text_color="#00FF00")
        refresh_vault_display()
        vault_password_entry.delete(0, 'end')
        btn_show_change_pass.configure(state="normal") # Enable Change Password Button
        return

    try:
        with open(VAULT_FILE, 'rb') as f: file_data = f.read()
        vault_salt = file_data[:16] 
        nonce = file_data[16:28]
        encrypted_data = file_data[28:]
        
        test_key = derive_key(master_pass, vault_salt)
        aesgcm = AESGCM(test_key)
        decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
        
        vault_master_key = test_key
        is_vault_unlocked = True
        vault_data = json.loads(decrypted_data.decode('utf-8'))
        
        vault_status_label.configure(text="Vault Unlocked Successfully!", text_color="#00FF00")
        refresh_vault_display()
        vault_password_entry.delete(0, 'end')
        btn_show_change_pass.configure(state="normal") # Enable Change Password Button
        
    except InvalidTag:
        vault_status_label.configure(text="ACCESS DENIED: Wrong Master Password!", text_color="#FF4A4A")
    except Exception as e:
        vault_status_label.configure(text="Error reading vault.", text_color="#FF4A4A")

def refresh_vault_display():
    vault_textbox.configure(state="normal")
    vault_textbox.delete("1.0", "end")
    if not is_vault_unlocked:
        vault_textbox.insert("end", "Vault is locked.\nEnter your Master Password above to view your saved items.")
    elif len(vault_data["entries"]) == 0:
        vault_textbox.insert("end", "Vault is empty!\nGo to the File Locker tab, add some passwords,\nand check 'Save to Vault' when locking a file.")
    else:
        for entry in vault_data["entries"]:
            vault_textbox.insert("end", f"File/Folder: {entry['file']}\n")
            vault_textbox.insert("end", f"Layers Used: {len(entry['passwords'])}\n")
            vault_textbox.insert("end", f"Passwords (in order): {', '.join(entry['passwords'])}\n")
            vault_textbox.insert("end", "-"*45 + "\n")
    vault_textbox.configure(state="disabled")

def lock_vault():
    global is_vault_unlocked, vault_master_key, vault_salt, vault_data
    is_vault_unlocked = False
    vault_master_key = None
    vault_salt = None
    vault_data = {"entries": []}
    vault_status_label.configure(text="Vault is securely Locked.", text_color="#FFD700")
    refresh_vault_display()
    btn_show_change_pass.configure(state="disabled") # Disable Change Password Button
    change_pass_frame.pack_forget() # Hide the menu if open

# NEW: Eye toggle function
def toggle_vault_eye():
    global vault_pass_hidden
    vault_pass_hidden = not vault_pass_hidden
    vault_password_entry.configure(show="*" if vault_pass_hidden else "")
    btn_vault_eye.configure(text="👁️" if vault_pass_hidden else "🙈")

# NEW: Show/Hide the change password menu
def toggle_change_pass_menu():
    if not is_vault_unlocked: return
    if change_pass_frame.winfo_ismapped():
        change_pass_frame.pack_forget()
    else:
        change_pass_frame.pack(pady=5, before=vault_textbox)

# NEW: Apply the new master password securely
def apply_new_master_password():
    global vault_salt, vault_master_key
    curr_pass = current_pass_entry.get()
    new_pass = new_pass_entry.get()
    conf_pass = confirm_pass_entry.get()
    
    if not is_vault_unlocked:
        return change_pass_status.configure(text="Error: Unlock vault first.", text_color="#FF4A4A")
    
    # 1. VERIFY CURRENT PASSWORD
    test_key = derive_key(curr_pass, vault_salt)
    if test_key != vault_master_key:
        return change_pass_status.configure(text="Error: Current password incorrect!", text_color="#FF4A4A")
        
    if new_pass == "" or conf_pass == "":
        return change_pass_status.configure(text="Error: New password cannot be empty.", text_color="#FF4A4A")
    if new_pass != conf_pass:
        return change_pass_status.configure(text="Error: New passwords do not match!", text_color="#FF4A4A")
        
    # 2. GENERATE NEW KEY AND SALT
    vault_salt = os.urandom(16)
    vault_master_key = derive_key(new_pass, vault_salt)
    
    # 3. SAVE VAULT WITH NEW CREDENTIALS
    save_vault_to_disk()
    
    change_pass_status.configure(text="Success! Master Password Changed.", text_color="#00FF00")
    current_pass_entry.delete(0, 'end')
    new_pass_entry.delete(0, 'end')
    confirm_pass_entry.delete(0, 'end')
    app.after(2000, lambda: change_pass_frame.pack_forget())
    app.after(2000, lambda: change_pass_status.configure(text=""))


# ==========================================
# 3. FILE & FOLDER LOCKER LOGIC 
# ==========================================
selected_path = "" 
password_entries = [] 

def browse_file():
    global selected_path
    filename = filedialog.askopenfilename()
    if filename: selected_path = filename; path_label.configure(text=f"Selected: {selected_path}")

def browse_folder():
    global selected_path
    foldername = filedialog.askdirectory()
    if foldername: selected_path = foldername; path_label.configure(text=f"Selected: {selected_path}")

def add_layer():
    if len(password_entries) < 5: 
        new_entry = customtkinter.CTkEntry(passwords_container, width=300, placeholder_text=f"Layer {len(password_entries) + 1} Password...", show="*")
        new_entry.pack(pady=5)
        password_entries.append(new_entry)
        if show_password_var.get() == 1: new_entry.configure(show="")

def remove_layer():
    if len(password_entries) > 1: password_entries.pop().destroy() 

def toggle_password_visibility():
    show_char = "" if show_password_var.get() == 1 else "*"
    for entry in password_entries: entry.configure(show=show_char)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return kdf.derive(password.encode())

def encrypt_action():
    global selected_path
    if selected_path.endswith(".locked"): return locker_status_label.configure(text="Error: Already locked!", text_color="#FF8C00")
    if selected_path == "" or not os.path.exists(selected_path): return locker_status_label.configure(text="Error: Select a file/folder.", text_color="#FF4A4A")
        
    passwords = [entry.get() for entry in password_entries if entry.get() != ""]
    if len(passwords) == 0: return locker_status_label.configure(text="Error: Enter at least 1 password.", text_color="#FF4A4A")

    if save_to_vault_var.get() == 1 and not is_vault_unlocked:
        return locker_status_label.configure(text="Error: Please unlock Password Vault first!", text_color="#FF4A4A")

    try:
        is_folder = os.path.isdir(selected_path)
        target_to_encrypt = selected_path
        if is_folder:
            locker_status_label.configure(text="Compressing folder...", text_color="white"); app.update()
            shutil.make_archive(selected_path, 'zip', selected_path)
            target_to_encrypt = selected_path + ".zip"

        locker_status_label.configure(text="Applying Encryption Layers...", text_color="white"); app.update() 

        with open(target_to_encrypt, 'rb') as f: current_data = f.read()

        for pwd in passwords:
            salt = os.urandom(16)
            key = derive_key(pwd, salt)
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            current_data = salt + nonce + aesgcm.encrypt(nonce, current_data, None)

        locked_path = selected_path + ".folder.locked" if is_folder else selected_path + ".file.locked"

        with open(locked_path, 'wb') as f: f.write(current_data)

        if is_folder: os.remove(target_to_encrypt); shutil.rmtree(selected_path) 
        else: os.remove(selected_path) 

        if save_to_vault_var.get() == 1:
            vault_data["entries"].append({
                "file": os.path.basename(selected_path),
                "passwords": passwords
            })
            save_vault_to_disk()
            refresh_vault_display()

        selected_path = locked_path
        path_label.configure(text=f"Selected: {selected_path}")
        for entry in password_entries: entry.delete(0, 'end') 
        locker_status_label.configure(text=f"Success! Secured with {len(passwords)} layer(s).", text_color="#00FF00")

    except Exception as e:
        locker_status_label.configure(text=f"Encryption Failed: {str(e)}", text_color="#FF4A4A")

def decrypt_action():
    global selected_path
    if selected_path == "" or not selected_path.endswith(".locked"): return locker_status_label.configure(text="Error: Select a '.locked' file.", text_color="#FF4A4A")
        
    passwords = [entry.get() for entry in password_entries if entry.get() != ""]
    if len(passwords) == 0: return locker_status_label.configure(text="Error: Enter passwords to unlock.", text_color="#FF4A4A")

    try:
        locker_status_label.configure(text="Peeling Encryption Layers...", text_color="white"); app.update()

        with open(selected_path, 'rb') as f: current_data = f.read()

        for pwd in reversed(passwords):
            salt = current_data[:16]; nonce = current_data[16:28]; encrypted_chunk = current_data[28:] 
            key = derive_key(pwd, salt)
            current_data = AESGCM(key).decrypt(nonce, encrypted_chunk, None) 

        is_folder = selected_path.endswith(".folder.locked")
        if is_folder:
            temp_zip_path = selected_path.replace(".folder.locked", ".zip")
            with open(temp_zip_path, 'wb') as f: f.write(current_data)
            locker_status_label.configure(text="Extracting folder...", text_color="white"); app.update()
            original_folder_path = selected_path.replace(".folder.locked", "")
            shutil.unpack_archive(temp_zip_path, original_folder_path, 'zip')
            os.remove(temp_zip_path) 
            original_path = original_folder_path
        else:
            original_path = selected_path.replace(".file.locked", "")
            with open(original_path, 'wb') as f: f.write(current_data)

        os.remove(selected_path) 
        selected_path = original_path
        path_label.configure(text=f"Selected: {selected_path}")
        for entry in password_entries: entry.delete(0, 'end') 
        locker_status_label.configure(text="Success! Fully UNLOCKED.", text_color="#00FF00")

    except InvalidTag: locker_status_label.configure(text="ACCESS DENIED: Wrong Password or Order!", text_color="#FF4A4A")
    except Exception as e: locker_status_label.configure(text="Decryption Failed. Wrong number of layers?", text_color="#FF4A4A")


# ==========================================
# 4. UI DESIGN 
# ==========================================
tabview = customtkinter.CTkTabview(app, width=700, height=650)
tabview.pack(pady=10)
tabview.add("Password Generator")
tabview.add("File Locker")
tabview.add("Password Vault") 

# --- PASSWORD GENERATOR TAB ---
pass_tab = tabview.tab("Password Generator")
password_display = customtkinter.CTkEntry(pass_tab, width=450, font=("Helvetica", 24), justify="center"); password_display.pack(pady=20)
password_display.bind("<KeyRelease>", on_user_typing)
length_label = customtkinter.CTkLabel(pass_tab, text="Password Length: 16", font=("Helvetica", 16)); length_label.pack(pady=5)
length_slider = customtkinter.CTkSlider(pass_tab, from_=8, to=64, number_of_steps=56, command=update_slider_text); length_slider.set(16); length_slider.pack(pady=10)
checkbox_frame = customtkinter.CTkFrame(pass_tab, fg_color="transparent"); checkbox_frame.pack(pady=15)
chk_upper = customtkinter.CTkCheckBox(checkbox_frame, text="A-Z"); chk_upper.select(); chk_upper.pack(side="left", padx=10)
chk_lower = customtkinter.CTkCheckBox(checkbox_frame, text="a-z"); chk_lower.select(); chk_lower.pack(side="left", padx=10)
chk_numbers = customtkinter.CTkCheckBox(checkbox_frame, text="0-9"); chk_numbers.select(); chk_numbers.pack(side="left", padx=10)
chk_symbols = customtkinter.CTkCheckBox(checkbox_frame, text="!@#$"); chk_symbols.select(); chk_symbols.pack(side="left", padx=10)
customtkinter.CTkButton(pass_tab, text="Generate Password", font=("Helvetica", 16, "bold"), command=create_password).pack(pady=20)
strength_label = customtkinter.CTkLabel(pass_tab, text="Strength: Waiting...", font=("Helvetica", 16)); strength_label.pack(pady=5)


# --- FILE LOCKER TAB ---
file_tab = tabview.tab("File Locker")
customtkinter.CTkLabel(file_tab, text="Secure File & Folder Encryption", font=("Helvetica", 20, "bold")).pack(pady=10)

browse_frame = customtkinter.CTkFrame(file_tab, fg_color="transparent"); browse_frame.pack(pady=5)
customtkinter.CTkButton(browse_frame, text="Select File", command=browse_file).pack(side="left", padx=10)
customtkinter.CTkButton(browse_frame, text="Select Folder", command=browse_folder).pack(side="left", padx=10)

path_label = customtkinter.CTkLabel(file_tab, text="Selected: None", font=("Helvetica", 12), text_color="gray"); path_label.pack(pady=5)

passwords_container = customtkinter.CTkFrame(file_tab, fg_color="transparent"); passwords_container.pack(pady=5)
show_password_var = customtkinter.IntVar(value=0) 
add_layer() 

layer_controls = customtkinter.CTkFrame(file_tab, fg_color="transparent"); layer_controls.pack(pady=5)
customtkinter.CTkButton(layer_controls, text="+ Add Layer", width=100, command=add_layer).pack(side="left", padx=5)
customtkinter.CTkButton(layer_controls, text="- Remove Layer", width=100, command=remove_layer, fg_color="#555555").pack(side="left", padx=5)

option_frame = customtkinter.CTkFrame(file_tab, fg_color="transparent"); option_frame.pack(pady=10)
customtkinter.CTkCheckBox(option_frame, text="Show Passwords", variable=show_password_var, command=toggle_password_visibility).pack(side="left", padx=10)

save_to_vault_var = customtkinter.IntVar(value=0)
customtkinter.CTkCheckBox(option_frame, text="Save to Vault (Must be Unlocked)", variable=save_to_vault_var, text_color="#FFD700").pack(side="left", padx=10)

action_frame = customtkinter.CTkFrame(file_tab, fg_color="transparent"); action_frame.pack(pady=10)
customtkinter.CTkButton(action_frame, text="Lock (Encrypt)", fg_color="#FF4A4A", hover_color="#CC0000", command=encrypt_action).pack(side="left", padx=10)
customtkinter.CTkButton(action_frame, text="Unlock (Decrypt)", fg_color="#00C851", hover_color="#007E33", command=decrypt_action).pack(side="left", padx=10)

locker_status_label = customtkinter.CTkLabel(file_tab, text="", font=("Helvetica", 14)); locker_status_label.pack(pady=10)


# --- PASSWORD VAULT TAB ---
vault_tab = tabview.tab("Password Vault")
customtkinter.CTkLabel(vault_tab, text="Encrypted Local Password Vault", font=("Helvetica", 20, "bold")).pack(pady=10)
customtkinter.CTkLabel(vault_tab, text="⚠️ WARNING: If you forget the Master Password, saved passwords are gone forever.", text_color="#FF4A4A", font=("Helvetica", 12, "bold")).pack(pady=5)

# NEW: The Eye Button UI Design
vault_input_frame = customtkinter.CTkFrame(vault_tab, fg_color="transparent")
vault_input_frame.pack(pady=10)

vault_password_entry = customtkinter.CTkEntry(vault_input_frame, width=260, placeholder_text="Enter Master Password...", show="*")
vault_password_entry.pack(side="left")

btn_vault_eye = customtkinter.CTkButton(vault_input_frame, text="👁️", width=40, fg_color="#444444", hover_color="#666666", command=toggle_vault_eye)
btn_vault_eye.pack(side="left", padx=(5, 0))

vault_action_frame = customtkinter.CTkFrame(vault_tab, fg_color="transparent")
vault_action_frame.pack(pady=10)

customtkinter.CTkButton(vault_action_frame, text="Unlock / Create Vault", command=unlock_vault).pack(side="left", padx=10)
customtkinter.CTkButton(vault_action_frame, text="Lock Vault", fg_color="#FF4A4A", hover_color="#CC0000", command=lock_vault).pack(side="left", padx=10)

# NEW: Change Master Password Button
btn_show_change_pass = customtkinter.CTkButton(vault_action_frame, text="Change Password", fg_color="#FF8C00", hover_color="#CC7000", state="disabled", command=toggle_change_pass_menu)
btn_show_change_pass.pack(side="left", padx=10)

vault_status_label = customtkinter.CTkLabel(vault_tab, text="", font=("Helvetica", 14))
vault_status_label.pack(pady=5)

# NEW: The Hidden Menu to actually change the password
change_pass_frame = customtkinter.CTkFrame(vault_tab, fg_color="#2b2b2b", corner_radius=10)
current_pass_entry = customtkinter.CTkEntry(change_pass_frame, width=220, placeholder_text="Current Master Password...", show="*")
current_pass_entry.pack(pady=5, padx=20)
new_pass_entry = customtkinter.CTkEntry(change_pass_frame, width=220, placeholder_text="New Master Password...", show="*")
new_pass_entry.pack(pady=5, padx=20)
confirm_pass_entry = customtkinter.CTkEntry(change_pass_frame, width=220, placeholder_text="Confirm New Password...", show="*")
confirm_pass_entry.pack(pady=5, padx=20)
customtkinter.CTkButton(change_pass_frame, text="Apply Change", fg_color="#00C851", hover_color="#007E33", command=apply_new_master_password).pack(pady=10)
change_pass_status = customtkinter.CTkLabel(change_pass_frame, text="", font=("Helvetica", 12))
change_pass_status.pack(pady=(0, 5))

vault_textbox = customtkinter.CTkTextbox(vault_tab, width=600, height=200, font=("Courier", 14))
vault_textbox.pack(pady=10)
vault_textbox.insert("0.0", "Vault is locked.\nEnter your Master Password above to view your saved items.")
vault_textbox.configure(state="disabled") 

app.mainloop()