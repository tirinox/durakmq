from serialization import DurakSerialized


def test_ser1():
    g = DurakSerialized()

    g.attack(g.players[0].cards[0])

    jg = g.serialized()
    g2 = DurakSerialized(jg)

    assert g.attacker_index == g2.attacker_index
    assert g.winner == g2.winner
    assert g.field == g2.field

    assert all(c1 == c2 for c1, c2 in zip(g.deck, g2.deck))

    for p1, p2 in zip(g.players, g2.players):
        assert p1.index == p2.index
        assert p1.cards == p2.cards
