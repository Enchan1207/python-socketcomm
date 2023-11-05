#
# ちょっとしたチャットサーバ
#
# selectによるクライアントの多重化とコネクション管理のテスト
#

import select
import socket
import sys
import textwrap
from datetime import datetime
from typing import List


def main() -> int:
    # 構成
    host = "localhost"
    port = 8080
    max_client_count = 3

    # ソケット準備
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))

    # サーバ待機開始
    server_socket.listen()
    print(f"Chat server started at {host}:{port}")

    # サーバメインループ
    select_timeout = 60
    clients: List[socket.socket] = []
    while True:
        try:
            # ソケットがreadableになるまで待つ
            readable_sockets, _, _ = select.select([*clients, server_socket], [], [], select_timeout)
            if len(readable_sockets) == 0:
                # selectがタイムアウトした
                continue

            # サーバソケットがreadableになったことは、新しい接続要求が来たことを意味する
            if server_socket in readable_sockets:
                # readableソケットリストからサーバソケットを削除する
                # (こうしておかないと以降の操作が面倒になる)
                readable_sockets.remove(server_socket)

                # 一旦受け入れる
                new_client, address = server_socket.accept()

                # これ以上接続を受け入れられなければ閉じる
                if len(clients) == max_client_count:
                    decline_message = """
                        Thank you for your connection request to our chat server!
                        But now we can't accept your request because there are many participants in chat room.
                        Please try again later.
                    """
                    new_client.send(textwrap.dedent(decline_message).encode('ascii'))
                    new_client.close()
                    continue
                
                # 接続者の情報を得る
                client_info = f"{address[0]}:{address[1]}"
                print(f"New connection: {client_info}")

                # 現在の参加者全員に通知
                broadcast(f"New visitor: {client_info} joined.\n".encode(), clients)

                # ウェルカムメッセージを送信し、参加者リストに追加
                new_client.send(f"Welcome to our chat server! Now we have {len(clients)} clients.\n".encode())
                clients.append(new_client)
            
            # 他のクライアントの要求を処理する
            for readable_socket in readable_sockets:
                client_address = readable_socket.getpeername()
                client_info = f"{client_address[0]}:{client_address[1]}"

                # データ受信
                data = readable_socket.recv(1024)

                # 長さ0 = 切断
                if len(data) == 0:
                    print(f"Client {client_info} has left.")
                    clients.remove(readable_socket)

                    # 参加者に通知
                    broadcast(f"Client {client_info} has left.\n".encode(), clients)
                    continue
                    
                # 改行や空白を取り除き、何も残らなければ送らない
                available_data = data.rstrip()
                if len(available_data) == 0:
                    continue
                
                # 参加者全員に受信データを送り返す
                timestamp = datetime.now().strftime("%H:%M:%S")
                message = f"{timestamp} [{client_info}]: {available_data.decode('ascii')}\n"
                print(f">> {message}", end="", flush=True)
                broadcast(message.encode(), clients)
                
        except KeyboardInterrupt:
            print("Termination request received.")

            # ルームの閉鎖を通知し、クライアントソケットを全て閉じる
            broadcast(b"Server termination request received. This chat room will be closed soon.\n", clients)
            for client in clients:
                client.close()
            break
    
    # 終了処理
    print("Terminating chat server...")
    server_socket.close()
    return 0

def broadcast(data:bytes, destination: List[socket.socket]):
    """複数のソケットにまとめて同じデータを送る

    Args:
        data (bytes): 送信データ
        destination (List[socket.socket]): 送信先配列
    """
    if len(destination) == 0:
        return

    _, writable_sockets, _ = select.select([], destination, [])
    for client in writable_sockets:
        client.send(data)

if __name__ == "__main__":
    sys.exit(main())
