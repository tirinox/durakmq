from durak import Durak, ACE


def test_1():
    d = Durak()
    assert d.attacker_index == 0
    assert len(d.deck) == 36 - 2 * 6
    assert d.attacking_player.n_cards == d.defending_player.n_cards == 6

    d.attack(d.attacking_player[0])
    d.finish_turn()

    assert d.attacker_index == 0
    assert d.defending_player.n_cards == 7
    assert d.attacking_player.n_cards == 6
    assert len(d.deck) == 36 - 13


def test_trump_not_ace():
    for _ in range(10000):
        d = Durak()
        assert d.trump[0] != ACE
        assert d.trump == d.deck[-1]