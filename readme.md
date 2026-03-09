# 🛡️ Ultimate Privacy Toolkit

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Security](https://img.shields.io/badge/Military_Grade-AES--256--GCM-red.svg)
![Portable](https://img.shields.io/badge/Portable-Any_Drive-success.svg)

Welcome to the **Ultimate Privacy Toolkit** — your all-in-one, completely offline, portable digital fortress. 

Whether you need to generate uncrackable passwords, lock sensitive files and folders behind multiple layers of military-grade encryption, or safely store those passwords in a hidden local vault, this app does it all instantly. **No cloud, no subscriptions, no backdoors. Your data belongs entirely to you.**

---

## ⚡ The Power & Efficiency Behind the App
Most "folder locker" apps just hide your files from the computer's search menu. **This app is different.** 

* **Onion Encryption:** You can lock a single file behind up to 5 different passwords. The app mathematically wraps your file in a secure layer, then wraps *that* layer in another layer. To unlock it, you must provide the exact passwords in the exact reverse order. 
* **Seamless Folder Zipping:** Cryptography algorithms normally can't encrypt "folders." This app bypasses that efficiently by silently compressing your folder into a `.zip`, encrypting the zip, and shredding the original folder in the blink of an eye. When you unlock it, it flawlessly unzips it back to normal.
* **100% Portable:** There is no heavy installation process. Put the `.exe` on a USB stick or an external drive, and you can carry your encryption station and your Password Vault in your pocket, anywhere you go.

---

## ✨ Features

### 🔑 1. Smart Password Generator
* **True Randomness:** Uses cryptographic randomness (`secrets` module) instead of predictable math formulas.
* **Live Strength Checker:** Integrates the industry-standard `zxcvbn` algorithm to tell you exactly how strong a password is against real-world hacker dictionary attacks.

### 🔒 2. Multi-Layer File Locker
* **Military-Grade Math:** Uses `AES-256-GCM` encryption. Your password is mathematically smashed 480,000 times (`PBKDF2`) to create an uncrackable digital key.
* **Secure Deletion:** Original files are wiped from your drive the moment the `.locked` file is generated. 

### 🗄️ 3. Encrypted Local Password Vault
* **Never Forget a Password:** Check the "Save to Vault" box when locking a file, and the app will automatically record the file name and all the passwords you used.
* **Master Lock:** The entire vault is encrypted into a local file (`vault.enc`). You can only view your saved passwords by entering your 1 Master Password.
* **Quick Tools:** Features an "👁️" button to double-check your master password, an instant "Lock Vault" button to hide your screen, and a secure menu to change your Master Password at any time.

---

## 🚀 Quick Start Guide (How to Use)

1. **Launch the App:** Open the `.exe` file (No installation required!).
2. **Setup your Vault:** Go to the *Password Vault* tab, type a Master Password, and click **Unlock / Create**. 
3. **Lock a File/Folder:** 
   * Go to the *File Locker* tab. Select what you want to hide.
   * Add 1 (or more!) passwords. 
   * Check **Save to Vault** so you don't lose them!
   * Click **Lock (Encrypt)**. Watch your file turn into a secure `.locked` file!
4. **Unlock a File:** Select the `.locked` file, enter your exact passwords, and click **Unlock**.

---

## ⚠️ Crucial Security Warning
This app was built with true privacy in mind. **THERE ARE NO BACKDOORS.**
* The app does not connect to the internet. It does not send your passwords to us.
* **If you lose your Master Password, your Password Vault cannot be recovered.** 
* **If you forget the passwords used to lock a file, that file is mathematically locked forever.**
* *Please test the app on a dummy text file first to get comfortable with how the layering and vault system works before encrypting your important family photos!*

---

## 🛠️ For Developers: How to Run & Build

If you want to view the source code or compile the app yourself:

**1. Clone the repository and install requirements:**
```bash
git clone https://github.com/Ibrahim71Reza/UltimateLocker.git
cd UltimateLocker
pip install customtkinter cryptography zxcvbn
```

**2. Run the Python script directly:**
```bash
python main.py
```

**3. Build the Portable `.exe`:**
We recommend using `auto-py-to-exe` for a clean build process:
1. `pip install auto-py-to-exe`
2. Run `auto-py-to-exe` in your terminal.
3. Select `main.py` as your script.
4. Select **One File** and **Window Based (Hide the Console)**.
5. **CRITICAL:** Under the *Advanced* tab, find `--collect-all` and type `customtkinter`.
6. Click Convert!

---

## 🤝 Contributing
Feel free to fork this project, submit pull requests, or send feature ideas via the Issues tab!

## 📝 License
This project is [MIT](https://choosealicense.com/licenses/mit/) licensed. Free to use, modify, and distribute!