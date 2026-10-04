# SailCloth-01 · 帆布浸渍防水台

帆布间布卷与浸渍固化台账基线项目（Django 5 + DRF + Vue 3 SPA）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Django 5 · DRF · SimpleJWT · django-cors-headers · Gunicorn |
| 前端 | Vue 3 · Vite · Pinia · Vue Router |
| 数据库 | PostgreSQL 15 |
| 部署 | Docker Compose · Nginx（前端反代 `/api`） |

## 路径与端口

- **项目路径**：`d:\work\document\bytecode\claudeCodePro\SailCloth\SailCloth-01`
- **前端**：http://localhost:3740
- **API**：http://localhost:8740
- **PostgreSQL**：localhost:6140

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 管理员 |
| `worker` | `123456` | 操作工 |

登录页已预填 `admin` / `123456`。后端 entrypoint 执行 migrate + seed。

## 业务规则

布卷状态不可设为「已固化」（`cured`），除非该卷**最近一条** `DipRun` 的 `cureHours` 已记录且 **≥ 12**。

浸渍备注字数受管理员在「备注字数」专页设定的 [最短, 最长] 区间约束（最短至少 1）：备注留空不校验；非空备注字数落在区间外则整笔拒绝（先校验后落库）。晾晒架面板登记与浸渍台账保存走同一套服务端校验，结论一致；改卷态、标已固化及备注以外字段不看字数。

规则实现：`backend/core/rules.py`（固化时长 + 备注字数）、`backend/core/models.py`（`NoteLengthRule` 单行配置）

## 快速启动

```bash
cd d:\work\document\bytecode\claudeCodePro\SailCloth\SailCloth-01
docker compose up --build
```

浏览器打开 http://localhost:3740

## SPA 信息架构

- **登录** → 进入主工作面
- **顶栏导航**：晾晒架 · 布卷台账 · 浸渍台账 · 备注字数
- **`/` 帆布间晾晒架（主）**：按帆布间挂布卷芯片（挂签状态 `raw` / `dipping` / `cured`）；点击打开右侧面板登记 `DipRun`、切换固化状态；架下为浸渍流水次要信息流
- **`/rolls` · `/dips`（次要台账）**：保留列表/表单 CRUD，非主路径
- **`/note-length` 备注字数（专页）**：管理员设定浸渍备注最短/最长汉字数；操作工只读查看

API 契约不变（JWT、`/api/lofts|rolls|dips|dashboard/`），新增 `/api/note-length-rule/`（GET 全员可读，PUT/PATCH 仅管理员）。

## 配色

海军蓝（navy）+ 帆布米色（canvas），与温室绿主题区分。
