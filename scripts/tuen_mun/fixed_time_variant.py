"""Tuen Mun sensitivity: the same network with every signal fixed-time instead of vehicle-actuated.

    python scripts/tuen_mun/fixed_time_variant.py
    -> sim/tuen-mun/network-fixed-time.net.xml

TD publishes no signal timings, so the replay's signals are an assumption that could decide a diversion
result, as the unsourced Tong Bin signal did for Aberdeen. This variant takes green away from the
diversion route instead of handing it out on demand:

  Sham Tseng Interchange (NT405)  the same stages, fixed: A (Castle Peak Rd both ways) 35 s, B (the Tuen Mun
                                  Rd exit slip, which the diversion uses) 20 s, C 8 s, with the same amber,
                                  all-red and pedestrian time: an 84 s cycle, 24% of it for the exit slip,
                                  against up to 40 s on demand in the actuated network
  every other signal              netconvert's own phase durations, fixed

Promised to the team before any P1/P2 run (14 Oct, 18:33): a plan only counts if it wins with both.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC, OUT = ROOT / "sim/tuen-mun/network.net.xml", ROOT / "sim/tuen-mun/network-fixed-time.net.xml"
NT405 = "joinedS_1707529259_5106010530_cluster_1707529249_1707529253_1707529254_1707529258_#11more_cluster_1707529275_7061433809"
NT405_FIXED = [(35, "GGGGrrrGGGGG"), (3, "GGyyrrrGyyGG"), (2, "GGrrrrrGrrGG"), (20, "GGrrrGGGrrGG"), (3, "GGrrryyyrrGG"),
               (2, "GGrrrrrrrrGG"), (8, "GGGGGrrrrrGG"), (3, "GGGGyrrrrrGG"), (2, "GGrrrrrrrrGG"), (6, "rrrrrrrrrrrr")]


def main():
    text = SRC.read_text()
    block = re.compile(r'<tlLogic id="([^"]+)" type="actuated"(.*?)</tlLogic>', re.S)

    def fixed(m):
        tls, body = m.group(1), m.group(2)
        if tls == NT405:
            head = body.split(">", 1)[0]
            phases = "".join(f'\n        <phase duration="{d}" state="{s}"/>' for d, s in NT405_FIXED)
            return f'<tlLogic id="{tls}" type="static"{head}>{phases}\n    </tlLogic>'
        body = re.sub(r'\s(minDur|maxDur)="[^"]*"', "", body)
        body = re.sub(r'\s*<param key="[^"]*" value="[^"]*"/>', "", body)
        return f'<tlLogic id="{tls}" type="static"{body}</tlLogic>'
    out, n = block.subn(fixed, text)
    OUT.write_text(out)
    print(f"{n} signals fixed-time -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
