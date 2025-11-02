import axios from 'axios'
import { 
  TrainingJob, 
  TrainingJobCreate, 
  SystemStatus, 
  FileUploadResponse,
  TrainingProgress,
  ModelInfo,
  TrainingLog
} from '../types'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    throw new Error(message)
  }
)

export const apiService = {
  // 文件上传相关
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post('/api/v1/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 上传文件需要更长的超时时间
    })
    
    return response.data
  },

  async getSupportedFormats() {
    return api.get('/upload/supported-formats')
  },

  async deleteFile(filePath: string) {
    return api.delete(`/upload/file/${encodeURIComponent(filePath)}`)
  },

  // 训练任务相关
  async createTrainingJob(jobData: TrainingJobCreate, filePath: string): Promise<TrainingJob> {
    return api.post('/training/jobs', jobData, {
      params: { file_path: filePath }
    })
  },

  async getTrainingJobs(skip = 0, limit = 100, status?: string): Promise<TrainingJob[]> {
    return api.get('/training/jobs', {
      params: { skip, limit, status }
    })
  },

  async getTrainingJob(jobId: number): Promise<TrainingJob> {
    return api.get(`/training/jobs/${jobId}`)
  },

  async deleteTrainingJob(jobId: number) {
    return api.delete(`/training/jobs/${jobId}`)
  },

  async stopTrainingJob(jobId: number) {
    return api.post(`/training/jobs/${jobId}/stop`)
  },

  async restartTrainingJob(jobId: number) {
    return api.post(`/training/jobs/${jobId}/restart`)
  },

  async getTrainingLogs(jobId: number, skip = 0, limit = 1000, logLevel?: string): Promise<TrainingLog[]> {
    return api.get(`/training/jobs/${jobId}/logs`, {
      params: { skip, limit, log_level: logLevel }
    })
  },

  async getTrainingProgress(jobId: number): Promise<TrainingProgress> {
    return api.get(`/training/jobs/${jobId}/progress`)
  },

  async getSystemStatus(): Promise<SystemStatus> {
    return api.get('/training/status')
  },

  // 模型管理相关
  async getModels(skip = 0, limit = 100, isDeployed?: boolean): Promise<ModelInfo[]> {
    return api.get('/models/', {
      params: { skip, limit, is_deployed: isDeployed }
    })
  },

  async getModel(modelId: number): Promise<ModelInfo> {
    return api.get(`/models/${modelId}`)
  },

  async downloadModel(modelId: number): Promise<Blob> {
    const response = await axios.get(`/api/v1/models/${modelId}/download`, {
      responseType: 'blob'
    })
    return response.data
  },

  async deployModel(modelId: number) {
    return api.post(`/models/${modelId}/deploy`)
  },

  async undeployModel(modelId: number) {
    return api.delete(`/models/${modelId}/deploy`)
  },

  async predictWithModel(modelId: number, inputText: string, options: {
    maxLength?: number
    temperature?: number
    topP?: number
  } = {}) {
    return api.post(`/models/${modelId}/predict`, {
      input_text: inputText,
      max_length: options.maxLength || 512,
      temperature: options.temperature || 0.7,
      top_p: options.topP || 0.9
    })
  },

  async deleteModel(modelId: number) {
    return api.delete(`/models/${modelId}`)
  },

  async getModelConfig(modelId: number) {
    return api.get(`/models/${modelId}/config`)
  },

  async validateModel(modelId: number) {
    return api.post(`/models/${modelId}/validate`)
  },

  async getSupportedModels() {
    return api.get('/models/supported/base-models')
  },

  // 监控相关
  async getSystemMetrics() {
    return api.get('/monitoring/system')
  },

  async getTrainingStatistics() {
    return api.get('/monitoring/training/statistics')
  },

  async getActiveTrainingJobs() {
    return api.get('/monitoring/training/active')
  },

  async getCeleryStatus() {
    return api.get('/monitoring/celery/status')
  },

  async getRecentLogs(limit = 100, logLevel?: string, jobId?: number) {
    return api.get('/monitoring/logs/recent', {
      params: { limit, log_level: logLevel, job_id: jobId }
    })
  },

  async getStorageUsage() {
    return api.get('/monitoring/storage/usage')
  },

  async getHealthCheck() {
    return api.get('/monitoring/health')
  },
}

// 工具函数
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  } else {
    return `${remainingSeconds}s`
  }
}

export const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    pending: 'text-yellow-600 bg-yellow-100',
    running: 'text-blue-600 bg-blue-100',
    completed: 'text-green-600 bg-green-100',
    failed: 'text-red-600 bg-red-100',
    stopped: 'text-gray-600 bg-gray-100',
  }
  return colorMap[status] || 'text-gray-600 bg-gray-100'
}

export const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
  }
  return textMap[status] || status
}
