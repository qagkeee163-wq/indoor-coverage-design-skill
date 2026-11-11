# Demo Factory – Indoor Signal Coverage Design

## Boosters

| Booster | Location | Output | Antennas | Antenna output |
|---|---|---|---|---|
| Booster A | IDF (office, SW corner) | 27 dBm | 9 | 3.9 ~ 5.5 dBm |
| Booster B | IDF (office, SW corner) | 27 dBm | 6 | 4.7 ~ 5.5 dBm |

## Per-antenna output

| Antenna | Cable | Cable loss | Device loss | Total loss | Output | Path (devices passed) |
|---|---|---|---|---|---|---|
| O1 | 19 m | 3.5 dB | 18.0 dB | 21.5 dB | 5.5 dBm | 10 dB coupler (coupled) −10.0 → 8 dB coupler (coupled) −8.0 |
| O2 | 34 m | 6.2 dB | 16.1 dB | 22.3 dB | 4.7 dBm | 10 dB coupler (coupled) −10.0 → 8 dB coupler (through) −1.1 → 5 dB coupler (coupled) −5.0 |
| O3 | 49 m | 9.0 dB | 13.2 dB | 22.3 dB | 4.7 dBm | 10 dB coupler (coupled) −10.0 → 8 dB coupler (through) −1.1 → 5 dB coupler (through) −2.15 |
| P1 | 55 m | 10.2 dB | 12.1 dB | 22.3 dB | 4.7 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (coupled) −8.0 |
| P2 | 70 m | 12.9 dB | 10.2 dB | 23.1 dB | 3.9 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (coupled) −5.0 |
| P3 | 85 m | 15.7 dB | 7.3 dB | 23.1 dB | 3.9 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (through) −2.15 |
| P4 | 55 m | 10.2 dB | 12.1 dB | 22.3 dB | 4.7 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (coupled) −8.0 |
| P5 | 70 m | 12.9 dB | 10.2 dB | 23.1 dB | 3.9 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (coupled) −5.0 |
| P6 | 85 m | 15.7 dB | 7.3 dB | 23.1 dB | 3.9 dBm | 10 dB coupler (through) −0.8 → 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (through) −2.15 |
| W1 | 55 m | 10.2 dB | 11.3 dB | 21.5 dB | 5.5 dBm | 1:2 splitter −3.3 → 8 dB coupler (coupled) −8.0 |
| W2 | 70 m | 12.9 dB | 9.4 dB | 22.3 dB | 4.7 dBm | 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (coupled) −5.0 |
| W3 | 85 m | 15.7 dB | 6.6 dB | 22.3 dB | 4.7 dBm | 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (through) −2.15 |
| W4 | 55 m | 10.2 dB | 11.3 dB | 21.5 dB | 5.5 dBm | 1:2 splitter −3.3 → 8 dB coupler (coupled) −8.0 |
| W5 | 70 m | 12.9 dB | 9.4 dB | 22.3 dB | 4.7 dBm | 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (coupled) −5.0 |
| W6 | 85 m | 15.7 dB | 6.6 dB | 22.3 dB | 4.7 dBm | 1:2 splitter −3.3 → 8 dB coupler (through) −1.1 → 5 dB coupler (through) −2.15 |

## Bill of materials

- Booster 27 dBm: 2
- Indoor ceiling antenna: 15;  Donor antenna: 2
- Couplers: 5 dB × 5, 8 dB × 5, 10 dB × 1
- Splitters: 1:2 × 2, 1:3 × 0, 1:4 × 0
- LMR400: indoor 357 m + donor 23 m = 380 m (≈1,247 ft); order 440 m

## Drawings

- Overview.png
- Production_Office.png
- Warehouse.png
- Areas.png
