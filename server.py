import socket
import threading
from Crypto.Cipher import AES

HOST = '0.0.0.0'
PORT  = 12345
AES_KEY = b'MySecretKey12345' 

clients      = {}
clients_lock = threading.Lock()

def load_credentials():
    with open("/home/aliahmed/MEGA/Semester 8/Network Programming/Project/usernames.txt", "r") as f:
        usernames = [line.strip() for line in f]
    with open("/home/aliahmed/MEGA/Semester 8/Network Programming/Project/pass.txt", "r") as f:
        passwords = [line.strip() for line in f]
    return usernames, passwords

def encrypt(plainbytes):
    """
    Encrypts bytes using AES-EAX.
    Returns:  nonce (16) + tag (16) + ciphertext
    The receiver needs all three pieces to decrypt.
    """
    cipher = AES.new(AES_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plainbytes)
    return cipher.nonce + tag + ciphertext          # fixed 32-byte prefix

def decrypt(blob):
    """
    Decrypts a blob produced by encrypt().
    blob = nonce (16) + tag (16) + ciphertext
    Returns the original plainbytes, or raises ValueError if tampered.
    """
    nonce      = blob[:16]
    tag        = blob[16:32]
    ciphertext = blob[32:]
    cipher = AES.new(AES_KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

def recv_exact(sock, n):
    """Receive exactly n bytes."""
    data = b''
    while len(data) < n:
        chunk = sock.recv(min(4096, n - len(data)))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return data

def send_encrypted(sock, plainbytes):
    """
    Encrypts plainbytes, then sends:
      4-byte length prefix  (so receiver knows how many bytes to read)
      + encrypted blob
    """
    blob = encrypt(plainbytes)
    length_prefix = len(blob).to_bytes(4, 'big')
    sock.sendall(length_prefix + blob)

def recv_encrypted(sock):
    """
    Reads a length-prefixed encrypted blob and returns the decrypted bytes.
    """
    raw_len = recv_exact(sock, 4)
    length  = int.from_bytes(raw_len, 'big')
    blob    = recv_exact(sock, length)
    return decrypt(blob)

def clientThread(sock, addr):
    print(f'[+] Connected by {addr}')

    sock.sendall(b'Welcome to Chat Server\n')
    buff = sock.recv(80)
    if not buff:
        sock.close()
        return
    print(f'[handshake] client said: {buff.decode().strip()}')

    sock.sendall(b'Enter username: ')
    Name = sock.recv(1024).decode().strip()
    sock.sendall(b'Enter password: ')
    password = sock.recv(1024).decode().strip()

    usernames, passwords = load_credentials()
    if Name in usernames:
        index = usernames.index(Name)
        if password == passwords[index]:
            sock.sendall(b'Login successful\n')
        else:
            sock.sendall(b'Wrong password\n')
            sock.close()
            return
    else:
        sock.sendall(b'User not found\n')
        sock.close()
        return

    with clients_lock:
        clients[Name] = sock
    print(f'[+] {Name} logged in. Online: {list(clients.keys())}')

    sock.sendall(b'Enter target username to chat with: ')
    target = sock.recv(1024).decode().strip()

    with clients_lock:
        target_online = target in clients

    if target_online:
        sock.sendall(f'User {target} is online. Start chatting!\n'.encode())
    else:
        sock.sendall(f'User {target} is offline. Messages will be stored until they connect.\n'.encode())

    while True:
        try:
            plain = recv_encrypted(sock)
        except Exception:
            break

        if plain.startswith(b'FILE:'):
            try:
                first      = plain.index(b':')
                second     = plain.index(b':', first + 1)
                third      = plain.index(b':', second + 1)
                header_end = third + 1

                header_str = plain[:header_end].decode()
                parts      = header_str.split(':')
                filename   = parts[1]
                filesize   = int(parts[2])
                file_data  = plain[header_end: header_end + filesize]

                with clients_lock:
                    target_sock = clients.get(target)

                if target_sock:
                    send_encrypted(target_sock, plain)   # forward same payload
                    send_encrypted(sock, b'[file_delivered]')
                    print(f'[*] File "{filename}" ({filesize}B) {Name} -> {target}')
                else:
                    send_encrypted(sock, f'User {target} is offline. Cannot send file.'.encode())

            except Exception as e:
                print(f'[!] File transfer error: {e}')
                send_encrypted(sock, b'File transfer failed on server.')
            continue

        msg = plain.decode(errors='ignore').strip()
        print(f'[msg] {Name} -> {target}: {msg}')

        if msg.lower() == 'bye':
            send_encrypted(sock, b'Goodbye!')
            break

        with clients_lock:
            target_sock = clients.get(target)

        if target_sock:
            try:
                send_encrypted(target_sock, f'{Name}: {msg}'.encode())
                send_encrypted(sock, b'[delivered]')
            except Exception:
                send_encrypted(sock, b'Failed to deliver message')
        else:
            send_encrypted(sock, f'User {target} is offline'.encode())

    with clients_lock:
        if Name in clients:
            del clients[Name]
    print(f'[-] {Name} disconnected. Online: {list(clients.keys())}')
    sock.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f'[*] Server listening on {HOST}:{PORT}')

    while True:
        print('[*] Waiting for connection...')
        conn, addr = s.accept()
        threading.Thread(target=clientThread, args=(conn, addr), daemon=True).start()
