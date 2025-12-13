from skyfield.api import load

def propagate(sats, debris):
    ts = load.timescale()
    t = ts.now()

    sat_pos = [s.at(t).position.km for s in sats]
    deb_pos = [d.at(t).position.km for d in debris]
    return sat_pos, deb_pos
