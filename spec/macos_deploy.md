# macOS 部署文档

## 目标

本文档说明如何在 macOS 上使用 `clash-sub-service-*.pkg` 安装、配置、启动、托管、升级和卸载 `clash_sub_service`。

适用产物：

```bash
/Users/lidan/Src/gen_clash_from_url/clash_sub_service/dist/nuitka/clash-sub-service-0.1.0.pkg
```

---

## 1. 安装

图形方式：

- 双击 `.pkg`
- 按安装向导完成安装

命令行方式：

```bash
sudo installer -pkg /Users/lidan/Src/gen_clash_from_url/clash_sub_service/dist/nuitka/clash-sub-service-0.1.0.pkg -target /
```

安装完成后，默认文件位置如下：

- 启动命令：
  ```bash
  /usr/local/bin/clash-sub-service
  ```
- 程序目录：
  ```bash
  /usr/local/lib/clash-sub-service
  ```
- 配置示例：
  ```bash
  /usr/local/etc/clash-sub-service/config.example.yaml
  ```
- 正式配置：
  ```bash
  /usr/local/etc/clash-sub-service/config.yaml
  ```
- LaunchDaemon：
  ```bash
  /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
  ```
- `launchctl` Label：
  ```bash
  com.lyratec.clash-sub-service
  ```
- `pkg` Identifier：
  ```bash
  com.lyratec.clash-sub-service
  ```

---

## 2. 准备配置

安装完成后，如果 `config.yaml` 不存在，安装脚本会自动从示例文件复制一份：

```bash
/usr/local/etc/clash-sub-service/config.yaml
```

如需重建正式配置：

```bash
sudo mkdir -p /usr/local/etc/clash-sub-service
sudo cp /usr/local/etc/clash-sub-service/config.example.yaml /usr/local/etc/clash-sub-service/config.yaml
```

编辑配置：

```bash
sudo vi /usr/local/etc/clash-sub-service/config.yaml
```

建议至少确认这些项：

- `output.path`
- `server.listen`
- `server.port`
- `server.refresh_interval`
- `logging.file.path`

---

## 3. 真实订阅 URL 的处理

真实订阅 URL 不建议写入受版本控制文件。

当前 `.pkg` 安装的是系统级 `LaunchDaemon`，以 `root` 运行。

推荐做法是直接编辑本机配置文件：

```bash
sudo vi /usr/local/etc/clash-sub-service/config.yaml
```

将下面这一项改成真实值：

```yaml
subscription:
  url: "https://jmssub.net/members/getsub.php?service=***&id=***"
```

修改以下配置后，无需重启 `launchctl` 服务，配置监控会主动触发重读：

- `subscription.url`
- `subscription.timeout`
- `clash.port`
- `clash.allow_lan`
- `server.refresh_interval`

说明：

- 服务优先使用 `watchdog` 监听配置文件变化
- 如果运行环境没有 `watchdog`，会自动回退到轮询检测

修改以下配置后，仍然需要重启服务进程或重新加载 `LaunchDaemon`：

- `server.listen`
- `server.port`
- `logging.*`

原因：

- 当前实现不会热更新已创建的日志 handler
- 当前实现不会在配置变更后自动重绑 HTTP 监听地址和端口

---

## 4. 配置校验

安装完成后先校验配置：

```bash
/usr/local/bin/clash-sub-service validate-config -c /usr/local/etc/clash-sub-service/config.yaml
```

预期结果：

- 退出码：`0`
- 输出或日志包含：
  ```text
  配置校验成功
  ```

如果失败：

- 退出码：`2`
- 日志中会给出具体字段错误

---

## 5. 执行一次生成

用于验证订阅拉取、解析和 YAML 输出是否正常：

```bash
/usr/local/bin/clash-sub-service once -c /usr/local/etc/clash-sub-service/config.yaml
```

预期结果：

- 退出码：`0`
- 配置中的 `output.path` 对应文件被写出

---

## 6. 前台启动后台服务

手工联调时可直接前台启动：

```bash
/usr/local/bin/clash-sub-service serve -c /usr/local/etc/clash-sub-service/config.yaml
```

启动后验证：

```bash
curl -fsS http://127.0.0.1:9095/clash.yaml
```

预期结果：

- HTTP 状态：`200`
- 返回内容：Clash YAML

未就绪时：

- HTTP 状态：`503`
- 返回错误文本

---

## 7. launchd 托管

`.pkg` 已经把 `LaunchDaemon` 安装到系统路径，并在安装后自动执行：

- `launchctl bootstrap system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist`
- `launchctl kickstart -k system/com.lyratec.clash-sub-service`

查看状态：

```bash
sudo launchctl print system/com.lyratec.clash-sub-service
```

停止：

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
```

重新加载：

```bash
sudo launchctl bootstrap system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
sudo launchctl kickstart -k system/com.lyratec.clash-sub-service
```

---

## 8. 日志

如果配置里启用了文件日志，查看方式例如：

```bash
tail -f /usr/local/var/log/clash-sub-service/app.log
```

如果通过 `launchd` 托管，还可以看：

```bash
tail -f /usr/local/var/log/clash-sub-service/launchd.stdout.log
tail -f /usr/local/var/log/clash-sub-service/launchd.stderr.log
```

日志中已识别的敏感 query 参数会被脱敏，例如：

```text
token=***&password=***
```

---

## 9. 升级

重新安装新的 `.pkg` 即可：

```bash
sudo installer -pkg /PATH/TO/clash-sub-service-NEW.pkg -target /
```

如果使用 `launchd`：

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
sudo installer -pkg /PATH/TO/clash-sub-service-NEW.pkg -target /
sudo launchctl bootstrap system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
sudo launchctl kickstart -k system/com.lyratec.clash-sub-service
```

---

## 10. 卸载

停止服务：

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist || true
```

删除文件：

```bash
sudo rm -f /usr/local/bin/clash-sub-service
sudo rm -rf /usr/local/lib/clash-sub-service
sudo rm -rf /usr/local/etc/clash-sub-service
sudo rm -rf /usr/local/var/log/clash-sub-service
sudo rm -f /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
```

---

## 11. 最小验收流程

1. 安装：

```bash
sudo installer -pkg /Users/lidan/Src/gen_clash_from_url/clash_sub_service/dist/nuitka/clash-sub-service-0.1.0.pkg -target /
```

2. 校验配置：

```bash
/usr/local/bin/clash-sub-service validate-config -c /usr/local/etc/clash-sub-service/config.yaml
```

3. 写入真实订阅 URL：

```bash
sudo vi /usr/local/etc/clash-sub-service/config.yaml
```

4. 重新加载系统服务：

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist || true
sudo launchctl bootstrap system /Library/LaunchDaemons/com.lyratec.clash-sub-service.plist
sudo launchctl kickstart -k system/com.lyratec.clash-sub-service
```

5. 请求本地订阅：

```bash
curl -fsS http://127.0.0.1:9095/clash.yaml
```

预期结果：

- 配置校验退出码：`0`
- 服务启动后可返回 YAML
- `curl` 退出码：`0`
