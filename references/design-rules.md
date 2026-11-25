# Design rules / 设计规则

These are reviewed defaults. Apply the confirmed scope and equipment for each project.
以下为经确认的通用做法，具体项目以用户确认的范围、参数和设备为准。

## 0. 补充规则（2026-11-24） / Supplemental rules

本节及本页相应的面积、机位/路由、地区选型和线材说明属于本次补充；完整五条见 [SKILL.md](../SKILL.md#补充规则2026-11-24)。原有其他适用规则保留。

- 面积和重点覆盖区先于布点。必须读懂各层/各区需要覆盖的面积及与天线、机位和布线有关的信息。面积可从有尺度的图纸合理推算并注明依据；资料仍不足时先问用户，在回复前只整理资料，不自行假设面积或用户数直接定天线。
- 覆盖范围明确后，结合天线覆盖能力和现场障碍布点，间距尽量相似，按行列或墙面整齐排布，不能为排版整齐牺牲必覆盖区域。
- 功率选型前先定机位，再以实际分岔布配件并减少走线。地区线材和产品参数见[地区产品与线材约定](regional-equipment.md)。本用户欧洲用5D，美洲用LMR400，二者线损不能混用。

## 0b. 补充规则（2026-11-25） / Lessons from the France residential project

本页标有“(2026-11-25)”的条目来自法国住宅楼项目复盘，已由用户确认为通用做法；汇总见 [SKILL.md](../SKILL.md#补充规则2026-11-25法国住宅项目复盘)，实例见 [reviewed-case-nimes.md](reviewed-case-nimes.md)。

## 1. Antennas / 天线

- Start with ceiling antennas for commercial jobs with professional installers. Use wall-mounted panels when the project calls for them.
  商业项目由专业人员安装时，通常先考虑吸顶天线。项目明确采用板状天线时，按板状天线的方向和挂墙条件布点。
- Rule of thumb: one ceiling antenna ≈ 300 m², R ≈ 10 m, 3–5 m through walls; panel antenna 15–20 m.
  经验值：吸顶天线约 300 m²、半径约 10 m，穿墙 3–5 m；板状天线 15–20 m。
- Size the layout from distances measured on the calibrated plan. Compare the union of ceiling-antenna circles with priority areas. Two representative points more than 20 m apart cannot fit within one 10 m radius circle.
  按校准后的图纸量距确定天线数量。吸顶天线核对覆盖圆并集和重点区。相距超过 20 m 的两个代表点无法同时落入一个半径 10 m 的圆。
- For a panel antenna, mark the wall face and bearing. Measure the forward distance and sideways offset from the axis at representative points in occupied areas, far ends and side edges. Treat a stated lateral width of about 10 m as total width, about 5 m each side for an initial check. Use project-specific antenna data where supplied.
  板状天线标明挂墙面和朝向，量取主要使用区、远端和侧缘代表点的前向距离与离轴距离。用户说横向约 10 米时，按总宽理解，初筛可按主轴左右各约 5 米。项目有明确的天线参数时，采用项目数据。
- Use the same coverage requirements to compare the current layout with candidate moves, changes in aim, consolidation, removal or additions. Remove a point if the measured geometry supports coverage of the required areas with the remaining antennas. Consider adding a point if a required area still has a material gap.
  按同一套覆盖要求对比现有布点和移位、转向、合并、撤点或加点后的方案。根据量距结果决定增减。剩余天线可以覆盖必覆盖区时可减点，必覆盖区仍有明显缺口时考虑加点。
- Give open and lower-priority areas edge coverage where the confirmed scope permits it. Favor layouts with more of each coverage circle inside the required footprint.
  已确认可接受边缘信号的空旷区或低优先区可从相邻点位借覆盖。尽量让理论圆落在目标范围内。
- Storage-like rooms get no own antennas; cover them from the neighbours' edge antennas.
  Electrical rooms need none. Low-demand parts (e.g. upper part of a hall) can be thinned.
  储藏间类的小区域不单独布天线，借助相邻区域的边缘天线；电力间不布；需求低的部分可减少。
- Adjacent small areas may be merged and re-laid out as one block (e.g. W4+W5+W6 → 8 antennas).
  相邻小区域可以合并成一大块重新排布。
- Spread antennas evenly; don't cluster them. Move an antenna slightly if that keeps cables apart.
  天线排布均匀，不要过密；必要时把天线挪一点，让走线分开。
- (2026-11-25) **Isolation / self-oscillation.** Too little isolation between the donor antenna and the indoor antennas makes the booster self-oscillate. Keep indoor antennas — above all on the top floor — away from the donor and facing away from it.
  施主天线和室内天线隔离度不够会自激。室内天线（尤其顶层）远离施主天线，并背对它。
- (2026-11-25) **No overlapping coverage.** Indoor antenna coverage should preferably not overlap; slight overlap at the edges is fine. Overlap wastes antennas and adds to the self-oscillation risk. When a layout shows large overlap, remove or re-aim one antenna rather than keep both (e.g. a street-wall panel was removed in the France project). `check` warns about panel footprints and ceiling antennas that overlap heavily.
  室内天线覆盖尽量不重叠，边缘可以有一点点。重叠多就撤点或转向；`check` 会提示。隔离度和重叠这两点都会影响天线排布。
- (2026-11-25) **Panels go on walls.** A panel antenna is wall-mounted and covers into the room. Do not place it in the middle of a corridor — the useful coverage there is poor. Moving a corridor panel to the wall of the room it should cover is the usual fix.
  板状天线贴墙安装，朝室内覆盖，不放在走廊中间。

- In a geometry-only pass, compare open-area circles by plan distance. Use the wall rule when the requested assessment considers obstructions. Confirm whether the user wants interfloor spillover assessed for the current project, including the floors, areas and intended use. Once confirmed, align shared structural features and project antenna positions. Treat spillover around openings and nearby projections as supplementary.
  纯理论阶段按图上距离布点。范围需要考虑障碍物时再应用穿墙规则。上下层互补先跟用户确认是否采用、涉及的楼层及区域、信号用途。确认后再对齐共同结构点，核对投影和楼梯等开口附近的补充信号。

## 2. Booster position / 主机位置

- Prefer an accessible IDF or equipment cabinet with a workable cable path. If the user selects a different spot, check a wall-mounted or cabinet-mounted position there and record the reason in `location_reason`.
  优先用弱电间或机柜。用户已确认其他位置时，在该处核对靠墙、维护和穿线条件，并记录原因。
- Boosters are wall-mounted — never floating in the middle of a room. If one sits mid-room it must
  be because there is an IDF there. 主机靠墙；如果画在房间中间，必须是因为那里有 IDF。
- The **donor antenna does not decide the booster position**. Don't pull the booster toward the
  donor at the cost of longer distribution cable; donor cable can be longer.
  施主天线位置不决定主机位置，不要为了靠近施主天线而多拉室内线。
- Several boosters may share a big area, but keep the number low; small neighbouring areas share a
  booster rather than getting their own (e.g. 3 antennas in M1 were fed from the E1/E2 booster).
  大区域可以多台主机，但数量要合理；小区域优先和相邻主机共用。
- (2026-11-25) **Simple wiring first.** When several boosters are needed, give each booster a block of adjacent floors and keep the wiring the same on every floor (same device, same branch pattern). A scheme that saves a unit but needs complex cross-floor splitting is worse.
  简单接法优先：每台主机带相邻楼层，各层接法一致；不为省一台主机做复杂分配。
- (2026-11-25) Boosters that sit in different places are drawn separately, each with its own riser, so nobody reads them as installed together.
  实际位置不同的主机，图上分开画，各自有竖井。
- Compare one booster feeding the confirmed points before adding another. Recalculate all paths and confirm the available output and isolation when changing the number of boosters.
  优先比较一台主机带已确认点位。调整主机台数后，重算各路径并核对可用输出和隔离度。

## 3. Booster power / 主机功率

- Use the user's actual regional product table; the reference inventory is not a substitute.
  选型必须使用用户给过的地区型号与功率档；未知时先询问。27、17、15、12dBm仅是美洲参考配置，不能默认用于欧洲。欧洲或需求涉及指定频段时，推荐同时列功率与频段组合，并匹配实际SKU。整机总输出、每频段和每载波输出分别记录，不默认等额拆分总功率。
- (2026-11-25) **Match power to run length.** Give the stronger booster the group with the longer riser / runs. A strong booster on short runs pushes the near antennas above 8 dBm (in the France project a 23 dBm unit on the upper floors did exactly that, so both groups became 20 dBm units). `check` warns when the weaker booster has the longer runs.
  按线长分配功率：竖井长、线损大的组用大功率；短线组用大功率时近端天线容易超 8 dBm。
- (2026-11-25) **Antennas per unit.** User guide values: Hi20 about 6–7 antennas, Hi23 about 8–9; a Hi20 with 9 is not suitable. Stored as `antennas_typical: [usual, max]` in the model table; `check` warns above `usual` and errors above `max`.
  每台主机带天线数：Hi20 约 6–7 支，Hi23 约 8–9 支；Hi20 带 9 支不合适。
- (2026-11-25) **Bands from the customer's test report.** Read each operator's bands and signal levels from the customer's measurement report (outdoor / roof and indoor points) and use them to pick the model and band set. Ask about any band the report leaves unnamed.
  频段从客户的信号测试报告读：各运营商的频段和强度，作为选型依据；报告未标名称的频段先问。
- "N×2" models (14×2, 12×2, 17×2) are **not dual-port**: they include a 2-way splitter, total
  about +3 dB (14×2 ≈ 17 dBm), and still have **one output port**. Not used by default.
  “×2” 型号不是双口：自带一个 2 功分器，整机约 +3 dB，仍只有一个输出口；默认不用。
- Require **0 < P < 8 dBm** at each antenna by default, using unrounded values. Select the lowest available passing power or verify the specified one. If a branch is near either limit, give its estimated power, the relevant limit and one recalculated alternative for reference. If the antenna moves, explain the effect on the required coverage. If a branch fails, identify it and compare route or component choices.
  默认按未舍入值逐支检查 0 < P < 8 dBm。优先用最低合格档，或验算用户指定档。接近上限或下限时，提醒用户具体支路、估算功率和接近的限值，并给一个经复算的替代参考方案。替代方案涉及移点时，说明对原覆盖区域的影响。越界时指出具体支路，比较调整走线或器件的方案。
- For a long branch at fixed power, use the shortest feasible route to screen the proposed splitter scheme. Compare routing and unequal division if the estimate falls short. After a point is moved, recheck whether the simpler splitter scheme can meet all branch limits.
  指定主机功率且有长支路时，先用最短可行走线核对原功分方案。若电平不足，比较走线与耦合分配。移点后重新核对各路，能满足要求时可恢复较简单的功分方案。

## 4. Cabling, couplers and splitters / 布线与器件

- **One cable leaves each booster.** All branching is done by couplers / splitters, and their
  losses are always counted. 每台主机只引出一根线，之后用耦合器 / 功分器分路，器件损耗必须计入。
- Put a splitter or coupler at a branch point where one feeder serves multiple onward paths.
  一根馈线在实际分岔处接功分器或耦合器。
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
- (2026-11-25) **No back-and-forth wiring.** If a run can be made in one pass, never go past the point and come back. When the cable direction changes (e.g. a panel must now be fed from its other side), adjust the antenna or the splitter/coupler position so the cable arrives directly — usually move the device back to the real branch point, or slide the antenna toward the run. Check this in every design; `check` flags any cable that walks more than `layout_checks.max_detour_m` (default 1.5 m) beyond the direct right-angle route.
  不来回布线。走线方向改了就微调天线或功分器/耦合器位置，让线一次到位。每次设计都要查。
- A coupler that feeds an antenna is **aligned** with it (coupled port straight up/down/sideways to
  the antenna). 直接接天线的耦合器要和天线对齐。
- Keep separate cables visibly apart on the drawing. Try reordering splitter output lanes or simplifying bends to remove crossings. For a wall-mounted panel, connect the last short orthogonal segment from the rear of the panel relative to its aim. Verify access behind the mounting face. (2026-11-25) The cable enters the **back (wall side) on the long side** of the panel, never the short end and never the front; the side the cable comes from on the drawing tells the reader the panel faces the other way.
  不同馈线在图上分开，优先通过调整功分器出线顺序或简化拐点消除交叉。板状天线以覆盖朝向为准，末端用短横线或竖线从背面接入，核对墙后进线条件。（2026-11-25）线从板状天线背面（贴墙一侧）的长边接入，不接短边，也不接正面；图上线从哪侧进，就表示天线朝另一侧覆盖。
- Use the shortest feasible orthogonal route with the correct regional cable loss.
  允许时用简洁的横竖路线，现场核对桥架、竖井和穿越条件。布线/核算前按地区锁定欧洲5D、美洲LMR400及其实际逐频段损耗，不得自动更换低损耗线材。18.6dB/100m只可作美洲LMR400的1800MHz参考；不能用于5D，也不能作为所有频率的损耗。机位至吊顶、层高和安装余量按实际条件记录。
- Only after the booster is fixed and all other branches are suitable, propose added cable for one overpowered antenna; get user confirmation before changing it.
  只有已定主机下其余支路功率均合适、仅单支过强时，才可提出人为加长支线。先给出增加长度、损耗和该支输出变化，用户确认后实施。优化目标仍是少线、少损耗，不能默认用绕线消耗功率。
- For a branch budget, follow the complete path from booster to antenna. For material quantities, count each shared trunk, jumper and rise once. Show indoor and donor lengths separately, with net and +15% purchase lengths.
  逐路验算计全路径；汇总线缆用量时，共用干线、跳线和过层各算一次。室内线和施主线分列，净用量与加 15% 的采购量分列。
- Recompute every affected antenna's output after a physical or electrical change. Use the same branch lengths in the drawing, power table and takeoff. Update symbol-only edits using the approved geometry and lengths.
  点位、物理路径或电气参数改动后，重算受影响天线。图纸、功率表和材料统计使用同一版长度。仅调整图形或文字时沿用已确认的物理长度。

## 5. Donor antenna / 施主天线

- On the roof at a building / room **corner**, on the exterior wall line.
  放在屋顶角落、墙体外沿。
- All donors face the base station (e.g. all north). 统一朝基站方向。
- Estimate the donor cable along its own confirmed path, including horizontal runs, actual vertical rise and roof penetration. The default roof-through allowance is configurable and separate from inter-floor height.
  施主线按实际水平路线、垂直上升和屋面穿越单独算。默认穿屋面余量可配置，与楼层间距分开。

## 6. Drawing conventions / 画图规范

| Item | Symbol | Colour |
|---|---|---|
| Booster 主机 | full-sized rectangle, with power label on detailed plans | distinct from splitter colors |
| Donor antenna 施主天线 | solid triangle for the outdoor log-periodic antenna; direction may be labeled outside the shape on detailed plans | green |
| Ceiling antenna 吸顶天线 | large readable dot; ID on detailed plans | purple |
| Panel antenna 板状天线 | readable wall-aligned rectangle with rear feeder connection; keep aim in the design data and show arrows as agreed | consistent colour across panels |
| Feeder 馈线 | line, with the project cable name in the detailed legend | orange |
| Coupler 耦合器 | T-shaped symbol follows feeder orientation; IN and TH inline, CP at 90 degrees; never a box | 5 dB green, 8 dB blue, 10 dB black |
| Splitter 功分器 | thin rectangle; single input on one long side; outputs as **parallel short lines** on the opposite long side; never in/out through the short ends; horizontal when the antennas are left/right symmetric | 1:2 light blue, 1:3 yellow, 1:4 pink |

- On the sending floor, label the destination at the end of each inter-floor feeder, such as `Ground floor`. On the receiving floor, draw the route from the entry point to the first device and label where it comes from. Keep the vertical length in the calculation and show it on the plan only as agreed. Omit splitter IDs on request.
  发出楼层的跨层线末端标目标楼层，例如 `Ground floor`。接收楼层标来源，并画出从上楼接入点到第一个分配器件的线段。过层长度计入核算，图上是否标注按交付要求。用户要求时去掉功分器编号。
- On a standalone distribution schematic, use a different pale background for each floor. Draw the outdoor log-periodic antenna as a pure green triangle. Keep component symbols unlabeled when requested, with just floor names if needed.
  独立分布图每层用不同浅色底。绿色室外天线为实心三角，内部无横线或中轴。需要无器件标注时，只保留楼层名。
- Different-power boosters must look different. 不同功率主机用不同颜色。
- (2026-11-25) Plans: straight cable runs with few bends; do not draw corridors or room details just to route cables. Splitter: single input on one long side, two (or more) short parallel outputs on the opposite long side, each then turning. Colours tell device specs apart.
  平面图走线画直线、少折角，不画走廊。功分器一边进、对边并排短线出再转向；不同规格用颜色区分。
- Client-facing drawings: **English only** ("Booster", "Donor antenna", "Indoor ceiling antenna",
  "coupler (coupled / through)", "splitter"). Internal version: Chinese.
  给客户的图全部英文，内部版中文。用户要求先审中文版时，按已确认的走线、功率与用量生成英文图，两版使用同一版数据。
- Per-area drawings show a table: antenna, cable length, cable loss, device loss, total loss,
  output, devices passed. The overview shows a booster summary instead.

## 7. Process / 流程

- Follow the stage order in SKILL.md and use already confirmed constraints. Ask about missing site facts when they affect the current decision.
  按阶段推进，沿用已确认约束。缺少会改变当前判断的现场条件时，集中向用户确认。
- Use the client's measured reality over brochure coverage numbers. 以实际覆盖效果为准，官网面积只是理论值。

## 8. Delivery: design version vs customer version / 交付：设计版与客户版（2026-11-25）

- **Design version** (internal review): every annotation — booster/antenna labels, coverage footprints and aim arrows, cable lengths and cable type, per-antenna power table.
  设计版保留全部标注、覆盖范围、朝向箭头、线长和功率表，用于内部核对。
- **Customer version** removes: labels next to boosters and antennas; coverage footprints and aim arrows; cable lengths and the cable name ("5D") on the lines; the power table (the customer gets the BOM only). Device symbols, cables and a symbol legend stay.
  客户版去掉主机、天线旁的标注，覆盖范围和箭头，线上的长度和“5D”，不给功率表，只给材料清单。
- When the customer gave no floor plans, customer plans show a **plain building outline only** — no internal dashed lines, corridors or rooms, no external annotations. (`floors[].outline`.)
  客户没给平面图时，客户版平面图只画外框，内部不画虚线、走廊、房间，外部不加标注。
- When the customer supplied a system / synoptic drawing, draw the system view **on that drawing**; do not redraw the buildings.
  客户给了示意图，就在原图上画系统图，不重画楼栋。
- Fixed customer order: 01 system diagram → 02 connection diagram → 03 BOM → 04 plan overview → 05 per-floor plans (`report --client` writes 02–05 and an index; 01 is done on the customer's drawing).
  客户版顺序固定：系统图 → 连接图 → 材料清单 → 平面总览 → 各层平面图。
- **Always include a connection diagram**: the simplest, most intuitive picture of booster → devices → antennas. Floors as pale bands, one column and one riser per booster; customer version shows only floor names, booster titles and "Roof".
  每次都附连接图，要最简单直观：楼层色带，每台主机一列、一条竖井；客户版只写楼层名、主机名和屋顶。
