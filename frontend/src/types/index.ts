// API 响应类型定义

export interface TrainingJob {
  id: number
  job_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped'
  upload_filename: string
  model_name: string
  epochs: number
  batch_size: number
  learning_rate: number
  use_fp16: boolean
  use_quantization: boolean
  lora_r: number
  lora_alpha: number
  lora_dropout: number
  final_loss?: number
  validation_accuracy?: number
  model_path?: string
  celery_task_id?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface TrainingParams {
  model_name: string
  epochs: number
  batch_size: number
  learning_rate: number
  use_fp16: boolean
  use_quantization: boolean
  lora_r: number
  lora_alpha: number
  lora_dropout: number
}

export interface TrainingJobCreate {
  job_name: string
  training_params: TrainingParams
}

export interface TrainingLog {
  id: number
  job_id: number
  log_level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  metrics?: Record<string, any>
  timestamp: string
}

export interface TrainingProgress {
  job_id: number
  current_epoch: number
  total_epochs: number
  current_step: number
  total_steps: number
  current_loss?: number
  average_loss?: number
  learning_rate?: number
  elapsed_time?: number
  estimated_remaining?: number
}

export interface ModelInfo {
  id: number
  job_id: number
  model_name: string
  model_path: string
  model_size?: number
  config?: Record<string, any>
  is_deployed: boolean
  api_endpoint?: string
  created_at: string
}

export interface DatasetInfo {
  id: number
  job_id: number
  total_samples?: number
  train_samples?: number
  val_samples?: number
  test_samples?: number
  avg_input_length?: number
  avg_output_length?: number
  unique_labels?: number
  processed_data_path?: string
  created_at: string
}

export interface FileUploadResponse {
  filename: string
  file_path: string
  file_size: number
  upload_time: string
  data_preview?: {
    csv_files?: number
    assignment_files?: number
    total_records?: number
    students?: number
    assignments?: number
    score_range?: {
      min: number
      max: number
      mean: number
    }
    sample_data?: Record<string, any>[]
    column_names?: string[]
    columns?: number
    data_types?: Record<string, string>
    missing_values?: Record<string, number>
  }
}

export interface SystemStatus {
  total_jobs: number
  running_jobs: number
  completed_jobs: number
  failed_jobs: number
  gpu_usage?: {
    available: boolean
    device_count?: number
    devices?: {
      index: number
      name: string
      memory: {
        total: number
        used: number
        free: number
        usage_percent: number
      }
      utilization: {
        gpu_percent: number
        memory_percent: number
      }
      temperature?: number
    }[]
    error?: string
  }
  disk_usage?: {
    total: number
    used: number
    free: number
    usage_percent: number
  }
  memory_usage?: {
    total: number
    available: number
    used: number
    usage_percent: number
    cached?: number
    buffers?: number
  }
}

export interface PredictionRequest {
  model_id: number
  input_text: string
  max_length?: number
  temperature?: number
  top_p?: number
}

export interface PredictionResponse {
  input_text: string
  generated_text: string
  confidence?: number
  processing_time: number
}

export interface ErrorResponse {
  error: string
  detail?: string
  error_code?: string
}

// 训练统计信息
export interface TrainingStatistics {
  status_distribution: Record<string, number>
  model_distribution: Record<string, number>
  daily_trend: {
    date: string
    count: number
  }[]
  average_training_time_seconds?: number
  total_jobs: number
  completed_jobs: number
}

// 系统资源监控
export interface SystemMetrics {
  cpu: {
    usage_percent: number
    core_count: number
    load_average?: number[]
  }
  memory: {
    total: number
    available: number
    used: number
    usage_percent: number
  }
  disk: {
    total: number
    used: number
    free: number
    usage_percent: number
  }
  gpu?: {
    available: boolean
    device_count?: number
    devices?: {
      index: number
      name: string
      memory: {
        total: number
        used: number
        free: number
        usage_percent: number
      }
      utilization: {
        gpu_percent: number
        memory_percent: number
      }
      temperature?: number
    }[]
  }
  timestamp: string
}

// Celery 状态
export interface CeleryStatus {
  active_tasks: Record<string, any>
  scheduled_tasks: Record<string, any>
  reserved_tasks: Record<string, any>
  worker_stats: Record<string, any>
  available_workers: string[]
}

// 存储使用情况
export interface StorageUsage {
  upload_directory: {
    path: string
    size_bytes: number
    size_mb: number
  }
  model_directory: {
    path: string
    size_bytes: number
    size_mb: number
  }
  total_used: {
    size_bytes: number
    size_mb: number
  }
  disk_usage: {
    total_bytes: number
    used_bytes: number
    free_bytes: number
    usage_percent: number
  }
}

// 健康检查
export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  checks: Record<string, {
    status: 'ok' | 'warning' | 'error'
    message: string
  }>
}

// 支持的模型信息
export interface SupportedModels {
  supported_models: string[]
  model_info: Record<string, {
    description: string
    size: string
    type: string
    requires_auth: boolean
  }>
}

// 组件状态类型
export interface ComponentState {
  loading: boolean
  error?: string
  data?: any
}

// 表单状态
export interface FormState {
  values: Record<string, any>
  errors: Record<string, string>
  touched: Record<string, boolean>
  isSubmitting: boolean
}

// 通知类型
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

// 分页信息
export interface Pagination {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

// 排序信息
export interface SortInfo {
  field: string
  direction: 'asc' | 'desc'
}

// 过滤信息
export interface FilterInfo {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in'
  value: any
}

// 表格列定义
export interface TableColumn {
  key: string
  title: string
  width?: number
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, record: any) => React.ReactNode
}

// 图表数据点
export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
  color?: string
}

// 图表配置
export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area'
  data: ChartDataPoint[]
  options?: Record<string, any>
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

// 模态框状态
export interface ModalState {
  isOpen: boolean
  title?: string
  content?: React.ReactNode
  onConfirm?: () => void
  onCancel?: () => void
}

// 主题配置
export interface ThemeConfig {
  mode: 'light' | 'dark'
  primaryColor: string
  secondaryColor: string
  fontSize: 'small' | 'medium' | 'large'
}

// 用户偏好设置
export interface UserPreferences {
  theme: ThemeConfig
  language: 'zh-CN' | 'en-US'
  notifications: {
    email: boolean
    push: boolean
    desktop: boolean
  }
  autoRefresh: boolean
  refreshInterval: number
}
