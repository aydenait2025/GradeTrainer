# AI 模型微调系统 - 前端

这是 AI 模型微调系统的 React 前端应用。

## 🚀 快速开始

### 开发环境

1. **安装依赖**
```bash
npm install
# 或使用启动脚本
./start.sh install
```

2. **启动开发服务器**
```bash
npm run dev
# 或使用启动脚本
./start.sh dev
```

3. **访问应用**
- 开发服务器: http://localhost:3000
- 后端 API: http://localhost:8000

### 生产环境

1. **构建应用**
```bash
npm run build
# 或使用启动脚本
./start.sh build
```

2. **预览构建结果**
```bash
npm run preview
# 或使用启动脚本
./start.sh preview
```

## 📁 项目结构

```
frontend/
├── public/              # 静态资源
│   ├── index.html      # HTML 模板
│   └── vite.svg        # 图标
├── src/
│   ├── components/     # React 组件
│   │   ├── Dashboard.tsx           # 仪表板
│   │   ├── FileUpload.tsx          # 文件上传
│   │   ├── TrainingConfig.tsx      # 训练配置
│   │   ├── TrainingProgress.tsx    # 训练进度
│   │   ├── ModelList.tsx           # 模型管理
│   │   ├── Notification.tsx        # 通知组件
│   │   ├── Loading.tsx             # 加载组件
│   │   └── Modal.tsx               # 模态框组件
│   ├── services/       # API 服务
│   │   └── api.ts      # API 调用
│   ├── types/          # TypeScript 类型
│   │   └── index.ts    # 类型定义
│   ├── App.tsx         # 主应用组件
│   ├── main.tsx        # 应用入口
│   └── index.css       # 全局样式
├── package.json        # 项目配置
├── vite.config.ts      # Vite 配置
├── tsconfig.json       # TypeScript 配置
├── tailwind.config.js  # Tailwind 配置
├── postcss.config.js   # PostCSS 配置
├── .eslintrc.cjs       # ESLint 配置
├── Dockerfile          # Docker 构建文件
├── nginx.conf          # Nginx 配置
└── start.sh            # 启动脚本
```

## 🛠️ 开发指南

### 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run preview` - 预览构建结果
- `npm run lint` - 代码检查
- `./start.sh [command]` - 使用启动脚本

### 代码规范

项目使用以下工具确保代码质量：

- **TypeScript** - 类型安全
- **ESLint** - 代码检查
- **Prettier** - 代码格式化
- **Tailwind CSS** - 样式框架

### 组件说明

#### 核心页面组件

1. **Dashboard.tsx** - 系统仪表板
   - 显示系统状态
   - 资源监控
   - 最近任务

2. **FileUpload.tsx** - 文件上传
   - 拖拽上传
   - 文件格式验证
   - 数据预览

3. **TrainingConfig.tsx** - 训练配置
   - 参数设置
   - 模型选择
   - 配置验证

4. **TrainingProgress.tsx** - 训练进度
   - 实时进度显示
   - 日志查看
   - 任务控制

5. **ModelList.tsx** - 模型管理
   - 模型列表
   - 部署管理
   - 预测测试

#### 共享组件

1. **Notification.tsx** - 通知系统
   - 成功/错误/警告通知
   - 自动消失
   - 全局状态管理

2. **Loading.tsx** - 加载组件
   - 旋转加载器
   - 骨架屏
   - 进度条

3. **Modal.tsx** - 模态框
   - 可配置大小
   - 确认对话框
   - 提示框

### API 集成

所有 API 调用都通过 `src/services/api.ts` 进行：

```typescript
import { apiService } from '../services/api'

// 获取训练任务
const jobs = await apiService.getTrainingJobs()

// 上传文件
const result = await apiService.uploadFile(file)

// 创建训练任务
const job = await apiService.createTrainingJob(config, filePath)
```

### 状态管理

项目使用 React 内置的状态管理：

- `useState` - 组件本地状态
- `useContext` - 全局状态（通知系统）
- `useEffect` - 副作用处理

### 样式系统

使用 Tailwind CSS 进行样式开发：

```tsx
// 基础样式类
<div className="card">           // 自定义卡片样式
<button className="btn-primary"> // 主要按钮样式
<input className="form-input">   // 表单输入样式
```

自定义样式定义在 `src/index.css` 中。

## 🔧 配置说明

### Vite 配置

`vite.config.ts` 配置了：
- React 插件
- 开发服务器代理
- 构建选项

### Tailwind 配置

`tailwind.config.js` 扩展了：
- 自定义颜色
- 动画效果
- 响应式断点

### TypeScript 配置

`tsconfig.json` 配置了：
- 严格类型检查
- 路径映射
- 编译选项

## 📦 部署

### Docker 部署

使用提供的 Dockerfile：

```bash
docker build -t ai-tuning-frontend .
docker run -p 3000:80 ai-tuning-frontend
```

### 静态部署

构建后的 `dist/` 目录可直接部署到：
- Nginx
- Apache
- CDN
- 静态托管服务

### 环境变量

可通过环境变量配置：

```bash
# API 地址
REACT_APP_API_URL=http://localhost:8000

# 其他配置
REACT_APP_ENVIRONMENT=production
```

## 🐛 故障排除

### 常见问题

**Q: 开发服务器启动失败**
A: 检查 Node.js 版本是否 >= 16

**Q: API 请求失败**
A: 确认后端服务是否启动，检查代理配置

**Q: 构建失败**
A: 清理依赖重新安装 `rm -rf node_modules && npm install`

**Q: 样式不生效**
A: 检查 Tailwind CSS 配置和 PostCSS 设置

### 调试技巧

1. **使用浏览器开发工具**
   - Network 标签页检查 API 请求
   - Console 查看错误信息
   - React DevTools 调试组件

2. **使用 VSCode 调试**
   - 安装 React 调试扩展
   - 设置断点调试

3. **日志输出**
   ```typescript
   console.log('Debug info:', data)
   console.error('Error:', error)
   ```

## 📚 学习资源

- [React 官方文档](https://react.dev/)
- [TypeScript 手册](https://www.typescriptlang.org/docs/)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [Vite 文档](https://vitejs.dev/guide/)
- [Heroicons 图标库](https://heroicons.com/)

## 🤝 贡献

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License
