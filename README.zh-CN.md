<!-- prettier-ignore -->
<p align="center">
  <img src="assets/cover.png" alt="hkfilings — 把港股年报 PDF 变成可追溯的结构化 JSON" width="720">
</p>

<h1 align="center">hkfilings · 港股年报 / 中期报告 Python SDK</h1>

<p align="center">
  <b>别再手工抄 300 页港股年报里的数字。<br>
  5 行 Python，每个数字都自带页码出处。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/hkfilings/"><img alt="PyPI" src="https://img.shields.io/pypi/v/hkfilings.svg"></a>
  <a href="https://pypi.org/project/hkfilings/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/hkfilings.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg"></a>
  <a href="https://github.com/mylovelycodes/hkfilings-python/actions"><img alt="CI" src="https://github.com/mylovelycodes/hkfilings-python/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pepy.tech/project/hkfilings"><img alt="Downloads" src="https://static.pepy.tech/badge/hkfilings/month"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>中文</b><br>
  <a href="#安装">安装</a> · <a href="#5-行跑通">5 行跑通</a> · <a href="#返回数据长这样">数据形态</a> · <a href="#实战案例">实战</a> · <a href="#api-一览">API</a> · <a href="#套餐和配额">套餐</a> · <a href="#faq">FAQ</a>
</p>

---

## 为什么做这个

如果你试过从 300 页 HKEX 年报 PDF 里抠分部收入、Capex 指引、毛利率构成，你
一定知道那些坑：数字找不到出处页码、OCR 错位、港币人民币混在一起、同比
数据对不上、分部加总不等于合并收入。

这个 SDK 是一个 API 客户端，让你拿到的每个数字都自带：

- **`source_page` + `source_text`** —— 精确指向 PDF 里的位置（如果解析器能
  定位 bbox，会落到 `extra` 字段里）
- **13 项确定性校验器** —— YoY 重算、会计恒等式、分部加总核对、币种 / 单位
  一致性、现金流符号检查、EPS 符号、自由现金流定义……
- **冻结的 v1 Schema + 前向兼容的 `extra` dict** —— 后端新增字段进 `extra`，
  你已经写好的代码永远不会因为后端升级而崩
- **Layer 2 行业信号** —— 11 类信号（毛利驱动、上游成本、下游需求、库存订单、
  Capex……），每条都绑定原文证据，过反幻觉规则
- **供应链图** —— 供应商、客户、竞争对手、监管者、替代品、合作伙伴 —— 含
  敞口占比和方向

### 跟现有方案对比

|                              | 数字带原文        | 自动校验          | 港股覆盖          | Schema 稳定            | 免费档          |
| ---------------------------- | :---------------: | :---------------: | :---------------: | :--------------------: | :-------------: |
| 手工分析师                   | 看人              | 手工              | 完整              | n/a                    | —               |
| Wind / 同花顺 / Choice       | ✗                 | 私有              | 完整              | 每次升级都变           | ✗               |
| 通用 LLM 直接读 PDF          | 易幻觉            | ✗                 | 任意              | 没有                   | API 费用        |
| **hkfilings**                | **页码 + 原文**   | **13 项校验**     | **完整 HKEX**     | **冻结 v1**            | **✓**           |

## 安装

```bash
pip install hkfilings
```

需要 Python ≥ 3.10，唯一运行时依赖是 `httpx`。Jupyter / Colab 直接好用。

## 5 行跑通

```python
from hkfilings import HKFilingsClient

client = HKFilingsClient(api_key="ak_...")

task   = client.analyze(ticker="9988", year=2026)   # 阿里 9988.HK
report = client.wait(task.task_id, timeout=600)

for fact in report.facts:
    print(f"{fact.metric_key:32}  {fact.value:>18,.0f}  p.{fact.source_page}")
```

<!--
  TODO（维护者）：用 vhs (https://github.com/charmbracelet/vhs) 录一段
  8 秒的 quickstart 演示，存为 assets/demo.gif，然后把下面的注释打开：

  <p align="center">
    <img src="assets/demo.gif" alt="hkfilings 快速开始演示" width="720">
  </p>
-->

> **免费档**：每月 20 次任务，无需信用卡。
> → **[领免费 Key](https://hkfilings.app/signup)**

## 返回数据长这样

每条 fact 都带出处：

```python
fact.metric_key       # "revenue"
fact.metric_label     # "营业收入"
fact.value            # 245_864_000_000.0
fact.comparable_value # 224_500_000_000.0    （上期）
fact.yoy_change       # 0.0952
fact.source_page      # 87
fact.source_text      # "本年度收入增长至人民币 245,864 百万元……"
fact.confidence       # 0.98
fact.extra            # 前向兼容字段（例如 bbox、unit）落在这里
```

Layer-2 信号自带方向 + 证据：

```python
signal.signal_type     # "margin_driver"
signal.direction       # "up" | "down" | "flat"
signal.summary         # "云业务毛利率提升源于 GPU 采购成本下降……"
signal.evidence        # [{"page": 42, "text": "……"}, ...]
signal.review_status   # "approved" | "auto_passed" | "pending"
```

供应链节点自带角色 + 敞口占比:

```python
node.node_label             # "台积电"
node.node_role              # "supplier" | "customer" | "competitor" | "regulator" | "substitute" | "partner"
node.exposure_share         # 0.18    （18% 的收入或成本依赖该节点）
node.direction_to_company   # "inflow" | "outflow"
node.evidence_page          # 142
```

## 实战案例

> 小贴士：下面每段代码都可以直接复制到 Jupyter notebook 里跑 —— 只要事先在
> shell 里 `export HKFILINGS_API_KEY=ak_...`。

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
    print(f"[{(s.direction or '-'):>4}] {s.summary}")
    for ev in s.evidence:
        text = (ev.get("text") or "")[:80]
        print(f"        p.{ev.get('page')} — {text}")

# [  up] 云智能毛利率 YoY 提升 4.2pp，源于 GPU 采购成本下降……
#         p.42 — 本年度云智能集团分部收入达到人民币……
```

### 画供应链图

```python
import networkx as nx

graph = nx.DiGraph()
sc = client.company_supply_chain("9988")
for node in sc.nodes:
    graph.add_edge(
        "9988",
        node.node_label,
        role=node.node_role,
        exposure=node.exposure_share,
    )
print(graph)   # → "DiGraph with N nodes and M edges"  (networkx ≥ 3.0)
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

SDK 本身 MIT 免费。后端按用量计费，含免费档：

| 套餐       | 月任务数  | Layer 2 访问           | 导出                    |
| ---------- | --------- | ---------------------- | ----------------------- |
| 免费       | 20        | 受限                   | JSON / CSV（带水印）    |
| Pro        | 200       | 完整                   | JSON / CSV              |
| Team       | 1,000     | 完整 + 多席位          | JSON / CSV / MD         |
| Enterprise | 自定义    | 完整 + Webhook + SLA   | 自定义                  |

→ **[到 hkfilings.app 查看实时价格 / 升级](https://hkfilings.app/pricing)**

也支持私有部署：构造客户端时传 `base_url="https://your-host"`。
企业部署联系 sales@hkfilings.app。

## Schema 契约

v1 公开 Schema 已冻结。JSON Schema 文档：

- https://hkfilings.app/v1/schema/financial_fact
- https://hkfilings.app/v1/schema/industry_signal
- https://hkfilings.app/v1/schema/supply_chain_node
- https://hkfilings.app/v1/schema/catalyst

后端新增字段进 `extra` dict —— 你不需要升 SDK 也能拿到。我们承诺 v1 内不
删除、不重命名任何已发布字段。

## 配置

| 配置项          | 构造参数        | 环境变量              |
| --------------- | --------------- | --------------------- |
| API 地址        | `base_url=`     | `HKFILINGS_BASE_URL`  |
| API Key         | `api_key=`      | `HKFILINGS_API_KEY`   |
| 请求超时（秒）  | `timeout=60.0`  | —                     |
| User-Agent      | `user_agent=`   | —                     |

客户端透传 `HTTPS_PROXY` / `HTTP_PROXY`，企业内网友好。

## Roadmap

- **v0.2** —— 异步客户端（`HKFilingsAsyncClient`）、指数退避自动重试、
  `client.facts_to_dataframe()` 便利方法
- **v0.3** —— 任务事件流（SSE 包装）、Webhook 签名校验、CLI
  （`hkfilings analyze 9988 2026`）
- **v1.0** —— 公开 API 稳定化、Deprecation 全部清理、TypeScript SDK 上线

提 issue 告诉我们优先做什么。

## FAQ

**问：能私有部署解析引擎吗？**
答：Enterprise 客户可以，联系 sales@hkfilings.app。需要自带 LLM Key
（DeepSeek / OpenAI / Anthropic）和一个 Postgres。

**问：跟 Wind / 同花顺 / Choice 有什么区别？**
答：我们只做港股，并把整条证据链（页码 + 原文）随数字一起返回。
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

## License

[MIT](LICENSE)。漏洞披露见 [SECURITY.md](SECURITY.md)，贡献指南见
[CONTRIBUTING.md](CONTRIBUTING.md)。

---

<p align="center">
  ⭐ <b>觉得有用请点个 Star</b> —— 这是对项目最便宜的支持方式。<br>
  领免费 Key → <a href="https://hkfilings.app/signup"><b>hkfilings.app/signup</b></a>
</p>
