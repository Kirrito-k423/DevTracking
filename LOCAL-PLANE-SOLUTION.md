# Plane 本地底座方案

## 当前状态

- 已安装 Plane Community Edition v1.3.1 的官方 Docker Compose 版本。
- 本地访问地址：<http://localhost:8090>
- 部署目录：`plane-selfhost/`
- 运行目录：`plane-selfhost/plane-app/`
- 外部端口：
  - HTTP: `8090 -> proxy:80`
  - HTTPS: `8443 -> proxy:443`
- 数据库、Redis、RabbitMQ、MinIO 只在 Docker 网络内暴露，没有直接映射到宿主机。

## 常用命令

```bash
cd /Users/Zhuanz/Documents/DevTracking/plane-selfhost

# 启动
./setup.sh start

# 停止
./setup.sh stop

# 重启
./setup.sh restart

# 查看日志，可加服务名：web/api/worker/proxy/postgres/redis/minio/rabbitmq
./setup.sh logs api

# 备份 Plane 容器数据
./setup.sh backup
```

## 为什么不从零做 Plane

Plane 已经覆盖了漂亮且成熟的项目管理底座：工作项、项目、周期、模块、页面、视图、Roadmap、成员协作和 API/Webhook。重新实现同等体验会把大量时间消耗在通用项目管理功能上，而不是你的核心差异。

更合适的路线是：

1. Plane 负责项目/任务/看板/成员协作。
2. 自研一个旁路扩展服务，负责需求导入、过滤、弹反、优先级、人力能力矩阵、日报周报、风险求助、项目复盘。
3. 通过 Plane API/Webhook 同步项目和任务，不直接改 Plane 数据库。
4. 关键业务数据单独存 PostgreSQL，并定时导出 Markdown/JSON 到 GitHub。

## 推荐扩展结构

```text
需求文档/客户反馈/人工录入
        |
        v
需求决策服务 Demand Hub
  - 需求导入与拆解
  - 分类、过滤、弹反
  - 价值/成本/风险/依赖评分
  - 人力能力矩阵与任务推荐
  - 日报、周报、风险求助、复盘报告
        |
        | Plane API / Webhook
        v
Plane
  - 项目
  - 工作项
  - 周期
  - 模块
  - 看板
```

## MVP 实施顺序

1. 先用 Plane 手工建 workspace、项目、成员、工作项，验证它能不能承接你的日常项目跟踪。
2. 做一个最小 Demand Hub：需求池、优先级评分、从需求一键创建 Plane 工作项。
3. 增加人员能力矩阵和负载模型，输出任务推荐理由。
4. 增加个人日报/阻塞/求助录入，自动生成日报和周报。
5. 增加项目复盘报告和 GitHub 备份。

## 注意事项

- 当前机器磁盘空间偏紧，Plane 镜像安装后剩余约 14GiB，可用于试用，但长期运行建议清理 Docker 或换到更大分区。
- `plane-selfhost/plane-app/plane.env` 包含 secret，已加入 `.gitignore`，不要提交到 GitHub。
- 这是本地 HTTP 测试部署，不是公网生产部署。公网部署需要域名、HTTPS、邮件服务、备份策略和更强的 secret 管理。

