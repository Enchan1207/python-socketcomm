#
# 継続的なデータ受信
#
# 接続先からデータを待ち受け、受信内容を表示するテスト
# telnet localhost 8080 でアクセスできる
#

import queue
import select
import socket
import sys
import threading


def main() -> int:
    # socketオブジェクトの構成
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # バインドして接続準備
    host = "localhost"
    port = 8080
    server_sock.bind((host, port))
    print(f"server socket bound to {host}:{port}")
    server_sock.listen(1)

    # 接続待機
    print("waiting for connection")
    client_sock, address = server_sock.accept()
    print(f"new connection from {address}")

    # ソケットオブジェクトとメッセージキューを渡してクライアントスレッド起動
    termination_event = threading.Event()
    message_queue: queue.Queue[str] = queue.Queue()
    client_thread = threading.Thread(target=client_worker, args=(client_sock, termination_event, message_queue))
    client_thread.start()

    # 受信ループ
    while True:
        try:
            message = message_queue.get().strip()
            print(f">> {message}")
        except KeyboardInterrupt:
            # ^Cで終了
            termination_event.set()
            print("termination request was sent to client thread")
            client_thread.join()
            break

    # サーバを終了
    print("terminating server...")
    server_sock.close()

    return 0

def client_worker(client_socket: socket.socket, termination_event: threading.Event, message_queue: queue.Queue[str]):
    """クライアントのワーカスレッド

    Args:
        client_socket (socket.socket): クライアントソケット
        termination_event (threading.Event): 終了通知イベント
        message_queue (queue.Queue[str]): メッセージキュー
    """
    capacity = 1024
    message_buffer = bytes(capacity)
    while not termination_event.is_set():
        # 受信可能状態になるまで待機
        rlist, _, _ = select.select([client_socket], [], [], 5)
        if len(rlist) == 0:
            continue
        
        # メッセージを受信 長さ0ならソケットが閉じたとみなし終了
        message_buffer = client_socket.recv(capacity)
        if len(message_buffer) == 0:
            print("client socket has been closed")
            break
        
        # 受信データをdecodeしてキューに積む
        try:
            message_queue.put(message_buffer.decode('ascii'))
        except UnicodeDecodeError:
            print("*** Error: non-ASCII characters received")
            continue
    
    print("terminating client socket...")
    client_socket.close()

        
if __name__ == "__main__":
    sys.exit(main())
