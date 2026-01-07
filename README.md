# Proper Prompts - 群聊分析与Prompt管理系统

一个智能群聊分析系统，能根据群组性质自动生成和评测不同的Prompt。

## 🎯 功能特性

### 1. 群聊分析
- **多类型群组支持**：投资群、科普群、学习群、技术群等
- **多时间维度分析**：天、月、季度、年度、自定义日期范围
- **成员维度分析**：支持指定特定成员进行分析
- **智能Prompt生成**：根据群组类型自动生成专属Prompt模板

### 2. Prompt评测系统
- 对同一需求生成多个不同风格的Prompt
- A/B测试评测不同Prompt的效果
- 效果指标：相关性、准确性、完整性、可读性

### 3. 对外API
- RESTful API设计
- 支持与其他项目集成：
  - Browser-LLM-Orchastrator
  - chatlog
  - health-llm-driven
- API密钥认证

### 4. 日志与监控
- 功能日志：详细记录业务操作
- 性能日志：追踪API响应时间
- 前端Debug日志：浏览器端调试信息

### 5. 测试覆盖
- 单元测试
- 集成测试
- API测试

## 🏗 技术架构

```
├── backend/                # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── tests/             # 单元测试
│   └── requirements.txt
├── frontend/              # 前端 (React + TypeScript)
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API服务
│   │   ├── hooks/         # 自定义hooks
│   │   └── utils/         # 工具函数
│   └── package.json
├── deploy/                # 部署脚本
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── deploy.sh
└── docs/                  # 文档
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 本地开发

```bash
# 克隆项目
git clone https://github.com/your-repo/proper-prompts.git
cd proper-prompts

# 后端启动
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端启动 (新终端)
cd frontend
npm install
npm run dev
```

### 部署到阿里云ECS

```bash
cd deploy
./deploy.sh
```

## 📡 API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📄 许可证

MIT License

