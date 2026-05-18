<!-- prettier-ignore -->
<p align="center">
  <img src="assets/cover.png" alt="hkfilings — 把港股年报 PDF 变成可追溯的结构化 JSON" width="720">
</p>

<h1 align="center">hkfilings</h1>

<p align="center">
  <b>5 行 Python 代码，把港股年报/中期报告 PDF 变成<br>
  可追溯到页码的财务事实、行业信号和供应链图。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/hkfilings/"><img alt="PyPI" src="https://img.shields.io/pypi/v/hkfilings.svg"></a>
  <a href="https://pypi.org/project/hkfilings/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/hkfilings.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg"></a>
  <a href="https://github.com/mylovelycodes/hkfilings-python/actions"><img alt="CI" src="https://github.com/mylovelycodes/hkfilings-python/actions/workflows/ci.yml/badge.svg"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>中文</b>
</p>

---

## 为什么做这个

如果你试过从 300 页 HKEX 年报 PDF 里抠分部收入、Capex 指引、毛利率构成，你
一定知道那些坑：数字找不到出处页码、OCR 错位、港币人民币混在一起、同比
数据对不上、分部加总不等于合并收入。

这个 SDK 是一个 API 客户端，让你拿到的每个数字都自带：

- **`source_page` + `bbox`** —— 在 PDF 里精确定位
- **13 项确定性校验器** —— YoY 重算、会计恒等式、分部加总核对、币种 / 单位
  一致性、现金流符号检查、EPS 符号、自由现金流定义……
- **冻结的 v1 Schema** —— 后端新增字段进入 `extra` dict，你的代码永远不会
  因为后端升级而崩
- **Layer 2 行业信号** —— 11 类信号（毛利驱动、上游成本、下游需求、库存订单、
  Capex……），每条都绑定原文证据，过反幻觉规则
- **供应链图** —— 供应商、客户、竞争对手、监管者、替代品 —— 含敞口占比和
  方向

## 安装

```bash
pip install hkfilings
```

需要 Python ≥ 3.10，唯一依赖是 `httpx`。

## 5 行跑通

```python
from hkfilings import HKFilingsClient

# 免费档：每月 20 次任务，无需信用卡 → https://hkfilings.app/signup
client = HKFilingsClient(api_key="ak_...")

task   = client.analyze(ticker="9988", year=2026)   # 阿里 9988.HK
report = client.wait(task.task_id, timeout=600)

for fact in report.facts:
    print(f"{fact.metric_key:32}  {fact.value!s:>16}  p.{fact.source_page}")
```

> 免费档每月 20 次任务，无需信用卡。
> → **领免费 key：** https://hkfilings.app/signup

## 拿到的每条事实长这样

```python
fact.metric_key       # "revenue"
fact.value            # 245_864_000_000.0
fact.comparable_value # 224_500_000_000.0  （上期）
fact.yoy_change       # 0.0952
fact.source_page      # 87
fact.source_text      # "本年度收入增长至人民币 245,864 百万元……"
fact.confidence       # 0.98
fact.extra            # 后端新增字段都进这里
```

## 实战案例

### 对比阿里、腾讯过去 3 年的毛利率

```python
from hkfilings import HKFilingsClient
import pandas as pd

client = HKFilingsClient(api_key="ak_...")
rows = []
for tk in ("9988", "0700"):
    m = client.company_matrix(tk, metrics=["revenue", "gross_profit"])
    rows.extend({"ticker": tk, **cell} for cell in m.cells)

df = pd.DataFrame(rows).pivot_table(
    index="period", columns=["ticker", "metric_key"], values="value"
)
print(df)
```

### 读取行业信号 + 原文证据

```python
sigs = client.task_signals(task.task_id, signal_type="margin_driver")
for s in sigs.signals:
    print(f"[{s.direction:>8}] {s.summary}")
    for ev in s.evidence:
        print(f"            p.{ev.get('page')} — {ev.get('text')[:80]}")
```

### 画供应链图

```python
import networkx as nx

graph = nx.DiGraph()
sc = client.company_supply_chain("9988")
for node in sc.nodes:
    graph.add_edge("9988", node.node_label,
                   role=node.node_role, exposure=node.exposure_share)
```

### 导出 CSV 给 Excel

```python
with open("baba_2026_facts.csv", "wb") as fh:
    fh.write(client.facts_csv(task.task_id))
```

更多可运行示例见 [`examples/`](examples/)。

## API 一览

| 方法 | 用途 |
| ---- | ---- |
| `analyze(ticker, year, …)` | 按代码 + 年度自动定位并解析年报 |
| `create_task(pdf_url, …)` | 按 URL 解析 PDF |
| `upload(file_path, …)` | 上传本地 PDF |
| `task_status(task_id)` | 查询任务进度 |
| `wait(task_id, timeout=600)` | 阻塞等待任务完成 |
| `result(task_id)` | 取 Layer 1 财务事实结果 |
| `facts_csv(task_id)` | 同上，CSV 字节 |
| `company_matrix(ticker, metrics=…)` | 跨期事实矩阵 |
| `task_signals(task_id, …)` | 单份报告的 Layer 2 信号 |
| `company_signals(ticker, …)` | 跨期信号流 |
| `task_supply_chain(task_id)` | 单份报告的供应链节点 |
| `company_supply_chain(ticker, …)` | 跨期供应链 |
| `task_catalysts(task_id)` | 1-4Q 催化剂预测 |
| `company_catalysts(ticker, …)` | 跨期催化剂 |
| `intelligence_brief(task_id)` | 高管简报（结构化嵌套） |
| `review_diff(task_id, …)` | 审核版本对比 |
| `patch_fact(fact_id, **fields)` | 事实级审核动作 |
| `patch_signal(signal_id, **fields)` | 信号级审核动作 |
| `fact_comment(fact_id, body, …)` | 事实评论 |
| `schema(name="financial_fact")` | 取 JSON Schema |

完整文档：https://docs.hkfilings.app/python

## 套餐和配额

SDK 免费 (MIT)。后端按用量计费：

| 套餐 | 月任务数 | Layer 2 | 导出 | 价格 |
| ---- | -------- | ------- | ---- | ---- |
| 免费 | 20 | 受限 | JSON / CSV（带水印） | ¥0 |
| Pro | 200 | 完整 | JSON / CSV | 见定价页 |
| Team | 1,000 | 完整 + 多席位 | JSON / CSV / MD | 见定价页 |
| Enterprise | 自定义 | 完整 + Webhook + SLA | 自定义 | 联系销售 |

→ 对比和升级：https://hkfilings.app/pricing

也支持私有部署：构造客户端时传 `base_url="https://your-host"`。
企业部署联系 sales@hkfilings.app。

## Schema 契约

v1 公开 Schema 已冻结。JSON Schema 文档：

- https://api.hkfilings.app/v1/schema/financial_fact
- https://api.hkfilings.app/v1/schema/industry_signal
- https://api.hkfilings.app/v1/schema/supply_chain_node
- https://api.hkfilings.app/v1/schema/catalyst

后端新增字段进 `extra` dict —— 你不需要升 SDK 也能拿到。我们承诺 v1 内不
删除、不重命名任何已发布字段。

## 配置

| 配置项 | 构造参数 | 环境变量 |
| ------ | -------- | -------- |
| API 地址 | `base_url=` | `HKFILINGS_BASE_URL` |
| API Key | `api_key=` | `HKFILINGS_API_KEY` |
| 请求超时（秒） | `timeout=60.0` | — |
| User-Agent | `user_agent=` | — |

客户端透传 `HTTPS_PROXY` / `HTTP_PROXY`，企业内网友好。

## Roadmap

- **v0.2** —— 异步客户端、自动重试、`facts_to_dataframe()` 便利方法
- **v0.3** —— 任务事件流（SSE 包装）、Webhook 签名校验、CLI 工具
- **v1.0** —— 公开 API 稳定化、Deprecation 全部清理、TypeScript SDK 上线

提 issue 告诉我们优先做什么。

## FAQ

**问：能私有部署解析引擎吗？**
答：Enterprise 客户可以，联系 sales@hkfilings.app。需要自带 LLM Key
（DeepSeek / OpenAI / Anthropic）和一个 Postgres。

**问：跟 Wind / 同花顺 / Choice 有什么区别？**
答：我们只做港股，并把整条证据链（页码 + 原文 + bbox）随数字一起返回。
Schema 公开冻结，他们的私有且会变。定价对个人和小型基金友好。

**问：A 股和美股什么时候支持？**
答：暂时还没有。等港股覆盖足够稳健后会考虑。

**问：解析逻辑开源吗？**
答：SDK 本身 MIT 开源。解析引擎（LLM prompts、校验器、反幻觉规则）闭源。
JSON Schema 契约公开发布，作为稳定性承诺。

**问：怎么提某份报告的解析 bug？**
答：开 GitHub issue 带上 `task_id`，我们会在 SaaS 后端定位修复。

**问：被限流了怎么办？**
答：免费档每月 20 次。升级或等下个月重置。`HKFilingsError` 会带
`status_code=429` 和 `payload["upgrade_url"]`。

## 致谢

基于 [`httpx`](https://www.python-httpx.org/) 构建。客户端 API 设计借鉴
`openai-python` 和 `anthropic-python` SDK。

## License

[MIT](LICENSE)。漏洞披露见 [SECURITY.md](SECURITY.md)，贡献指南见
[CONTRIBUTING.md](CONTRIBUTING.md)。

---

<p align="center">
  为港股研究而做。领免费 key →
  <a href="https://hkfilings.app/signup"><b>hkfilings.app/signup</b></a>
</p>
