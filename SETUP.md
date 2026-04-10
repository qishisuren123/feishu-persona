# 飞书人格基因分析机器人 - 部署指南

## 第一步：创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app) → 创建企业自建应用
2. 填写应用名称（如「人格基因分析」）和描述
3. 记下 **App ID** 和 **App Secret**

## 第二步：配置应用权限

在应用后台 → **权限管理** 中开通以下权限：

| 权限 | 说明 |
|------|------|
| `im:message` | 发送消息 |
| `im:message:readonly` | 读取消息 |
| `im:chat:readonly` | 获取群信息 |
| `contact:user.base:readonly` | 获取用户基本信息 |

## 第三步：启用机器人

应用后台 → **添加应用能力** → 勾选 **机器人**

## 第四步：部署服务

### 方式A：直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_APP_ID=cli_xxxx
export FEISHU_APP_SECRET=xxxx
export ANTHROPIC_API_KEY=sk-ant-xxxx

# 启动
python app.py
```

### 方式B：Docker

```bash
docker build -t feishu-persona .
docker run -d --name feishu-persona \
  -e FEISHU_APP_ID=cli_xxxx \
  -e FEISHU_APP_SECRET=xxxx \
  -e ANTHROPIC_API_KEY=sk-ant-xxxx \
  -p 9000:9000 \
  feishu-persona
```

### 方式C：一键部署到 Railway / Render / 阿里云

略，参考各平台文档。

## 第五步：配置事件订阅

1. 应用后台 → **事件订阅**
2. 请求地址填：`https://你的域名/webhook/event`
3. 如果服务已启动，飞书会自动发送验证请求
4. 添加事件：`im.message.receive_v1`（接收消息）

## 第六步：发布应用

1. 应用后台 → **版本管理与发布** → 创建版本 → 申请发布
2. 管理员审批通过后生效
3. 用户在飞书中搜索机器人名称即可使用

## 使用方式

- **群聊**：@机器人 分析我
- **私聊**：直接发送「分析我」
- **帮助**：发送「帮助」

## 常见问题

**Q: 提示消息太少？**
A: 机器人需要读取你在该群中的历史消息，至少要有5条。新群里先多聊几句。

**Q: 分析结果准吗？**
A: 基于AI语义分析，消息越多越准（建议50条以上）。仅供娱乐参考。

**Q: 能分析别人吗？**
A: 当前版本只支持「分析我」，分析自己。后续可扩展。
