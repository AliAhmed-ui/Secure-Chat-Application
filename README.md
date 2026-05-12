# Secure-Chat-Application
A light-weight client server chat application inspired by platforms like WhatsApp, Developed in python using socket programming, multithreading, GUI development with Tkinter, and AES encryption for secure communication.
# Secure Chat Application

This project was created as a semester project for a Network Programming course and demonstrates real-time messaging, encrypted communication, authentication, and file transfer over TCP sockets while ensuring concurrency.

---

## Features

* Real-time one-to-one messaging
* AES encrypted communication using AES-EAX mode
* GUI-based chat interface using Tkinter
* Multi-client server handling with threading
* User authentication system
* File transfer support
* Online/offline user detection
* Delivery acknowledgements
* Secure encrypted file sharing
* Length-prefixed packet communication for reliable data transfer

---

## Technologies Used

* Python
* Socket Programming
* Threading
* Tkinter
* PyCryptodome (AES Encryption)

---

## Project Structure

```bash
├── Clientcode.py     # Client-side GUI application
├── server.py         # Multi-threaded server
├── usernames.txt     # Stored usernames
├── pass.txt          # Stored passwords
└── README.md
```

---

## How It Works

### Server

The server:

* Accepts multiple client connections
* Authenticates users using stored credentials
* Maintains a list of online users
* Forwards encrypted messages/files between clients
* Handles concurrent communication using threads

### Client

The client:

* Provides a graphical chat interface
* Connects to the server through TCP sockets
* Encrypts all outgoing messages/files using AES
* Decrypts incoming encrypted data
* Supports both text messaging and file transfer

---

## Encryption

The application uses AES encryption in EAX mode for:

* Confidentiality
* Integrity verification
* Tamper detection

Each encrypted packet contains:

```text
Nonce (16 bytes) + Authentication Tag (16 bytes) + Ciphertext
```

Messages are transmitted using:

```text
4-byte Length Prefix + Encrypted Payload
```

This ensures reliable and secure packet transmission.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/secure-chat-app.git
cd secure-chat-app
```

### 2. Install Dependencies

```bash
pip install pycryptodome
pip install tkinter    #if you are on linux you may need to install tkinter seperately
```

---

## Running the Project

### Start the Server

```bash
python server.py
```

### Run the Client

```bash
python Clientcode.py
```

---

## Authentication

The server authenticates users using:

* `usernames.txt`
* `pass.txt`

Each username corresponds to the password at the same index.

Example:

### usernames.txt

```text
ali
ahmed
```

### pass.txt

```text
1234
abcd
```

---

## File Transfer

The application supports encrypted file transfer between users.

Files are sent in the following format:

```text
FILE:<filename>:<filesize>:<binary_data>
```

The receiver can choose where to save the file locally.

---

## Concepts Demonstrated

This project demonstrates:

* TCP socket programming
* Client-server architecture
* Multithreading
* GUI programming
* Secure communication
* Cryptography basics
* File handling
* Concurrent client management

---

## Future Improvements

Possible future enhancements:

* Group chats
* Message storage/database integration
* Better UI/UX
* User registration system
* End-to-end encryption
* Voice/video calling
* Cross-platform deployment
* Cloud hosting

---

## Screenshots

Add screenshots of:

* Login window
* Chat interface
* File transfer
* Server terminal

---

## Author

**Syed Ali Ahmed Shah**
BS Electrical Engineering (Embedded Systems)
FAST-NUCES

---

## License

This project is for educational purposes and semester project demonstration.
