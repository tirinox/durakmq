from durak import Durak


def test_1():
    d = Durak()
    assert d.attacker_index == 0
    assert len(d.deck) == 36 - 2 * 6
    assert d.current_player.n_cards == d.opponent_player.n_cards == 6

    d.attack(d.current_player[0])
    d.finish_turn()

    assert d.attacker_index == 0
    assert d.opponent_player.n_cards == 7
    assert d.current_player.n_cards == 6
    assert len(d.deck) == 36 - 13