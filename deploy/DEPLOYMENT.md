# 部署指南

## 阿里云ECS部署到 prompt.westwetlandtech.com

### 前置要求

1. 阿里云ECS服务器（推荐配置：2核4G以上）
2. 域名 prompt.westwetlandtech.com 已解析到服务器IP
3. 开放端口：80, 443, 22

### 快速部署

1. **上传代码到服务器**

```bash
# 本地执行
scp -r /path/to/proper-prompts root@your-server-ip:/opt/
```

2. **SSH登录服务器执行部署**

```bash
ssh root@your-server-ip
cd /opt/proper-prompts/deploy
chmod +x deploy.sh
./deploy.sh
```

3. **配置环境变量**

```bash
# 编辑环境变量
vim /opt/proper-prompts/deploy/.env

# 必须配置 OPENAI_API_KEY
OPENAI_API_KEY=your-actual-api-key
```

4. **重启服务**

```bash
cd /opt/proper-prompts/deploy
docker-compose restart
```

### 部署命令详解

```bash
# 完整部署（首次）
./deploy.sh deploy

# 仅安装依赖
./deploy.sh install

# 仅设置SSL证书
./deploy.sh ssl

# 更新代码后重新部署
./deploy.sh update

# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 创建备份
./deploy.sh backup

# 重启服务
./deploy.sh restart

# 停止服务
./deploy.sh stop
```

### 手动部署步骤

如果自动部署脚本出现问题，可以手动执行：

```bash
# 1. 安装Docker
curl -fsSL https://get.docker.com | bash
systemctl enable docker
systemctl start docker

# 2. 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. 创建目录
mkdir -p /opt/proper-prompts
cd /opt/proper-prompts

# 4. 复制项目文件到此目录

# 5. 配置环境变量
cp deploy/env.example deploy/.env
vim deploy/.env

# 6. 获取SSL证书
certbot certonly --standalone -d prompt.westwetlandtech.com
mkdir -p deploy/ssl
cp /etc/letsencrypt/live/prompt.westwetlandtech.com/fullchain.pem deploy/ssl/
cp /etc/letsencrypt/live/prompt.westwetlandtech.com/privkey.pem deploy/ssl/

# 7. 启动服务
cd deploy
docker-compose up -d
```

### 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查后端健康
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 检查HTTPS
curl https://prompt.westwetlandtech.com/health
```

### 日志位置

- 应用日志: `/opt/proper-prompts/logs/`
- Nginx日志: `docker-compose logs nginx`
- 后端日志: `docker-compose logs backend`
- 前端日志: `docker-compose logs frontend`

### 备份策略

建议设置定时备份：

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/proper-prompts/deploy/backup.sh
```

### 常见问题

**Q: SSL证书获取失败**
A: 确保80端口可访问，且域名已正确解析

**Q: 数据库连接失败**
A: 等待PostgreSQL完全启动，检查docker-compose logs postgres

**Q: 后端启动失败**
A: 检查环境变量配置，特别是DATABASE_URL格式

### 监控和告警

建议配置阿里云云监控，监控以下指标：
- CPU使用率
- 内存使用率
- 磁盘使用率
- HTTP请求成功率

