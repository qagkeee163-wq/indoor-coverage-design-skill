# Design rules / 设计规则

These are reviewed defaults. Apply the confirmed scope and equipment for each project.
以下为经确认的通用做法，具体项目以用户确认的范围、参数和设备为准。

## 0. 补充规则（2026-11-24） / Supplemental rules

本节及本页相应的面积、机位/路由、地区选型和线材说明属于本次补充；完整五条见 [SKILL.md](../SKILL.md#补充规则2026-11-24)。原有其他适用规则保留。

- 面积和重点覆盖区先于布点。必须读懂各层/各区需要覆盖的面积及与天线、机位和布线有关的信息。面积可从有尺度的图纸合理推算并注明依据；资料仍不足时先问用户，在回复前只整理资料，不自行假设面积或用户数直接定天线。
- 覆盖范围明确后，结合天线覆盖能力和现场障碍布点，间距尽量相似，按行列或墙面整齐排布，不能为排版整齐牺牲必覆盖区域。
- 功率选型前先定机位，再以实际分岔布配件并减少走线。地区线材和产品参数见[地区产品与线材约定](regional-equipment.md)。本用户欧洲用5D，美洲用LMR400，二者线损不能混用。

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
- Compare one booster feeding the confirmed points before adding another. Recalculate all paths and confirm the available output and isolation when changing the number of boosters.
  优先比较一台主机带已确认点位。调整主机台数后，重算各路径并核对可用输出和隔离度。

## 3. Booster power / 主机功率

- Use the user's actual regional product table; the reference inventory is not a substitute.
  选型必须使用用户给过的地区型号与功率档；未知时先询问。27、17、15、12dBm仅是美洲参考配置，不能默认用于欧洲。欧洲或需求涉及指定频段时，推荐同时列功率与频段组合，并匹配实际SKU。整机总输出、每频段和每载波输出分别记录，不默认等额拆分总功率。
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
- A coupler that feeds an antenna is **aligned** with it (coupled port straight up/down/sideways to
  the antenna). 直接接天线的耦合器要和天线对齐。
- Keep separate cables visibly apart on the drawing. Try reordering splitter output lanes or simplifying bends to remove crossings. For a wall-mounted panel, connect the last short orthogonal segment from the rear of the panel relative to its aim. Verify access behind the mounting face.
  不同馈线在图上分开，优先通过调整功分器出线顺序或简化拐点消除交叉。板状天线以覆盖朝向为准，末端用短横线或竖线从背面接入，核对墙后进线条件。
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
- Client-facing drawings: **English only** ("Booster", "Donor antenna", "Indoor ceiling antenna",
  "coupler (coupled / through)", "splitter"). Internal version: Chinese.
  给客户的图全部英文，内部版中文。用户要求先审中文版时，按已确认的走线、功率与用量生成英文图，两版使用同一版数据。
- Per-area drawings show a table: antenna, cable length, cable loss, device loss, total loss,
  output, devices passed. The overview shows a booster summary instead.

## 7. Process / 流程

- Follow the stage order in SKILL.md and use already confirmed constraints. Ask about missing site facts when they affect the current decision.
  按阶段推进，沿用已确认约束。缺少会改变当前判断的现场条件时，集中向用户确认。
- Use the client's measured reality over brochure coverage numbers. 以实际覆盖效果为准，官网面积只是理论值。
