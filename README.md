# clash_sub_service

`clash_sub_service` 是一个面向本地部署的后台服务，用来拉取 JMS 提供的订阅地址、解析节点、生成 Clash YAML，并通过本地 HTTP 接口对外提供订阅内容。

## Features

- 拉取并解析 JMS 订阅地址返回的 `ss://` / `vmess://` 节点
- 生成 Clash YAML
- 仅暴露本地 `GET /clash.yaml`
- 后台定时刷新订阅
- 配置文件监控与自动重读
- 离线单元测试与本地 smoke test
- `nuitka` 打包支持
- `systemd` / `launchd` 部署样例

## Project Layout

- `src/`: 源码
- `tests/`: 单元测试、smoke test、测试夹具
- `packaging/`: `nuitka`、`systemd`、`launchd` 脚本与样例
- `spec/`: 任务卡、决策记录、部署文档

## Requirements

- Python `>= 3.10`
- macOS 或 Linux

安装依赖：

```bash
python3 -m pip install -e .
```

## Quick Start

1. 准备配置文件：

```bash
cp config.example.yaml local.config.yaml
```

2. 修改 `local.config.yaml` 中的订阅地址、输出路径和日志路径。

3. 校验配置：

```bash
PYTHONPATH=src python3 -m cli validate-config -c local.config.yaml
```

4. 执行一次生成：

```bash
PYTHONPATH=src python3 -m cli once -c local.config.yaml
```

5. 启动后台服务：

```bash
PYTHONPATH=src python3 -m cli serve -c local.config.yaml
```

6. 请求本地订阅：

```bash
curl -fsS http://127.0.0.1:9095/clash.yaml
```

## CLI

查看帮助：

```bash
PYTHONPATH=src python3 -m cli --help
```

可用命令：

- `validate-config`: 只校验配置，不访问网络
- `once`: 拉取订阅并生成一次 YAML
- `serve`: 启动后台服务

## Configuration

示例配置见 [config.example.yaml](/Users/lidan/Src/clash_sub_service/config.example.yaml)。

关键配置项：

- `subscription.url`
- `subscription.timeout`
- `server.listen`
- `server.port`
- `server.refresh_interval`
- `clash.port`
- `clash.allow_lan`
- `output.path`
- `logging.*`

说明：

- `subscription.url` 预期填写 JMS 提供的订阅地址
- 真实订阅 URL 不应提交到仓库
- 服务运行时会独立监控配置文件变化
- 优先使用 `watchdog` 事件监听；不可用时回退到轮询
- 配置变更后会主动重读，不需要等待下一次刷新周期
- 配置重读成功后会立即尝试刷新订阅并更新内存中的 YAML 状态
- 非法配置不会中断服务，而是继续使用上一份有效配置
- `server.listen` / `server.port` 和已创建的日志 handler 不会热更新

## Testing

运行离线单元测试：

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_fetcher \
  tests.test_parser \
  tests.test_builder \
  tests.test_service \
  tests.test_server \
  tests.test_cli \
  tests.test_app
```

运行本地 smoke test：

```bash
./tests/test_smoke.sh
```

运行完整验收：

```bash
./tests/test_all.sh
```

`test_smoke.sh` 会启动本地模拟订阅源，再启动服务并请求 `/clash.yaml`，不依赖外网。

## Packaging

Linux:

```bash
./packaging/nuitka/build_linux.sh
```

macOS:

```bash
./packaging/nuitka/build_macos.sh
```

macOS 打包产物默认为：

```bash
dist/nuitka/clash-sub-service-*.pkg
```

## Deployment

系统服务样例：

- [clash-sub-service.service](/Users/lidan/Src/clash_sub_service/packaging/systemd/clash-sub-service.service)
- [com.lyratec.clash-sub-service.plist](/Users/lidan/Src/clash_sub_service/packaging/launchd/com.lyratec.clash-sub-service.plist)

macOS 部署说明见：

- [macos_deploy.md](/Users/lidan/Src/clash_sub_service/spec/macos_deploy.md)
- [ubuntu_deploy.md](/Users/lidan/Src/clash_sub_service/spec/ubuntu_deploy.md)

## Notes

- 使用前请按实际环境修改配置中的路径与端口
