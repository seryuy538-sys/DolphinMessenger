import socket

# Создаем клиентский сокет
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Подключаемся к нашему серверу на локальном компьютере
client.connect(('127.0.0.1', 5555))

# Отправляем сообщение
message = "Привет! Это мой первый мессенджер!"
client.send(message.encode('utf-8'))

# Получаем ответ от сервера
response = client.recv(1024).decode('utf-8')
print(f"Сервер ответил: {response}")

client.close()