#
# プレーンなTCP/IPサーバ
#
# ソケットサーバとして最低限の機能を実装したもの。
# telnet localhost 8080 でアクセスできる
#

import socket
import sys
from datetime import datetime


def main() -> int:
    # socketオブジェクトの生成
    #
    # AF_INETは「IPv4専用のソケット」、SOCK_STREAMは「TCPによる通信」を表す。
    # ref:
    #   https://docs.oracle.com/cd/E19253-01/819-0392/sockets-4/index.html
    #   https://docs.oracle.com/cd/E19253-01/819-0392/sockets-18552/index.html
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # ソケットオプションの設定
    # 
    # 第一引数に設定したいオプションに対応するレベルを、第2,第3引数にオプション名と値を設定する。
    # レベルについてはrefを参照。
    # ここでは SO_REUSEADDR (使用していたアドレスを処理終了後即座に再利用可能にする) を設定している。
    # ref:
    #   https://manpages.debian.org/bookworm/manpages-ja-dev/setsockopt.2.ja.html
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ソケットとアドレスのバインド
    # 
    # socketオブジェクトを特定のアドレスにバインド(紐付け)する。
    host = "localhost"
    port = 8080
    server_sock.bind((host, port))
    print(f"Server socket is binded at {host}:{port}")

    # ソケットのリッスン
    # 
    # クライアントからの接続を受け入れる。第一引数はクライアントの同接数設定
    server_sock.listen(5)

    # ソケットサーバのメインループ
    while True:
        try:
            # 接続を待つ
            print("wait for new connection...")
            client_sock, address = server_sock.accept()
            print(f"new connection from {address}")

            # クライアントソケットにデータを送信する
            print("send message to client")
            message = f"Hello, World! now: {datetime.now().isoformat()}\n"
            client_sock.send(message.encode())
            
            # クライアントソケットを閉じる
            client_sock.close()
        except KeyboardInterrupt:
            # ^Cで終了
            break

    # サーバソケットを閉じる
    print("terminating server...")
    server_sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
