# 重构任务卡片

## 背景
目标是将当前项目重构为一个纯后台服务程序，保留以下核心能力：

- 订阅拉取与解析
- Clash 配置生成
- 本地订阅服务

约束如下：

- 所有新代码放在新的目录下
- 运行形态为后台服务
- 使用 `nuitka` 打包
- 支持 `macOS` 和 `Ubuntu`
- HTTP 接口只保留 `GET /clash.yaml`
- 增加统一日志模块
- `stdout` 使用 `colorlog`
- 日志需要支持写文件和轮转
- 文件日志不带颜色
- 不再保留 GUI

---

## 任务卡 1：搭建 `clash_sub_service/` 新工程骨架
### 目标
在新目录下建立后台服务项目基础结构，不迁移旧逻辑。

### 范围
- 新建 `clash_sub_service/`
- 新建 `src/` 源码结构
- 新建 `tests/`、`packaging/`、`spec/`
- 新建 `pyproject.toml`、`README.md`、`config.example.yaml`

### 不做
- 不迁移 `core.py` 逻辑
- 不实现 HTTP 服务
- 不实现日志细节

### 交付物
- 可导入的 Python 包
- 最小 CLI 入口

### 验收标准
- `python3 -m cli --help` 可执行
- 项目目录结构符合设计

---

## 任务卡 2：定义配置模型与退出码
### 目标
建立统一配置加载与校验入口。

### 范围
- 定义配置 schema
- 支持从 YAML 加载配置
- 定义退出码常量
- 新增 `spec/decisions.md`

### 配置项
- `subscription.url`
- `subscription.timeout`
- `server.listen`
- `server.port`
- `server.refresh_interval`
- `clash.port`
- `clash.allow_lan`
- `output.path`
- `logging.*`

### 交付物
- `config/loader.py`
- `config/schema.py`
- `exit_codes.py`
- `config.example.yaml`
- `spec/decisions.md`

### 验收标准
- 合法配置加载成功，退出码 `0`
- 非法配置返回退出码 `2`

---

## 任务卡 3：重构日志模块
### 目标
建立统一日志初始化能力。

### 范围
- `stdout` 使用 `colorlog`
- 文件日志使用 `RotatingFileHandler`
- URL query 敏感字段脱敏
- access log 开关
- 文件日志自动建目录
- 文件日志按大小轮转

### 不做
- 不做 JSON log
- 不做按天轮转
- 不做 Prometheus 集成

### 交付物
- `logging/setup.py`
- `logging/formatters.py`
- `logging/filters.py`

### 验收标准
- 终端输出彩色日志
- 日志文件可生成且无 ANSI 颜色码
- `token` 等字段被脱敏

---

## 任务卡 4：迁移订阅拉取逻辑
### 目标
把旧项目的拉取逻辑迁入新架构。

### 范围
- 从旧 `core.py` 拆出 `fetcher.py`
- 统一请求超时、UA、错误包装

### 交付物
- `core/fetcher.py`
- 对应单元测试

### 验收标准
- 能成功获取本地模拟订阅内容
- 网络异常时返回运行时错误

---

## 任务卡 5：迁移节点解析逻辑
### 目标
把 `ss` / `vmess` 解析逻辑迁入新架构。

### 范围
- 拆出 `parser.py`
- 定义 `Node` 数据模型
- 保持当前兼容行为

### 交付物
- `models/node.py`
- `core/parser.py`
- `tests/test_parser.py`

### 验收标准
- 可解析 base64 订阅正文
- 支持 `ss://` 和 `vmess://`
- 空结果时返回明确错误

---

## 任务卡 6：迁移 Clash 配置生成逻辑
### 目标
把 Clash YAML 生成逻辑迁入新架构。

### 范围
- 拆出 `clash_builder.py`
- 拆出 `generator.py`
- 支持 YAML dump

### 交付物
- `core/clash_builder.py`
- `core/generator.py`
- `tests/test_builder.py`

### 验收标准
- 输入节点列表后可生成 Clash 配置
- 输出 YAML 内容与预期一致

---

## 任务卡 7：实现本地 HTTP 服务
### 目标
提供仅 `/clash.yaml` 的本地订阅服务。

### 范围
- 实现 HTTP server
- 只保留 `GET /clash.yaml`
- 其他路径返回 `404`
- 未就绪返回 `503`

### 交付物
- `http/server.py`
- `tests/test_server.py`

### 验收标准
- `GET /clash.yaml` 返回 `200` 和 YAML
- 未生成时返回 `503`
- 非 `/clash.yaml` 返回 `404`

---

## 任务卡 8：实现后台刷新服务
### 目标
实现常驻刷新与状态管理。

### 范围
- 周期刷新订阅
- 在内存中保存最新 YAML、节点数、错误状态、更新时间
- 支持优雅停止

### 交付物
- `service/state.py`
- `service/refresher.py`
- `service/runner.py`

### 验收标准
- 服务启动后自动首次刷新
- 后续按 `refresh_interval` 周期刷新
- 停止时线程和 HTTP 服务能正常退出

---

## 任务卡 9：实现 CLI 运行模式
### 目标
提供后台服务的命令入口。

### 范围
- `serve`
- `once`
- `validate-config`

### 交付物
- `cli.py`
- `app.py`

### 验收标准
- `serve` 可启动后台服务
- `once` 可生成 YAML 到输出路径
- `validate-config` 只校验配置，不访问网络

---

## 任务卡 10：增加本地 smoke test
### 目标
提供最小可运行验收脚本，且不依赖外网。

### 范围
- 本地起一个模拟订阅源
- 启动后台服务
- 请求 `/clash.yaml`
- 检查日志文件

### 交付物
- `tests/test_smoke.sh`
- `tests/fixtures/subscription.txt`
- `tests/fixtures/expected.yaml`

### 验收标准
- 脚本本地可直接执行
- 失败时退出非 `0`
- 不依赖外网
- 日志文件中包含关键事件

---

## 任务卡 11：增加 Nuitka 打包脚本
### 目标
支持 `macOS` 和 `Ubuntu` 打包。

### 范围
- `build_macos.sh`
- `build_linux.sh`
- 统一公共构建参数
- 确保 `colorlog` 等依赖被正确带入

### 交付物
- `packaging/nuitka/common.sh`
- `packaging/nuitka/build_macos.sh`
- `packaging/nuitka/build_linux.sh`

### 验收标准
- 可生成目标平台可执行文件
- 打包产物能正常启动后台服务

---

## 任务卡 12：增加系统服务示例
### 目标
提供跨平台后台托管样例。

### 范围
- Ubuntu `systemd`
- macOS `launchd`

### 交付物
- `packaging/systemd/clash-sub-service.service`
- `packaging/launchd/com.lyratec.clash-sub-service.plist`

### 验收标准
- 样例配置可直接改路径后使用
- 与 stdout/file 日志策略兼容

---

## 任务卡 13：增加配置文件监控与自动重读
### 目标
为后台服务增加独立的配置文件监控能力，在配置文件发生变动时主动触发重新读取，而不是等到下一次订阅刷新周期。

### 范围
- 增加独立的配置文件监控组件
- 监控目标为服务启动时指定的配置文件路径
- 优先使用 `watchdog` 事件监听配置文件所在目录
- 在 `watchdog` 不可用时回退到轮询检测
- 对同一次保存产生的重复文件事件做防抖或去重
- 检测到文件内容或元数据变化后自动重新加载配置
- 配置校验通过后更新运行时配置
- 配置重读成功后主动触发一次即时刷新
- 配置校验失败时保留上一份有效配置并记录错误日志
- 将配置变更事件与订阅刷新逻辑解耦
- 支持在停止服务时优雅关闭监控线程
- 打包时确保 `watchdog` 依赖被正确带入
- 日志输出中的订阅敏感参数需要脱敏

### 不做
- 不要求配置变更后立即重绑 `server.listen` / `server.port`
- 不要求热更新已创建的日志 handler
- 不要求对同一次写入触发多次细粒度事件去重以外的复杂防抖策略

### 交付物
- `app.py`
- `service/config_watcher.py`
- `service/runner.py`
- `packaging/nuitka/common.sh`
- `pyproject.toml`
- `tests/test_app.py`
- `tests/test_service.py`
- `README.md`

### 验收标准
- 修改配置文件后，无需等待下一次订阅刷新周期即可触发配置重读
- 配置文件未变化时不会重复加载
- 已安装 `watchdog` 时优先使用事件监听
- 未安装 `watchdog` 时自动回退到轮询，功能保持可用
- 同一次配置文件保存不会导致重复配置重读日志
- 配置非法时服务保持运行，并继续使用上一份有效配置
- 修改 `subscription.*`、`server.refresh_interval`、`clash.*` 后，配置重读成功后会立即尝试使用新配置刷新
- 服务停止时配置监控线程能正常退出
- 日志中不会明文输出订阅 URL 的敏感 query 参数
- 日志中可看到配置文件变更、重载成功、重载失败等关键事件

---

## 建议实施顺序
1. 任务卡 1：搭建 `clash_sub_service/` 新工程骨架
2. 任务卡 2：定义配置模型与退出码
3. 任务卡 3：重构日志模块
4. 任务卡 4：迁移订阅拉取逻辑
5. 任务卡 5：迁移节点解析逻辑
6. 任务卡 6：迁移 Clash 配置生成逻辑
7. 任务卡 8：实现后台刷新服务
8. 任务卡 7：实现本地 HTTP 服务
9. 任务卡 9：实现 CLI 运行模式
10. 任务卡 10：增加本地 smoke test
11. 任务卡 11：增加 Nuitka 打包脚本
12. 任务卡 12：增加系统服务示例
13. 任务卡 13：增加配置文件监控与自动重读

---

## 总体验收目标
完成后应满足：

- 可通过配置文件启动后台服务
- 周期拉取订阅并生成 Clash YAML
- 本地仅暴露 `GET /clash.yaml`
- 支持 `stdout` 彩色日志和文件日志
- 文件日志支持轮转
- 配置文件变更后可主动触发重读，而不是仅依赖刷新周期
- 可在 `macOS` 和 `Ubuntu` 上使用 `nuitka` 打包
- 可通过本地 smoke test 验证核心能力
