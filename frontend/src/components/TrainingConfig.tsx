import React, { useState, useEffect } from 'react'
import { 
  CogIcon, 
  PlayIcon, 
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { apiService } from '../services/api'
import { TrainingJobCreate, SupportedModels } from '../types'

interface TrainingConfigProps {
  uploadedFile?: {
    filename: string
    file_path: string
  }
}

function TrainingConfig({ uploadedFile }: TrainingConfigProps) {
  const [config, setConfig] = useState({
    job_name: '',
    training_params: {
      model_name: 'meta-llama/Llama-2-7b-chat-hf',
      epochs: 3,
      batch_size: 4,
      learning_rate: 0.0002,
      use_fp16: true,
      use_quantization: false,
      lora_r: 16,
      lora_alpha: 32,
      lora_dropout: 0.1
    }
  })
  
  const [supportedModels, setSupportedModels] = useState<SupportedModels | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    fetchSupportedModels()
  }, [])

  const fetchSupportedModels = async () => {
    try {
      const data = await apiService.getSupportedModels()
      setSupportedModels(data)
    } catch (error) {
      console.error('获取支持的模型失败:', error)
    }
  }

  const handleInputChange = (field: string, value: any) => {
    if (field.startsWith('training_params.')) {
      const paramField = field.replace('training_params.', '')
      setConfig(prev => ({
        ...prev,
        training_params: {
          ...prev.training_params,
          [paramField]: value
        }
      }))
    } else {
      setConfig(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  const validateConfig = () => {
    const errors: string[] = []
    
    if (!config.job_name.trim()) {
      errors.push('请输入任务名称')
    }
    
    if (config.training_params.epochs < 1 || config.training_params.epochs > 50) {
      errors.push('训练轮数必须在 1-50 之间')
    }
    
    if (config.training_params.batch_size < 1 || config.training_params.batch_size > 32) {
      errors.push('批次大小必须在 1-32 之间')
    }
    
    if (config.training_params.learning_rate <= 0 || config.training_params.learning_rate >= 1) {
      errors.push('学习率必须在 0-1 之间')
    }
    
    if (config.training_params.lora_r < 4 || config.training_params.lora_r > 128) {
      errors.push('LoRA Rank 必须在 4-128 之间')
    }
    
    return errors
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const validationErrors = validateConfig()
    if (validationErrors.length > 0) {
      setError(validationErrors.join('; '))
      return
    }
    
    if (!uploadedFile) {
      setError('请先上传训练数据文件')
      return
    }
    
    setIsSubmitting(true)
    setError('')
    setSuccess('')
    
    try {
      const job = await apiService.createTrainingJob(config as TrainingJobCreate, uploadedFile.file_path)
      setSuccess(`训练任务 "${job.job_name}" 创建成功！任务 ID: ${job.id}`)
      
      // 重置表单
      setConfig(prev => ({
        ...prev,
        job_name: ''
      }))
      
    } catch (error) {
      setError(error instanceof Error ? error.message : '创建训练任务失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getModelDescription = (modelName: string) => {
    return supportedModels?.model_info[modelName]?.description || modelName
  }

  const getEstimatedTime = () => {
    // 简单的时间估算
    const baseTime = 5 // 分钟
    const epochs = config.training_params.epochs
    const batchSize = config.training_params.batch_size
    
    const estimated = (baseTime * epochs) / (batchSize / 4)
    
    if (estimated < 60) {
      return `约 ${Math.round(estimated)} 分钟`
    } else {
      return `约 ${Math.round(estimated / 60)} 小时`
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">训练配置</h1>
        <p className="mt-2 text-sm text-gray-600">
          配置模型训练参数，开始 AI 模型微调任务
        </p>
      </div>

      {/* 上传文件信息 */}
      {uploadedFile && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="h-6 w-6 text-blue-600" />
            <div>
              <p className="font-medium text-blue-900">已选择训练数据</p>
              <p className="text-sm text-blue-700">{uploadedFile.filename}</p>
            </div>
          </div>
        </div>
      )}

      {/* 训练配置表单 */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基础配置 */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <CogIcon className="h-5 w-5 mr-2" />
            基础配置
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="form-label">任务名称 *</label>
              <input
                type="text"
                value={config.job_name}
                onChange={(e) => handleInputChange('job_name', e.target.value)}
                className="form-input"
                placeholder="输入训练任务名称"
                required
              />
            </div>
            
            <div>
              <label className="form-label">模型选择 *</label>
              <select
                value={config.training_params.model_name}
                onChange={(e) => handleInputChange('training_params.model_name', e.target.value)}
                className="form-input"
                required
              >
                {supportedModels?.supported_models.map(model => (
                  <option key={model} value={model}>
                    {getModelDescription(model)}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                选择用于微调的基础模型
              </p>
            </div>
          </div>
        </div>

        {/* 训练参数 */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">训练参数</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="form-label">训练轮数 (Epochs)</label>
              <input
                type="number"
                min="1"
                max="50"
                value={config.training_params.epochs}
                onChange={(e) => handleInputChange('training_params.epochs', parseInt(e.target.value))}
                className="form-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                模型训练的轮数，通常 2-5 轮
              </p>
            </div>
            
            <div>
              <label className="form-label">批次大小 (Batch Size)</label>
              <select
                value={config.training_params.batch_size}
                onChange={(e) => handleInputChange('training_params.batch_size', parseInt(e.target.value))}
                className="form-input"
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={4}>4</option>
                <option value={8}>8</option>
                <option value={16}>16</option>
                <option value={32}>32</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                每次训练处理的样本数量
              </p>
            </div>
            
            <div>
              <label className="form-label">学习率 (Learning Rate)</label>
              <select
                value={config.training_params.learning_rate}
                onChange={(e) => handleInputChange('training_params.learning_rate', parseFloat(e.target.value))}
                className="form-input"
              >
                <option value={0.00005}>5e-5 (保守)</option>
                <option value={0.0001}>1e-4 (标准)</option>
                <option value={0.0002}>2e-4 (推荐)</option>
                <option value={0.0005}>5e-4 (激进)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                控制模型学习速度
              </p>
            </div>
          </div>
        </div>

        {/* 优化选项 */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">优化选项</h3>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="use_fp16"
                checked={config.training_params.use_fp16}
                onChange={(e) => handleInputChange('training_params.use_fp16', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="use_fp16" className="text-sm font-medium text-gray-700">
                使用 FP16 混合精度训练
              </label>
              <InformationCircleIcon className="h-4 w-4 text-gray-400" title="节省显存，加速训练，但可能影响数值稳定性" />
            </div>
            
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="use_quantization"
                checked={config.training_params.use_quantization}
                onChange={(e) => handleInputChange('training_params.use_quantization', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="use_quantization" className="text-sm font-medium text-gray-700">
                使用 4-bit 量化
              </label>
              <InformationCircleIcon className="h-4 w-4 text-gray-400" title="大幅减少显存占用，但可能影响训练效果" />
            </div>
          </div>
        </div>

        {/* 高级 LoRA 配置 */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">LoRA 配置</h3>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              {showAdvanced ? '隐藏高级选项' : '显示高级选项'}
            </button>
          </div>
          
          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="form-label">LoRA Rank (r)</label>
                <input
                  type="number"
                  min="4"
                  max="128"
                  value={config.training_params.lora_r}
                  onChange={(e) => handleInputChange('training_params.lora_r', parseInt(e.target.value))}
                  className="form-input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  LoRA 矩阵的秩，影响参数效率
                </p>
              </div>
              
              <div>
                <label className="form-label">LoRA Alpha</label>
                <input
                  type="number"
                  min="8"
                  max="256"
                  value={config.training_params.lora_alpha}
                  onChange={(e) => handleInputChange('training_params.lora_alpha', parseInt(e.target.value))}
                  className="form-input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  LoRA 缩放参数，通常是 rank 的 2 倍
                </p>
              </div>
              
              <div>
                <label className="form-label">LoRA Dropout</label>
                <input
                  type="number"
                  min="0"
                  max="0.5"
                  step="0.1"
                  value={config.training_params.lora_dropout}
                  onChange={(e) => handleInputChange('training_params.lora_dropout', parseFloat(e.target.value))}
                  className="form-input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  防止过拟合的 dropout 率
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 训练预估 */}
        <div className="card bg-gray-50">
          <h3 className="text-lg font-medium text-gray-900 mb-3">训练预估</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">预估时间:</span>
              <span className="ml-2 text-gray-600">{getEstimatedTime()}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">显存需求:</span>
              <span className="ml-2 text-gray-600">
                {config.training_params.use_quantization ? '~4GB' : '~8GB'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">可训练参数:</span>
              <span className="ml-2 text-gray-600">
                ~{(config.training_params.lora_r * 4 / 1000).toFixed(1)}M
              </span>
            </div>
          </div>
        </div>

        {/* 错误和成功消息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mr-2" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}
        
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-green-800">{success}</span>
            </div>
          </div>
        )}

        {/* 提交按钮 */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="btn-secondary"
          >
            返回
          </button>
          
          <button
            type="submit"
            disabled={isSubmitting || !uploadedFile}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                创建中...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                开始训练
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default TrainingConfig
