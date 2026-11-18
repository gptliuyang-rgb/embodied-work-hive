# Embodied Work Hive

个人具身智能技术雷达与工作复盘工作流。第一版先运行**公开技术雷达**；私人复盘和 Notion 集成见[路线图](docs/ROADMAP.md)。

## 每天会发生什么

北京时间 **21:17**，GitHub Actions 读取官方入口和 arXiv 论文元数据，按首次发现的 URL 去重，生成[最新简报](reports/latest.md)与日期归档，提交回当前仓库。GitHub 定时任务可能延迟；公共仓库长期无活动也可能暂停定时任务，可手动补跑。

1. **收集**：Generalist AI、Sunday Robotics、Physical Intelligence、Dyna Robotics、Anthropic Research/Engineering、OpenAI RSS、arXiv Robotics Agents。
2. **筛选**：OpenAI / Anthropic 按 robot、embodied、agent、planning 等词筛选标题。通用 agent 能力属于机器人间接相关信息。
3. **去重**：记录首次发现日期；有发布日期的订阅只取近14天。官网索引无结构化日期时标注待核实，首次运行建立历史基线，不能把旧文视为今天发布。
4. **解读与复核（可选）**：有模型密钥时最多两次调用，生成中文线索解读与待读问题，只引用已采集来源。复核不代表事实验证。
5. **沉淀**：保存 Markdown 日报和公开来源索引。

当前是多角色流水线。只读取网页索引与论文元数据，尚未读取全文，不自动判断性能或可复现性。社交媒体、视频、登录内容和已知 URL 的正文修改尚不覆盖。单个来源失败列在报告中；全部失败则运行失败，不推进去重记录。

## 使用

代码进入默认分支后自动运行一次。在 **Actions → Daily embodied radar** 查看结果，或点击 **Run workflow** 手动运行。没有模型密钥时仍会生成来源简报。

本地运行（Python 3.11+，无需第三方库；Windows 若缺少时区数据，可安装 `tzdata`）：

```sh
python -m unittest discover -s tests -v
python hive.py
```

`config.json` 配置信息源、关键词、论文窗口、每日数量和模型。每来源的新条目轮流选取，最多12条；全部首次发现内容保存在 `state/seen.json`，未展示条目不会自动在以后补发。请保留这个跨运行去重记录，删除会重新导入历史线索。同一天重跑保留当天发现。

## 模型方案

建议先用 **GPT-5.4 mini** 完成标题解读与复核，之后用真实样本评估是否升级。初期采用同一模型两次调用，降低配置复杂度；这不属于独立事实核验。

在 **Settings → Secrets and variables → Actions** 添加 Secret `OPENAI_API_KEY` 即可启用。通过 Variable `HIVE_MODEL` 指定账号可用的其他模型 ID。密钥不要放进代码、Issue 或聊天。调用发往 OpenAI 官方 Responses API，只包含本流程采集的公开标题与元数据。

无密钥：零模型调用。有密钥且有线索：每次运行最多两次调用，每次输出上限3,500 tokens（含可能的推理 token），付费调用不自动重试；手动重跑也会产生调用。上限不等于金额预算，请在模型服务账号设置预算提醒或限制。模型失败会降级成来源简报。

参考：[模型说明](https://developers.openai.com/api/docs/models/gpt-5.4-mini)、[API 入门](https://developers.openai.com/api/docs/quickstart)、[定时规则](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。价格与可用性以服务商实时说明为准。

## 公开与私人资料

此仓库、运行日志和报告公开。只接公开来源，不添加私人 Notion 数据、公司内部文档、私有项目活动或私人访问令牌。私人工作复盘将在本地或独立私有仓库运行，具体页面和仓库授权后接入。

## 维护

- `failed`：请求失败，可能是网络、限流或访问限制。
- `empty_parse`：未解析到条目，需检查网站结构，不能视为该公司没有进展。
- `ok` 且0条：读取成功，目前没有满足主题或时间条件的条目。
- 工作流需允许写入本仓库；组织策略若禁止，将无法保存报告。

当前未接入 Notion、私人 GitHub 活动、通知推送或硬件控制。先验证来源覆盖率与简报质量，再扩展。
