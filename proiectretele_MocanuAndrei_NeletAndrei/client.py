import socket

class RemoteExecutionClient:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print("Conectat la server.")

    def authenticate(self):
        username = input(self.client_socket.recv(1024).decode('utf-8'))
        self.client_socket.sendall(username.encode('utf-8'))
        password = input(self.client_socket.recv(1024).decode('utf-8'))
        self.client_socket.sendall(password.encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        print(response)
        return "succes" in response

    def send_command(self, command):
        self.client_socket.sendall(command.encode('utf-8'))

    def receive_response(self):
        return self.client_socket.recv(4096).decode('utf-8')

    def close_connection(self):
        self.client_socket.close()
        print("Conexiune inchisa")

    def interactive_menu(self):
        menu_options = {
            "1": "Adauga un nou script",
            "2": "Executa un script",
            "3": "Sterge un script",
            "4": "Lista scripturi",
            "5": "Lista clienti",
            "6": "Adauga secventa de comenzi",
            "7": "Executa secventa de comenzi", 
            "8": "Citeste continutul unui fisier", 
            "9": "Exit"
        }

        while True:
            print("\nOptiuni:")
            for key in sorted(menu_options.keys()):
                print(f"{key}. {menu_options[key]}")

            selection = input("Selecteaza o optiune: ")
            if selection == '1':
                script_name = input("Numele scriptului: ")
                script_content = input("Content script: ")
                self.send_command(f"REGISTER {script_name} {script_content}")
                print(self.receive_response())
            elif selection == '2':
                script_name = input("Numele scriptului pentru rulare: ")
                self.send_command(f"EXECUTE {script_name}")
                print(self.receive_response())
            elif selection == '3':
                script_name = input("Numele scriptului pentru sterger: ")
                self.send_command(f"DELETE {script_name}")
                print(self.receive_response())
            elif selection == '4':
                self.send_command("LIST")
                print(self.receive_response())
            elif selection == '5':
                self.send_command("LIST_CLIENTS")
                print(self.receive_response())
            elif selection == '6':
                self.register_command_sequence()
            elif selection == '7':
                self.execute_command_sequence() 
            elif selection == '8':
                self.read_file_content()
            elif selection == '9':
                self.close_connection()
                break
            else:
                print("Invalid option. Please choose a valid number.")


    def register_command_sequence(self):
        sequence_name = input("Numele secventei de comenzi: ")
        script_names = input("Numele scripturilor (separate prin spațiu): ").split()
        self.send_command(f"REGISTER_SEQUENCE {sequence_name} {' '.join(script_names)}")
        print(self.receive_response())

    def execute_command_sequence(self):
        sequence_name = input("Numele secventei de comenzi pentru executie: ")
        input_file = input("Numele fisierului de intrare (optional): ")

        input_data = b""
        if input_file:
            try:
                with open(input_file, 'rb') as f:
                    input_data = f.read()
            except FileNotFoundError:
                print(f"Fisierul {input_file} nu exista.")

        self.send_command(f"EXECUTE_SEQUENCE {sequence_name}")
        self.client_socket.sendall(input_data)
        print(self.receive_response())

    def read_file_content(self):
        file_path = input("Introduceti calea fisierului: ")
        self.send_command(f"READ_FILE {file_path}")
        print(self.receive_response())

if __name__ == "__main__":
    client = RemoteExecutionClient()
    client.connect_to_server()
    if client.authenticate():
        client.interactive_menu()

