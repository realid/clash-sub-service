# Ubuntu 部署文档

## 目标

本文档说明如何在 Ubuntu 上安装、配置、启动、托管、升级和卸载 `clash_sub_service`。

适用方式：

- 使用 `nuitka` 构建出的 Linux 可执行产物
- 配合 `systemd` 托管服务

---

## 1. 准备产物

先在构建机执行：

```bash
./packaging/nuitka/build_linux.sh
```

默认产物位于：

```bash
dist/nuitka/
```

将可执行文件和配置文件部署到目标机，例如：

- 可执行文件：
  ```bash
  /usr/local/bin/clash-sub-service
  ```
- 配置目录：
  ```bash
  /usr/local/etc/clash-sub-service
  ```
- 日志目录：
  ```bash
  /usr/local/var/log/clash-sub-service
  ```

---

## 2. 安装文件

创建目录：

```bash
sudo mkdir -p /usr/local/bin
sudo mkdir -p /usr/local/etc/clash-sub-service
sudo mkdir -p /usr/local/var/log/clash-sub-service
```

复制可执行文件：

```bash
sudo cp /PATH/TO/dist/nuitka/clash-sub-service.dist/clash-sub-service /usr/local/bin/clash-sub-service
sudo chmod +x /usr/local/bin/clash-sub-service
```

复制配置示例：

```bash
sudo cp config.example.yaml /usr/local/etc/clash-sub-service/config.yaml
```

复制 `systemd` 样例：

```bash
sudo cp packaging/systemd/clash-sub-service.service /etc/systemd/system/clash-sub-service.service
```

---

## 3. 准备配置

编辑配置文件：

```bash
sudo vi /usr/local/etc/clash-sub-service/config.yaml
```

建议至少确认这些项：

- `subscription.url`
- `output.path`
- `server.listen`
- `server.port`
- `server.refresh_interval`
- `logging.file.path`

说明：

- `subscription.url` 预期填写 JMS 提供的订阅地址
- 真实订阅 URL 不建议写入仓库
- 配置文件变更后服务会主动重读
- 优先使用 `watchdog`；不可用时回退到轮询
- 配置重读成功后会立即尝试刷新订阅

以下配置修改后通常无需重启服务：

- `subscription.*`
- `clash.*`
- `server.refresh_interval`

以下配置修改后需要重启服务：

- `server.listen`
- `server.port`
- `logging.*`

---

## 4. 配置校验

校验配置：

```bash
/usr/local/bin/clash-sub-service validate-config -c /usr/local/etc/clash-sub-service/config.yaml
```

预期结果：

- 退出码：`0`
- 输出或日志包含：
  ```text
  配置校验成功
  ```

---

## 5. 执行一次生成

用于验证订阅拉取、解析和 YAML 输出是否正常：

```bash
/usr/local/bin/clash-sub-service once -c /usr/local/etc/clash-sub-service/config.yaml
```

预期结果：

- 退出码：`0`
- `output.path` 对应文件被写出

---

## 6. 前台启动服务

手工联调时可直接前台启动：

```bash
/usr/local/bin/clash-sub-service serve -c /usr/local/etc/clash-sub-service/config.yaml
```

启动后验证：

```bash
curl -fsS http://127.0.0.1:9095/clash.yaml
```

---

## 7. systemd 托管

编辑服务文件：

```bash
sudo vi /etc/systemd/system/clash-sub-service.service
```

重点替换以下占位项：

- `User=YOUR_USER`
- `Group=YOUR_GROUP`
- `WorkingDirectory=/ABS/PATH/TO/clash_sub_service`
- `Environment=PYTHONPATH=/ABS/PATH/TO/clash_sub_service/src`
- `ExecStart=/ABS/PATH/TO/clash-sub-service serve -c /ABS/PATH/TO/config.yaml`

重新加载并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable clash-sub-service
sudo systemctl restart clash-sub-service
```

查看状态：

```bash
sudo systemctl status clash-sub-service
```

停止服务：

```bash
sudo systemctl stop clash-sub-service
```

重启服务：

```bash
sudo systemctl restart clash-sub-service
```

---

## 8. 日志

如果启用了文件日志，查看方式例如：

```bash
tail -f /usr/local/var/log/clash-sub-service/app.log
```

如果通过 `systemd` 托管，也可以查看：

```bash
journalctl -u clash-sub-service -f
```

---

## 9. 升级

替换可执行文件后重启服务：

```bash
sudo cp /PATH/TO/dist/nuitka/clash-sub-service.dist/clash-sub-service /usr/local/bin/clash-sub-service
sudo chmod +x /usr/local/bin/clash-sub-service
sudo systemctl restart clash-sub-service
```

如果 `systemd` 文件也有变更：

```bash
sudo cp packaging/systemd/clash-sub-service.service /etc/systemd/system/clash-sub-service.service
sudo systemctl daemon-reload
sudo systemctl restart clash-sub-service
```

---

## 10. 卸载

停止并禁用服务：

```bash
sudo systemctl stop clash-sub-service || true
sudo systemctl disable clash-sub-service || true
```

删除文件：

```bash
sudo rm -f /etc/systemd/system/clash-sub-service.service
sudo rm -f /usr/local/bin/clash-sub-service
sudo rm -rf /usr/local/etc/clash-sub-service
sudo rm -rf /usr/local/var/log/clash-sub-service
```

重新加载 `systemd`：

```bash
sudo systemctl daemon-reload
```

---

## 11. 最小验收流程

1. 复制可执行文件和配置文件
2. 执行：

```bash
/usr/local/bin/clash-sub-service validate-config -c /usr/local/etc/clash-sub-service/config.yaml
```

3. 写入真实 JMS 订阅地址
4. 启动服务：

```bash
sudo systemctl restart clash-sub-service
```

5. 请求本地订阅：

```bash
curl -fsS http://127.0.0.1:9095/clash.yaml
```

预期结果：

- 返回 HTTP `200`
- 响应内容为 Clash YAML
