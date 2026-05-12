import socket
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import os
from Crypto.Cipher import AES

HOST = '172.15.65.49'
PORT = 12345

AES_KEY = b'MySecretKey12345'   

s = None

def encrypt(plainbytes):
    """Encrypt bytes → nonce(16) + tag(16) + ciphertext."""
    cipher = AES.new(AES_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plainbytes)
    return cipher.nonce + tag + ciphertext

def decrypt(blob):
    """Decrypt blob produced by encrypt(). Raises ValueError if tampered."""
    nonce      = blob[:16]
    tag        = blob[16:32]
    ciphertext = blob[32:]
    cipher = AES.new(AES_KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

def recv_exact(n):
    """Receive exactly n bytes from the global socket s."""
    data = b''
    while len(data) < n:
        chunk = s.recv(min(4096, n - len(data)))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return data

def send_encrypted(plainbytes):
    """Encrypt and send with a 4-byte length prefix."""
    blob = encrypt(plainbytes)
    s.sendall(len(blob).to_bytes(4, 'big') + blob)

def recv_encrypted():
    """Read one length-prefixed encrypted message and return plainbytes."""
    raw_len = recv_exact(4)
    length  = int.from_bytes(raw_len, 'big')
    blob    = recv_exact(length)
    return decrypt(blob)


def connect_and_login():
    global s
    username = entry_user.get().strip()
    password = entry_pass.get().strip()
    target   = entry_target.get().strip()

    if not username or not password or not target:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        # Handshake & login are still plain text (same as before)
        s.recv(1024)
        s.sendall(b'Hello')
        s.recv(1024)
        s.sendall(username.encode())
        s.recv(1024)
        s.sendall(password.encode())
        result = s.recv(1024).decode().strip()

        if 'successful' not in result.lower():
            messagebox.showerror("Login Failed", result)
            s.close()
            return

        s.recv(1024)
        s.sendall(target.encode())
        status = s.recv(1024).decode().strip()

        auth_win.destroy()
        open_chat(username, target, status)

    except Exception as e:
        messagebox.showerror("Connection Error", str(e))


def auth_window():
    global auth_win, entry_user, entry_pass, entry_target
    auth_win = tk.Tk()
    auth_win.title("Login")
    auth_win.resizable(False, False)

    tk.Label(auth_win, text="Username:").grid(row=0, column=0, padx=10, pady=6, sticky="e")
    entry_user = tk.Entry(auth_win, width=24)
    entry_user.grid(row=0, column=1, padx=10, pady=6)

    tk.Label(auth_win, text="Password:").grid(row=1, column=0, padx=10, pady=6, sticky="e")
    entry_pass = tk.Entry(auth_win, show="*", width=24)
    entry_pass.grid(row=1, column=1, padx=10, pady=6)

    tk.Label(auth_win, text="Chat with:").grid(row=2, column=0, padx=10, pady=6, sticky="e")
    entry_target = tk.Entry(auth_win, width=24)
    entry_target.grid(row=2, column=1, padx=10, pady=6)

    tk.Button(auth_win, text="Connect", width=16, command=connect_and_login)\
        .grid(row=3, column=0, columnspan=2, pady=12)

    auth_win.mainloop()


def open_chat(username, target, status_msg):
    chat_win = tk.Tk()
    chat_win.title(f"Chat — {username}")
    chat_win.resizable(False, False)

    msg_box = tk.Text(chat_win, width=50, height=20, state="disabled",
                      wrap="word", relief="sunken", bd=1)
    msg_box.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 4))

    scrollbar = tk.Scrollbar(chat_win, command=msg_box.yview)
    scrollbar.grid(row=0, column=3, sticky="ns", pady=(10, 4))
    msg_box.config(yscrollcommand=scrollbar.set)

    def append(text):
        msg_box.config(state="normal")
        msg_box.insert("end", text + "\n")
        msg_box.config(state="disabled")
        msg_box.see("end")

    append(f"[{status_msg}]")
    append("[AES Encryption is ON]")

    mode = tk.IntVar(value=1)

    mode_frame = tk.LabelFrame(chat_win, text="Mode", padx=6, pady=4)
    mode_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(4, 0), sticky="w")

    tk.Radiobutton(mode_frame, text="1 - Send Text", variable=mode, value=1,
                   command=lambda: on_mode_change()).grid(row=0, column=0, padx=8)
    tk.Radiobutton(mode_frame, text="2 - Send File", variable=mode, value=2,
                   command=lambda: on_mode_change()).grid(row=0, column=1, padx=8)

    entry_msg = tk.Entry(chat_win, width=38)
    entry_msg.grid(row=2, column=0, padx=(10, 4), pady=8)

    btn_action = tk.Button(chat_win, text="Send", width=10)
    btn_action.grid(row=2, column=1, columnspan=2, padx=(0, 10), pady=8)

    def on_mode_change():
        if mode.get() == 1:
            entry_msg.config(state="normal")
            btn_action.config(text="Send", command=send_text)
            append("[Mode: Text]")
        else:
            entry_msg.config(state="disabled")
            btn_action.config(text="Choose File", command=send_file)
            append("[Mode: File Transfer]")

    def send_text(_=None):
        msg = entry_msg.get().strip()
        if not msg:
            return
        entry_msg.delete(0, "end")
        send_encrypted(msg.encode())          # <-- encrypted send
        append(f"You: {msg}")
        if msg.lower() == 'bye':
            chat_win.destroy()

    entry_msg.bind("<Return>", send_text)
    btn_action.config(command=send_text)

    def send_file():
        filepath = filedialog.askopenfilename(title="Choose a file to send")
        if not filepath:
            return

        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
        filesize = len(file_bytes)

        header  = f'FILE:{filename}:{filesize}:'.encode()
        payload = header + file_bytes
        send_encrypted(payload)               # <-- encrypted send

        append(f"[You sent file: {filename} ({filesize} bytes)] [Encrypted]")

    def receive():
        while True:
            try:
                plain = recv_encrypted()      # <-- encrypted receive
            except Exception:
                append("[Disconnected]")
                break

            # Incoming file
            if plain.startswith(b'FILE:'):
                first      = plain.index(b':')
                second     = plain.index(b':', first + 1)
                third      = plain.index(b':', second + 1)
                header_end = third + 1

                parts    = plain[:header_end].decode().split(':')
                filename = parts[1]
                filesize = int(parts[2])
                file_data = plain[header_end: header_end + filesize]

                def save_file(fd=file_data, fn=filename):
                    save_path = filedialog.asksaveasfilename(
                        title=f"Save file from {target}",
                        initialfile=fn
                    )
                    if save_path:
                        with open(save_path, 'wb') as wf:
                            wf.write(fd)
                        append(f"[File received: {fn} — saved to {save_path}] [Decrypted OK]")
                    else:
                        append(f"[File received: {fn} — not saved]")

                chat_win.after(0, save_file)
                continue

            # Plain text message
            text = plain.decode(errors='ignore').strip()
            if text not in ('[delivered]', '[file_delivered]'):
                append(text)

    threading.Thread(target=receive, daemon=True).start()
    chat_win.mainloop()


auth_window()
