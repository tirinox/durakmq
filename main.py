from render import ConsoleRenderer
from net_game import DurakNetGame
from discovery_protocol import DiscoveryProtocol
from util import rand_id

PORT_NO = 37020
PORT_NO_AUX = 37021


def main():
    my_pid = rand_id()

    discovery = DiscoveryProtocol(my_pid, port_no=PORT_NO)
    print('Сканирую локальную сеть...')
    (remote_addr, _port), remote_pid = discovery.run()
    del discovery

    renderer = ConsoleRenderer()
    game = DurakNetGame(renderer, my_pid, remote_pid, remote_addr, [PORT_NO, PORT_NO_AUX])
    game.start()


if __name__ == '__main__':
    main()
