#
# 継続的なデータ送信
#
# sample.txt (Apache license 2.0) を連続で送信し続けるテスト
# telnet localhost 8080 でアクセスできる
#

import sys
import socket
import threading

def main() -> int:
    # socketオブジェクトの構成
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # バインドして接続準備
    host = "localhost"
    port = 8080
    server_sock.bind((host, port))
    print(f"Server socket is binded at {host}:{port}")
    server_sock.listen(5)

    # ソケットサーバのメインループ
    client_termination_event = threading.Event()
    while True:
        try:
            # 接続を待つ
            client_sock, address = server_sock.accept()
            print(f"new connection from {address}")

            # クライアントスレッドを起動
            # while内で起動したスレッドはこれ以降コード上から参照できない気がするが、果たしてそれでいいのか
            client_thread = threading.Thread(
                target=client_socket_worker, 
                args=(client_sock, client_termination_event))
            client_thread.start()
            print(f"client thread started (Thread {client_thread.ident})")
            
        except KeyboardInterrupt:
            # ^Cで終了
            print("send termination request to child threads...")
            client_termination_event.set()
            break

    # サーバソケットを閉じる
    print("terminating server...")
    server_sock.close()
    return 0

def client_socket_worker(client_socket: socket.socket, termination_event: threading.Event):
    """クライアントソケットのワーカスレッド

    Args:
        client_socket (socket.socket): クライアントソケット
        termination_event (threading.Event): 終了イベント
    """

    # サンプルテキストを読み込む
    # なお、子スレッドでファイルハンドルを握ったり新しくメモリを確保したりするのは
    # 個人的にどうかと思う
    with open("sample.txt") as f:
        lines = f.readlines()
    
    # イベントフラグがセットされるまでテキストファイルの内容を出力し続ける
    current_line = 0
    max_lines = len(lines)
    interval: float = 0.5
    while not termination_event.wait(interval):
        try:
            client_socket.send(lines[current_line].encode())
            current_line = (current_line + 1) % max_lines
        except BrokenPipeError as e:
            # ソケットが落ちるとここで例外を吐く
            print(f"client socket was broken: {e}")

            # クライアントソケットを閉じてスレッドを終了
            print("close client socket...")
            client_socket.close()
            break

if __name__ == "__main__":
    sys.exit(main())
