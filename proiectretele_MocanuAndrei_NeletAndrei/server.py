import socket
import threading
import subprocess
import json
import os

class RemoteExecutionServer:
    def __init__(self, host="localhost", port=5000, storage_file="scripts.json"):
        self.host = host
        self.port = port
        self.storage_file = storage_file
        self.client_scripts = self.load_scripts()
        self.users = {
            'cont1': 'parola1',
            'cont2': 'parola2',
            'cont3': 'parola3'
        }
        self.lock = threading.Lock()

    def start_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        try:
            while True:
                client, address = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(client, address)).start()
        finally:
            self.sock.close()

    def handle_client(self, client, address):
        print(f"Connected with {address}")
        username = self.authenticate_client(client)
        if not username:
            print(f"Authentication failed for {address}")
            client.close()
            return

        if username not in self.client_scripts:
            self.client_scripts[username] = {}
        print(f"Authenticated {address} as {username}")

        while True:
            try:
                data = client.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Received data from {address}: {data}")
                command, *args = data.split()
                if command == "REGISTER":
                    self.register_script(username, client, *args)
                elif command == "EXECUTE":
                    self.execute_scripts(username, client, *args)
                elif command == "DELETE":
                    self.delete_command(username, client, *args)
                elif command == "LIST":
                    self.list_scripts(username, client)
                elif command == "LIST_CLIENTS":
                    self.list_clients(client)
                elif command == "REGISTER_SEQUENCE":
                    self.register_command_sequence(username, client, *args)
                elif command == "EXECUTE_SEQUENCE":
                    self.execute_command_sequence(username, client, *args)
                elif command == "READ_FILE":
                    self.read_file(client, *args)
            except ConnectionResetError:
                print(f"Connection reset by {address}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
        client.close()
        print(f"Connection closed with {address}")

    def authenticate_client(self, client):
        client.sendall("User? ".encode('utf-8'))
        username = client.recv(1024).decode('utf-8').strip()
        client.sendall("Parola? ".encode('utf-8'))
        password = client.recv(1024).decode('utf-8').strip()

        if username in self.users and self.users[username] == password:
            client.sendall("Autentificare cu succes.\n".encode('utf-8'))
            return username
        else:
            client.sendall("Autentificare esuata.\n".encode('utf-8'))
            return None

    def register_script(self, username, client, script_name, *script_content):
        script_content = " ".join(script_content)
        with self.lock:
            self.client_scripts[username][script_name] = script_content
            self.save_scripts()
            client.sendall(f"Script {script_name} inregistrat.\n".encode('utf-8'))

    def execute_scripts(self, username, client, *script_names):
        input_data = b""
        for script_name in script_names:
            if script_name in self.client_scripts[username]:
                script = self.client_scripts[username][script_name]
                result = subprocess.run(script, input=input_data, capture_output=True, shell=True, text=True)
                input_data = result.stdout.encode()
            else:
                client.sendall(f"Scriptul {script_name} nu a fost gasit.\n".encode('utf-8'))
                return
        client.sendall(input_data)

    def delete_command(self, username, client, command_name):
        with self.lock:
            if command_name in self.client_scripts[username]:
                del self.client_scripts[username][command_name]
                self.save_scripts()
                client.sendall(f"Command {command_name} deleted.\n".encode('utf-8'))
            else:
                client.sendall(f"Command {command_name} not found.\n".encode('utf-8'))

    def list_scripts(self, username, client):
        with self.lock:
            scripts = self.client_scripts.get(username, {})
            if scripts:
                response = "\n".join(scripts.keys()) + "\n"
            else:
                response = "Lista este goala\n"
            client.sendall(response.encode('utf-8'))

    def list_clients(self, client):
        with self.lock:
            response = ""
            for username, scripts in self.client_scripts.items():
                script_list = ", ".join(scripts.keys())
                response += f"{username}: {script_list}\n"
            if not response:
                response = "Niciun client connectat.\n"
            client.sendall(response.encode('utf-8'))

    def load_scripts(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {}

    def save_scripts(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.client_scripts, f, indent=4)

    def register_command_sequence(self, username, client, sequence_name, *script_names):
        if len(script_names) < 2:
            client.sendall("O secventa de comenzi trebuie sa contina cel putin doua scripturi.\n".encode('utf-8'))
            return

        for script_name in script_names:
            if script_name not in self.client_scripts[username]:
                client.sendall(f"Scriptul {script_name} nu a fost gasit.\n".encode('utf-8'))
                return

        with self.lock:
            self.client_scripts[username][sequence_name] = script_names
            self.save_scripts()
            client.sendall(f"Secventa de comenzi {sequence_name} inregistrata.\n".encode('utf-8'))

    def execute_command_sequence(self, username, client, sequence_name):
        if sequence_name not in self.client_scripts[username]:
            client.sendall(f"Secventa de comenzi {sequence_name} nu a fost gasita.\n".encode('utf-8'))
            return

        print(f"Secventa de comenzi {sequence_name} gasita.")
        client.sendall(f"Secventa de comenzi {sequence_name} gasita.\n".encode('utf-8'))

        script_names = self.client_scripts[username][sequence_name]
        input_data = b""
    
        print("Incepem primirea datelor de intrare de la client.")
        client.sendall("Incepem primirea datelor de intrare de la client.\n".encode('utf-8'))
    
        while True:
            part = client.recv(4096)
            if not part:
                break
            input_data += part
    
        print(f"Date de intrare primite: {input_data.decode('utf-8')}")
        client.sendall(f"Date de intrare primite: {input_data.decode('utf-8')}\n".encode('utf-8'))

        for script_name in script_names:
            print(f"Executam scriptul: {script_name}")
            client.sendall(f"Executam scriptul: {script_name}\n".encode('utf-8'))
        
            script = self.client_scripts[username][script_name]
        
            print(f"Script: {script}")
            client.sendall(f"Script: {script}\n".encode('utf-8'))
        
            try:
                result = subprocess.run(script, input=input_data, capture_output=True, shell=True, text=True)
            except Exception as e:
                error_message = f"Eroare la executarea comenzii: {script_name} cu mesajul: {str(e)}"
                print(error_message)
                client.sendall(error_message.encode('utf-8'))
                return
        
            if result.returncode != 0:
                error_message = f"Eroare la executarea comenzii: {script_name} cu mesajul: {result.stderr}"
                print(error_message)
                client.sendall(error_message.encode('utf-8'))
                return
        
            print(f"Rezultatul comenzii {script_name}: {result.stdout}")
            client.sendall(f"Rezultatul comenzii {script_name}: {result.stdout}\n".encode('utf-8'))
        
            input_data = result.stdout.encode()

        client.sendall(input_data)
        print("Secventa de comenzi a fost executata cu succes.")
        client.sendall("Secventa de comenzi a fost executata cu succes.\n".encode('utf-8'))

    def read_file(self, client, file_path):
        try:
            with open(file_path, 'r') as file:
                data = file.read()
                client.sendall(data.encode('utf-8'))
        except FileNotFoundError:
            client.sendall(f"Fisierul {file_path} nu exista.\n".encode('utf-8'))

if __name__ == "__main__":
    server = RemoteExecutionServer()
    server.start_server()




