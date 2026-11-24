# 室内信号覆盖方案设计 Skill

这是一个给 AI 助手（Claude、Codex 等）用的工作流 skill。给它一张厂房 / 楼层平面图，它会一步步做出完整的信号放大器室分方案：

区域划分 → 吸顶天线布置 → 主机 / IDF 位置 → 耦合器、功分器布线 → 每支天线的线损和输出功率 → 中英文两套图纸和材料清单。

## 本次补充（2026-11-24）

本版在已修订的 Skill 上新增[五条补充规则](SKILL.md#补充规则2026-11-24)，保留原有适用规则：面积不清先询问；按面积和天线能力均匀布点；先定机位和配件/路由再选功率；按真实产品说明功率及所需频段；本用户欧洲用5D、美洲用LMR400，按实际规格分别核算。单支过强而需人为加线时，先取得用户确认。

[地区产品与线材约定](references/regional-equipment.md)补充已提供的欧版型号及功率口径。上述地区线材是本用户约定，不是行业统一标准。GitHub 本次同时同步本机此前已修订的多楼层、板状天线及严格功率检查内容。

## 代码更新（2026-11-24 之后）

计算工具已按补充规则改进：

- 线损按地区和频段核算（`config/regions/` 里有美洲 LMR400、欧洲 5D 两套配置）；缺规格值时停下询问。
- 支持多楼层：每层一张底图，过层垂直段计入线长，并在图上标注。
- 支持壁挂板状天线：朝向、前向距离 × 侧向宽度、背面接线检查。
- 核对主机型号和频段；整机总功率未确认逐频段输出时报错。
- 天线口功率按严格的 0 < P < 8 dBm 判断，接近上下限时提醒；人为加线必须标明已确认。
- 修复：多台主机一起优化时，失败一台不再丢掉其他主机的结果。
- 新增 `tests/run_tests.py` 回归测试和标准答案，网页版也要与它的结果一致。

## 包含什么

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 工作流本体，说明设计顺序和各阶段如何确认关键决策 |
| `references/design-rules.md` | 设计规则（中英对照），全部来自实际项目中的修改意见 |
| `config/equipment.yaml` | 默认参考参数（美洲） |
| `config/regions/` | 地区配置：`americas-lmr400.yaml`、`europe-5d.yaml`（含欧版型号表），项目复制一份再改 |
| `scripts/coverage.py` | 计算和出图工具 |
| `examples/demo-factory/` | 虚构示例工厂（单层、LMR400），含全部输出 |
| `examples/demo-hotel/` | 虚构示例酒店（两层、板状天线、5D），含全部输出 |
| `tests/` | 回归测试和标准答案 |
| `docs/github-upload.zh-CN.md` | 上传到 GitHub 的图文步骤 |

## 工具命令

```bash
pip install -r requirements.txt
python scripts/coverage.py areas    项目/design.json   # 第 0 步：区域划分图（米 + 英尺）
python scripts/coverage.py layout   项目/design.json   # 第 1 步：天线布置图 + 覆盖圈
python scripts/coverage.py optimize 项目/design.json   # 自动选耦合器 5/8/10 dB
python scripts/coverage.py check    项目/design.json   # 每支天线功率 + 设计规则检查
python scripts/coverage.py report   项目/design.json   # 出全部图纸、CSV、材料清单（zh/ 和 en/）
```

欧洲项目加 `--config 项目/europe-5d.yaml`。

`check` 会自动检查：每个频段的天线口功率是否严格在 0–8 dBm 之内、是否接近上下限、可行的主机输出区间、加线是否经确认、型号是否支持所需频段、是否有重复 / 并行走线、耦合器是否和天线对齐、功分器是不是一边进另一边并排出、板状天线是否背面接线、主机是否放在 IDF、天线楼层是否对得上。

## 输出

`output/zh/`（内部用）和 `output/en/`（给国外客户）各一套：

- 全厂总图
- 每个区域一张详图（含每支天线的线长、线损、器件损耗、输出功率、经过的器件）
- 区域划分图
- 天线输出功率汇总 CSV
- 材料清单 CSV：主机按功率、耦合器按 dB、功分器按分路数分别统计；线缆分室内、施主线、合计和采购量，单位 m 和 ft；另有 N 型接头数量
- 方案说明 md

## 怎么用

在 Claude 或 Codex 里说：“这是 XX 工厂的平面图，基站在北面约 1 km，红圈是重点区域，帮我做覆盖方案。”

AI 会：

1. 先问清缺的信息：比例尺、IDF 位置、吊顶高度等。
2. 按阶段推进，出图核对范围、点位和设备等关键决策。
3. 最后输出中英文两套结果。

安装方法见 [README.md](README.md#install)。上传到 GitHub 的方法见 [docs/github-upload.zh-CN.md](docs/github-upload.zh-CN.md)。

## 注意

- 客户图纸不要放进公开仓库。`.gitignore` 已经忽略 `projects/` 文件夹，实际项目请放在这个文件夹里。
- 计算结果是方案阶段的估算，没有计接头损耗和墙体衰减，以现场测试为准。
