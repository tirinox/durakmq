from serialization import DurakSerialized
from render import ConsoleRenderer
from net_game import DurakNetGame
from network import BroadcastNetworking
from local_game import help


def main():
    help()
    d = DurakNetGame(ConsoleRenderer(), BroadcastNetworking())
    d.start()


if __name__ == '__main__':
    main()