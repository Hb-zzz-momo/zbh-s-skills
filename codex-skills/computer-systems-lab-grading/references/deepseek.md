# DeepSeek V4.1 Flash 接入约定

后端0.3.0的Word主路径已改为先事实核对、再评分，通常两次调用；详见[word-first-workflow.md](word-first-workflow.md)。本文件后文旧试批分数仅为0.2.0历史记录；当前试批与失败记录见项目docs/development/word-first-pilot-result.json，未教师校准。

核验日期：2026-09-24。用户指定内部接入DeepSeek V4.1 Flash。官方当前调用名为`deepseek-flash`，原生支持图像。名称是服务别名，不能据此保证以后仍指向同一模型权重；每批应保存请求配置、响应model字段和提供方可用版本信息，并在别名发生变化时重跑校准集。[官方发布说明](https://api-docs.deepseek.com/zh-cn/news/news260910/)

默认配置建议：

```json
{
  "endpoint": "https://api.deepseek.com/chat/completions",
  "model": "deepseek-flash",
  "api_key_env": "DEEPSEEK_API_KEY",
  "max_tokens": 16000,
  "timeout_seconds": 180,
  "max_retries": 2,
  "max_images": 160,
  "thinking": "disabled",
  "simulation": false
}
```

内网代理可替换endpoint/model，必须仍兼容图像和JSON参数，正式调用要求HTTPS且不跟随重定向。密钥在发送时读取DEEPSEEK_API_KEY或用户指定credential_file，不进入skill、提示词或日志。provider.py构造/解析，transport.py执行HTTP及有限重试，storage.py持久化可见响应和审计元数据。配置只保存密钥文件位置，不保存密钥值。

Chat Completions图像必须放在user消息；传`image_url`数据URL以及`detail=original`。报告中的细小代码应裁剪为可读图片，并保留原图位置和父图哈希。detail=original也不能保证字迹全部读对；仍需用原图复核关键符号、地址和运算符。[官方图像指南](https://api-docs.deepseek.com/guides/vision/)

使用`response_format={"type":"json_object"}`并在提示中明确JSON及示例。空响应、截断和非法结构都视为任务失败/重试，不转成缺答；JSON模式保证不了评分事实正确。`finish_reason`不是stop时拒绝结果。[官方JSON说明](https://api-docs.deepseek.com/guides/json_mode/)

运行参数由一份批次配置固定。温度低不能证明公平，也不保证确定性；本版不依赖temperature参数控制一致性。评分的一致性来自固定规则、证据定位、程序汇总、盲评校准和争议复核。收到429/5xx或超时后有限退避重试；超过次数标记待处理，不伪造0分、不静默切换另一模型。

运输层已记录请求体哈希、任务关联、响应ID/model、状态码、finish_reason、usage、耗时及原始可见JSON；不持久化隐藏推理。规则、证据、提示指纹和模型配置随任务冻结。报告图像中的身份文字仍可能存在，本版不是严格匿名化系统。

2026-09-24在用户授权的本机密钥下完成实验2、实验3真实调用。第一轮未显式关闭思考模式，16000个输出token耗在推理后截断，程序拒绝评分；因此默认thinking=disabled。实验2产出97.5建议分；实验3缺答引用不完整，相关项转为待复核，区间75—100而非确定分数。全部保留原响应，未发布任何学生正式成绩。两份试批只验证链路，不证明评分公平或准确；完整记录见项目docs/development/live-pilot-result.json。
