import socket
import threading
import json

clients = {} # Словарь {Имя_Пользователя: Сокет}

def broadcast_users():
    """Отправляет актуальный список пользователей всем, кто в сети"""
    user_list = list(clients.keys())
    msg = json.dumps({"type": "users", "list": user_list})
    for sock in clients.values():
        try:
            sock.sendall(msg.encode('utf-8'))
        except:
            pass

def handle_client(client_socket):
    username = None
    while True:
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break
        except:
            break
            
        try:
            # Защита от склеивания пакетов в TCP-потоке
            raw_messages = data.replace("}{", "}\n\n{").split("\n\n")
            for raw_msg in raw_messages:
                if not raw_msg.strip():
                    continue
                msg = json.loads(raw_msg)
                
                # Вход в сеть
                if msg["type"] == "login":
                    username = msg["username"].strip()
                    clients[username] = client_socket
                    print(f"Пользователь {username} вошел в сеть.")
                    broadcast_users()
                    
                # Пересылка сообщения конкретному другу
                elif msg["type"] == "message":
                    to_user = msg["to"]
                    if to_user in clients:
                        forward_msg = json.dumps({
                            "type": "message", 
                            "from": username, 
                            "text": msg["text"],
                            "time": msg["time"]
                        })
                        clients[to_user].sendall(forward_msg.encode('utf-8'))
                        
                # Пересылка статуса прочтения (друг открыл чат)
                elif msg["type"] == "read_all":
                    to_user = msg["to"]
                    if to_user in clients:
                        forward_read = json.dumps({"type": "read_all", "from": username})
                        clients[to_user].sendall(forward_read.encode('utf-8'))
                        
        except Exception as e:
            print(f"Ошибка обработки на сервере: {e}")

    if username and username in clients:
        del clients[username]
        print(f"Пользователь {username} вышел из сети.")
        broadcast_users()
    client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen()
    print("Сервер Дельфина запущен и ожидает подключений...")
    
    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_server()