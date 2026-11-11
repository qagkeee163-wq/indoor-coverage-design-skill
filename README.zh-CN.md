# 室内信号覆盖方案设计 Skill

这是一个给 AI 助手（Claude、Codex 等）用的工作流 skill。给它一张厂房 / 楼层平面图，它会一步步做出完整的信号放大器室分方案：

区域划分 → 吸顶天线布置 → 主机 / IDF 位置 → 耦合器、功分器布线 → 每支天线的线损和输出功率 → 中英文两套图纸和材料清单。

## 包含什么

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 工作流本体：每一步做什么，每一步做完都停下来等你确认 |
| `references/design-rules.md` | 设计规则（中英对照），全部来自实际项目中的修改意见 |
| `config/equipment.yaml` | 设备参数：线损、主机功率档、耦合器 / 功分器损耗、天线功率范围、颜色、字体。换设备只改这里 |
| `scripts/coverage.py` | 计算和出图工具 |
| `examples/demo-factory/` | 虚构示例工厂，含全部输出 |
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

`check` 会自动检查：天线是否在 0–8 dBm、是否有重复 / 并行走线、耦合器是否和天线对齐、功分器是不是一边进另一边并排出、主机是否放在 IDF、主机功率是否在可用档位内。

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
2. 按步骤推进，每步出图给你确认。
3. 最后输出中英文两套结果。

安装方法见 [README.md](README.md#install)。上传到 GitHub 的方法见 [docs/github-upload.zh-CN.md](docs/github-upload.zh-CN.md)。

## 注意

- 客户图纸不要放进公开仓库。`.gitignore` 已经忽略 `projects/` 文件夹，实际项目请放在这个文件夹里。
- 计算结果是方案阶段的估算，没有计接头损耗和墙体衰减，以现场测试为准。
