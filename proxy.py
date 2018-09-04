import logging
import select
import socket
import struct
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler

from ethdns import eth_resolve, MapResolver

dns_resolver = MapResolver()

logging.basicConfig(level=logging.DEBUG)
SOCKS_VERSION = 5


# class ThreadingTCPServer(ThreadingMixIn, TCPServer):
class ThreadingTCPServer(TCPServer):
    pass


class SocksProxy(StreamRequestHandler):
    username = 'username'
    password = 'password'

    def handle(self):
        logging.info('Accepting connection from %s:%s' % self.client_address)

        # greeting header
        # read and unpack 2 bytes from a client
        header = self.connection.recv(2)
        version, nmethods = struct.unpack("!BB", header)

        # socks 5
        assert version == SOCKS_VERSION
        assert nmethods > 0

        # get available methods
        methods = self.get_available_methods(nmethods)

        # accept only USERNAME/PASSWORD auth
        # if 2 not in set(methods):
        #     # close connection
        #     self.server.close_request(self.request)
        #     return

        # send welcome message
        self.connection.sendall(struct.pack("!BB", SOCKS_VERSION, 0))

        # request
        data = self.connection.recv(4)
        version, cmd, _, address_type = struct.unpack("!BBBB", data)
        assert version == SOCKS_VERSION

        use_ipv6 = False
        if address_type == 1:  # IPv4
            address = socket.inet_ntoa(self.connection.recv(4))
        elif address_type == 3:  # Domain name
            domain_length = self.connection.recv(1)
            domain = self.connection.recv(ord(domain_length)).decode('ascii')
            address = eth_resolve(domain.split('.'))
            if address:
                use_ipv6 = True
            else:
                address = domain
        elif address_type == 4: # IPv6
            address = self.connection.recv(16)
            use_ipv6 = True

        port = struct.unpack('!H', self.connection.recv(2))[0]

        is_dns_request = False
        # reply
        try:
            if cmd == 1:  # CONNECT
                remote = socket.socket(socket.AF_INET6 if use_ipv6 else socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((address, port))
                bind_address = remote.getsockname()
                if port == 53: #DNS
                    is_dns_request = True
                    logging.info('DNS caught, using local resolver')
                else:
                    logging.info('Connected to %s %s' % (address, port))
            else:
                self.server.close_request(self.request)

            port = bind_address[1]
            if use_ipv6:
                addr = struct.unpack("!IIII", socket.inet_pton(socket.AF_INET6, bind_address[0]))
                address_type = 4
                pack_struct = '!BBBBIIIIH'
                reply = struct.pack(pack_struct, SOCKS_VERSION, 0, 0, address_type,
                                    *addr, port)
            else:
                addr = struct.unpack("!I", socket.inet_pton(socket.AF_INET, bind_address[0]))[0]
                address_type = 1
                pack_struct = "!BBBBIH"
                reply = struct.pack(pack_struct, SOCKS_VERSION, 0, 0, address_type,
                                    addr, port)

        except Exception as err:
            logging.error(err)
            # return connection refused error
            reply = self.generate_failed_reply(address_type, 5)

        self.connection.sendall(reply)

        # establish data exchange
        if is_dns_request:
            self.mock_dns(self.connection)
        if reply[1] == 0 and cmd == 1:
            self.exchange_loop(self.connection, remote)

        self.server.close_request(self.request)

    def get_available_methods(self, n):
        methods = []
        for i in range(n):
            methods.append(ord(self.connection.recv(1)))
        return methods

    def verify_credentials(self):
        version = ord(self.connection.recv(1))
        assert version == 1

        username_len = ord(self.connection.recv(1))
        username = self.connection.recv(username_len).decode('utf-8')

        password_len = ord(self.connection.recv(1))
        password = self.connection.recv(password_len).decode('utf-8')

        response = struct.pack("!BB", version, 0)
        self.connection.sendall(response)
        return True

    def generate_failed_reply(self, address_type, error_number):
        return struct.pack("!BBBBIH", SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def mock_dns(self, client):
        data = b''
        while True:
            try:
                data += client.recv(4096)
            except Exception as e:
                break
        client.send(mock_resolver.get_response(data))

    def exchange_loop(self, client, remote):

        while True:

            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break


if __name__ == '__main__':
    with ThreadingTCPServer(('127.0.0.1', 9012), SocksProxy) as server:
        server.serve_forever()
