import flet as ft
import socket
import threading
import json
from datetime import datetime

def main(page: ft.Page):
    page.title = "Дельфин — Мессенджер"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#010b1a"
    page.padding = 20

    username = ""
    active_chat = None 
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Хранилище: {"Имя друга": [{"sender": "Я/Имя", "text": "...", "time": "00:00", "read": True/False}]}
    chats_data = {}
    online_users = []

    users_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=10)
    chat_container = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=15)
    
    message_field = ft.TextField(
        hint_text="Выберите чат слева, чтобы начать общение...",
        expand=True,
        border_radius=10,
        bgcolor="#0f172a",
        border_color="#1e40af",
        disabled=True 
    )

    def create_message_bubble(name, text, is_me, time_str, is_read):
        status_ticks = ""
        if is_me:
            status_ticks = " ✓✓" if is_read else " ✓"

        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text(name, size=12, weight="bold", color="#3b82f6" if is_me else "#00ffcc"),
                        ft.Text(text, size=16, color="white"),
                        ft.Row([
                            ft.Text(f"{time_str}{status_ticks}", size=10, color="#94a3b8")
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=2),
                    padding=12,
                    border_radius=10,
                    bgcolor="#1e3a8a" if is_me else "#334155",
                    width=300,
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START
        )

    def refresh_chat_ui():
        chat_container.controls.clear()
        if active_chat and active_chat in chats_data:
            for msg in chats_data[active_chat]:
                is_me = (msg["sender"] == "Я")
                chat_container.controls.append(
                    create_message_bubble(msg["sender"], msg["text"], is_me, msg["time"], msg.get("read", False))
                )
        page.update()

    def load_chat(friend_name):
        nonlocal active_chat
        active_chat = friend_name
        
        try:
            read_pkg = json.dumps({"type": "read_all", "to": friend_name})
            client.sendall(read_pkg.encode('utf-8'))
        except:
            pass
            
        if friend_name in chats_data:
            for m in chats_data[friend_name]:
                if m["sender"] != "Я":
                    m["read"] = True

        if friend_name in online_users:
            message_field.disabled = False
            message_field.hint_text = f"Сообщение для {friend_name}..."
        else:
            message_field.disabled = True
            message_field.hint_text = f"{friend_name} оффлайн..."
            
        refresh_chat_ui()
        update_users_ui()

    def update_users_ui():
        users_column.controls.clear()
        users_column.controls.append(ft.Text("Чаты онлайн", size=18, weight="bold", color="#3b82f6"))
        
        for u in online_users:
            if u != username:
                is_current = (u == active_chat)
                users_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(name="person", color="#3b82f6" if is_current else "white", size=20),
                            ft.Text(u, size=16, color="white", weight="bold" if is_current else "normal"),
                        ], alignment=ft.MainAxisAlignment.START, spacing=10),
                        padding=12,
                        border_radius=8,
                        bgcolor="#1e40af" if is_current else "#1e293b",
                        width=190,  
                        on_click=lambda e, user=u: load_chat(user),
                        ink=True
                    )
                )
                
        if len(users_column.controls) == 1:
            users_column.controls.append(ft.Text("Никого нет в сети", size=14, color="gray"))
            
        if active_chat and active_chat not in online_users:
            message_field.disabled = True
            message_field.hint_text = f"{active_chat} вышел из сети"
            
        page.update()

    def receive_messages():
        while True:
            try:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    break
            except:
                break
                
            try:
                raw_messages = data.replace("}{", "}\n\n{").split("\n\n")
                for raw_msg in raw_messages:
                    if not raw_msg.strip():
                        continue
                    msg = json.loads(raw_msg)
                    
                    if msg["type"] == "users":
                        nonlocal online_users
                        online_users = msg["list"]
                        update_users_ui()
                        
                    elif msg["type"] == "message":
                        from_user = msg["from"]
                        text = msg["text"]
                        t_str = msg["time"]
                        
                        if from_user not in chats_data:
                            chats_data[from_user] = []
                            
                        is_chat_open = (active_chat == from_user)
                        chats_data[from_user].append({
                            "sender": from_user, 
                            "text": text, 
                            "time": t_str, 
                            "read": is_chat_open
                        })
                        
                        if is_chat_open:
                            try:
                                read_pkg = json.dumps({"type": "read_all", "to": from_user})
                                client.sendall(read_pkg.encode('utf-8'))
                            except:
                                pass
                            refresh_chat_ui()
                        page.update()
                        
                    elif msg["type"] == "read_all":
                        from_user = msg["from"]
                        if from_user in chats_data:
                            for m in chats_data[from_user]:
                                if m["sender"] == "Я":
                                    m["read"] = True 
                        if active_chat == from_user:
                            refresh_chat_ui() 
            except Exception as e:
                print(f"Ошибка чтения пакета: {e}")

    def send_click(e):
        if message_field.value and active_chat:
            try:
                current_time = datetime.now().strftime("%H:%M")
                out_msg = json.dumps({
                    "type": "message",
                    "to": active_chat,
                    "text": message_field.value,
                    "time": current_time
                })
                client.sendall(out_msg.encode('utf-8'))
                
                if active_chat not in chats_data:
                    chats_data[active_chat] = []
                chats_data[active_chat].append({
                    "sender": "Я", 
                    "text": message_field.value, 
                    "time": current_time, 
                    "read": False
                })
                
                refresh_chat_ui()
                message_field.value = ""
                page.update()
            except Exception as send_err:
                chat_container.controls.append(ft.Text(f"Сбой отправки: {send_err}", color="red"))
                page.update()

    send_button = ft.ElevatedButton("Отправить", on_click=send_click, bgcolor="#3b82f6", color="white")

    def join_click(e):
        nonlocal username
        if name_field.value:
            username = name_field.value.strip()
            
            # Умное подключение
            HOST_EXTERNAL = 'gorshkov.ddns.net'
            HOST_LOCAL = '127.0.0.1'
            PORT = 5555

            try:
                print(f"Попытка подключения к внешнему серверу: {HOST_EXTERNAL}")
                client.connect((HOST_EXTERNAL, PORT))
            except:
                print("Внешний сервер недоступен, подключаюсь локально...")
                client.connect((HOST_LOCAL, PORT))
            
            login_data = json.dumps({"type": "login", "username": username})
            client.sendall(login_data.encode('utf-8'))
            
            threading.Thread(target=receive_messages, daemon=True).start()
            page.clean()
            
            page.add(
                ft.Row([
                    ft.Container(
                        content=users_column, 
                        width=220, 
                        bgcolor="#0f172a", 
                        padding=15, 
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Container(content=chat_container, expand=True),
                        ft.Row([message_field, send_button], spacing=10)
                    ], expand=True)
                ], expand=True)
            )
            update_users_ui()
            page.update()

    name_field = ft.TextField(label="Ваше имя", border_radius=10, width=300)
    
    page.add(
        ft.Column([
            ft.Text("Дельфин", size=45, weight="bold", color="#3b82f6"),
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "«Это не просто мессенджер. Мы пробуем создать что-то новое — тихую гавань в океане цифрового шума, где каждый сигнал наполнен искренностью.»",
                        italic=True,
                        size=14,
                        color="#94a3b8",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "— Сергей Горшков",
                        size=12,
                        weight="bold",
                        color="#64748b",
                        text_align=ft.TextAlign.RIGHT
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=380,
                margin=ft.margin.only(top=10, bottom=30)
            ),
            name_field,
            ft.Container(height=10),
            ft.ElevatedButton("Войти в чат", on_click=join_click, bgcolor="#3b82f6", color="white", width=200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    )

ft.app(target=main)