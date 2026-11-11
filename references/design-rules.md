# Design rules / 设计规则

Every rule below came from a review comment by the engineer who owns this workflow. They are
requirements, not suggestions. 以下每条规则都来自实际项目里工程师提出的修改意见，必须遵守。

## 1. Antennas / 天线

- Commercial jobs with professional installers: **ceiling antennas only**.
  商业项目、专业工人安装：全部用吸顶天线。
- Rule of thumb: one ceiling antenna ≈ 300 m², R ≈ 10 m, 3–5 m through walls; panel antenna 15–20 m.
  经验值：吸顶天线约 300 m²、半径约 10 m，穿墙 3–5 m；板状天线 15–20 m。
- Keep the count reasonable. Too many antennas make the booster hard to install and raise the
  client's expectations. Example: an area first given 18 was reduced to 15; another from 15 to 12.
  天线数量要合理控制，太多会让主机难装，也会抬高客户的期望（例：18 → 15，15 → 12）。
- Large open areas: **edge coverage** is enough. Coverage circles should not spill far outside the
  exterior wall (waste).
  空旷区域边缘覆盖即可；覆盖圈不要明显超出外墙。
- Storage-like rooms get no own antennas; cover them from the neighbours' edge antennas.
  Electrical rooms need none. Low-demand parts (e.g. upper part of a hall) can be thinned.
  储藏间类的小区域不单独布天线，借助相邻区域的边缘天线；电力间不布；需求低的部分可减少。
- Adjacent small areas may be merged and re-laid out as one block (e.g. W4+W5+W6 → 8 antennas).
  相邻小区域可以合并成一大块重新排布。
- Spread antennas evenly; don't cluster them. Move an antenna slightly if that keeps cables apart.
  天线排布均匀，不要过密；必要时把天线挪一点，让走线分开。

## 2. Booster position / 主机位置

- Booster goes **in the IDF** (telecom room, red square on many drawings) when there is one.
  有 IDF（弱电间，图上常为红色方块）就放 IDF。
- Exception: no IDF nearby, or the run from the IDF is so long that an antenna falls below the
  minimum (0 dBm) → mount the booster **on a wall** near the load instead, and record why
  (`location_reason`). 例外：附近没有 IDF，或从 IDF 拉线太远导致天线 < 0 dBm，就改为靠墙放，并写明原因。
- Boosters are wall-mounted — never floating in the middle of a room. If one sits mid-room it must
  be because there is an IDF there. 主机靠墙；如果画在房间中间，必须是因为那里有 IDF。
- The **donor antenna does not decide the booster position**. Don't pull the booster toward the
  donor at the cost of longer distribution cable; donor cable can be longer.
  施主天线位置不决定主机位置，不要为了靠近施主天线而多拉室内线。
- Several boosters may share a big area, but keep the number low; small neighbouring areas share a
  booster rather than getting their own (e.g. 3 antennas in M1 were fed from the E1/E2 booster).
  大区域可以多台主机，但数量要合理；小区域优先和相邻主机共用。
- Two small boosters near each other can be replaced by one bigger booster (two 17 dBm → one 27 dBm).
  相邻两台小功率主机可以换成一台大功率主机。

## 3. Booster power / 主机功率

- Allowed single-port powers (default): 27, 17, 15, 12 dBm. **23 dBm is not available.**
  可用：27、17、15、12 dBm 单口；23 dBm 不可用。
- "N×2" models (14×2, 12×2, 17×2) are **not dual-port**: they include a 2-way splitter, total
  about +3 dB (14×2 ≈ 17 dBm), and still have **one output port**. Not used by default.
  “×2” 型号不是双口：自带一个 2 功分器，整机约 +3 dB，仍只有一个输出口；默认不用。
- Every antenna output must be **0 to 8 dBm** (max checked after rounding to 0.1).
  每支天线口功率 0–8 dBm。
- Near antennas on a 27 dBm booster need ≈19 dB loss; if the nearest one is too hot, add cable
  (route the near row on the far side) or use a higher-value coupler — don't exceed 8 dBm.
  27 dBm 主机最近的天线需要约 19 dB 损耗；太强时可以绕远一点或用更大的耦合器。

## 4. Cabling, couplers and splitters / 布线与器件

- **One cable leaves each booster.** All branching is done by couplers / splitters, and their
  losses are always counted. 每台主机只引出一根线，之后用耦合器 / 功分器分路，器件损耗必须计入。
- A coupler / splitter is used **only where one cable becomes two**.
  只有从一根线变成两根线的地方才用功分器 / 耦合器。
- **Splitter**: branches of similar length to similar antennas; every port has the same loss
  (1:2 3.3 dB, 1:3 5.2 dB, 1:4 6.4 dB).
  功分器：分出去的几路距离相近时用，每路损耗一样。
- **Coupler**: when one branch is much longer. Near antenna on the coupled port (loss = 5/8/10 dB),
  far branch on the through port (loss 2.15/1.1/0.8 dB).
  耦合器：一路远一路近时用；近的接耦合端，远的接直通。
- Couplers and splitters are interchangeable tools — choose whichever gives sensible numbers and
  clean routing. 功分器和耦合器可以灵活互换，以数值和走线合理为准。
- Put the coupler / splitter **at the point where the cables actually diverge**. Never split early
  and then run two cables side by side in the same direction. 器件放在线真正分岔的地方，不要先分开再两根线并行。
- **No duplicated / back-tracking runs** (same stretch walked twice) — it adds loss. A booster in
  the middle of its antennas branches outward in all directions. Especially no overlapping cables
  around the booster. 不要重复布线 / 来回走线；主机在中间时往四周分线；主机周围尤其不能有重叠的线。
- A coupler that feeds an antenna is **aligned** with it (coupled port straight up/down/sideways to
  the antenna). 直接接天线的耦合器要和天线对齐。
- Keep separate cables visibly apart on the drawing; move an antenna a little if needed.
  不同的线在图上要分开，必要时挪一下天线。
- Cable loss: LMR400 18.6 dB/100 m. Length = right-angle routing + 5 m riser at the booster
  (adjust to ceiling height) + 1 m slack per antenna. 线长 = 直角走线 + 主机到吊顶 5 m + 每支天线 1 m。
- **After every change, recompute and show every antenna's output.** 每次改动后都要重新算并列出每支天线的输出功率。

## 5. Donor antenna / 施主天线

- On the roof at a building / room **corner**, on the exterior wall line.
  放在屋顶角落、墙体外沿。
- All donors face the base station (e.g. all north). 统一朝基站方向。
- Donor cable = right-angle distance booster → donor + riser + 3 m through the roof.

## 6. Drawing conventions / 画图规范

| Item | Symbol | Colour |
|---|---|---|
| Booster 主机 | box + label "Booster A 27dBm" | by power: 27 red, 17 gold, 15 teal, 12 gray |
| Donor antenna 施主天线 | triangle, "N↑", dashed line to booster | green |
| Ceiling antenna 吸顶天线 | dot + id | purple |
| LMR400 cable | line | orange |
| Coupler 耦合器 | thick bar on the **input** side + short stub toward the **coupled** port ("──┘"); never a box | 5 dB green, 8 dB blue, 10 dB black |
| Splitter 功分器 | rectangle; single input on one long side; outputs as **parallel short lines** on the opposite long side; never in/out through the short ends; horizontal when the antennas are left/right symmetric | 1:2 light blue, 1:3 yellow, 1:4 pink |

- Legend lists every device type with its **quantity**. 图例写出每种器件数量。
- Different-power boosters must look different. 不同功率主机用不同颜色。
- Client-facing drawings: **English only** ("Booster", "Donor antenna", "Indoor ceiling antenna",
  "coupler (coupled / through)", "splitter"). Internal version: Chinese.
  给客户的图全部英文；内部版中文。
- Per-area drawings show a table: antenna, cable length, cable loss, device loss, total loss,
  output, devices passed. The overview shows a booster summary instead.

## 7. Process / 流程

- Follow the steps in order and get the user's confirmation after each one; do one area at a time.
  按步骤一步步来，每步确认后再继续；一块区域一块区域做。
- Ask when unsure — do not guess site facts (IDF, ceiling height, RSRP, models).
  不清楚的先问，不要猜现场信息。
- Use the client's measured reality over brochure coverage numbers. 以实际覆盖效果为准，官网面积只是理论值。
