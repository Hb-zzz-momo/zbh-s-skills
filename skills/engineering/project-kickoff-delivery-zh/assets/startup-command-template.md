# 启动命令模板

## 模型服务

```powershell
cd <model-service-path>
.\.venv\Scripts\activate
$env:MODEL_MODE="<mode>"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 后端

```powershell
cd <backend-path>
.\.venv\Scripts\activate
$env:MODEL_SERVICE_URL="http://127.0.0.1:8001/api/v1"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 前端

```powershell
cd <frontend-path>
npm run dev -- --host 0.0.0.0 --port 5173
```

## 访问地址

- 前端：
- 后端文档：
- 模型服务文档：
