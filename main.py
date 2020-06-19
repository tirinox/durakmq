from render import ConsoleRenderer
from net_game import DurakNetGame
from network import Networking
from discovery_protocol import DiscoveryProtocol
from local_game import help

PORT_NO = 37020


def main():
    my_id = DurakNetGame.rand_id()

    discovery = DiscoveryProtocol(my_id, port_no=PORT_NO)
    print('Scanning the network...')
    (addr, _port), remote_pid = discovery.run()
    del discovery

    endpoint = Networking(PORT_NO, broadcast=False)
    endpoint.bind(addr)

    renderer = ConsoleRenderer()
    game = DurakNetGame(renderer, endpoint, remote_pid)
    help()
    game.start()


if __name__ == '__main__':
    main()