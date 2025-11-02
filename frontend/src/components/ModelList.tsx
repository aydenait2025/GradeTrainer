import React, { useState, useEffect } from 'react'
import { 
  CubeIcon, 
  CloudArrowDownIcon, 
  PlayIcon,
  StopIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { apiService, downloadFile, formatFileSize } from '../services/api'
import { ModelInfo, PredictionResponse } from '../types'

function ModelList() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null)
  const [showPredictionModal, setShowPredictionModal] = useState(false)
  const [predictionInput, setPredictionInput] = useState('')
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null)
  const [predictionLoading, setPredictionLoading] = useState(false)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const data = await apiService.getModels()
      setModels(data)
    } catch (error) {
      console.error('获取模型列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (model: ModelInfo) => {
    try {
      const blob = await apiService.downloadModel(model.id)
      downloadFile(blob, `model_${model.id}_${model.model_name.replace('/', '_')}.zip`)
    } catch (error) {
      console.error('下载模型失败:', error)
    }
  }

  const handleDeploy = async (model: ModelInfo) => {
    try {
      await apiService.deployModel(model.id)
      fetchModels() // 刷新列表
    } catch (error) {
      console.error('部署模型失败:', error)
    }
  }

  const handleUndeploy = async (model: ModelInfo) => {
    try {
      await apiService.undeployModel(model.id)
      fetchModels() // 刷新列表
    } catch (error) {
      console.error('取消部署失败:', error)
    }
  }

  const handleDelete = async (model: ModelInfo) => {
    if (!confirm(`确定要删除模型 "${model.model_name}" 吗？此操作不可恢复。`)) {
      return
    }
    
    try {
      await apiService.deleteModel(model.id)
      fetchModels() // 刷新列表
    } catch (error) {
      console.error('删除模型失败:', error)
    }
  }

  const handlePredict = async () => {
    if (!selectedModel || !predictionInput.trim()) return
    
    setPredictionLoading(true)
    setPredictionResult(null)
    
    try {
      const result = await apiService.predictWithModel(selectedModel.id, predictionInput)
      setPredictionResult(result)
    } catch (error) {
      console.error('预测失败:', error)
    } finally {
      setPredictionLoading(false)
    }
  }

  const PredictionModal = () => (
    showPredictionModal && selectedModel && (
      <div className="modal-overlay" onClick={() => setShowPredictionModal(false)}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            模型预测 - {selectedModel.model_name}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="form-label">输入文本</label>
              <textarea
                value={predictionInput}
                onChange={(e) => setPredictionInput(e.target.value)}
                className="form-input h-32"
                placeholder="输入要预测的文本..."
              />
            </div>
            
            {predictionResult && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">预测结果</h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">生成文本:</span>
                    <p className="mt-1 text-gray-600 whitespace-pre-wrap">
                      {predictionResult.generated_text}
                    </p>
                  </div>
                  <div className="flex space-x-4">
                    <span>
                      <span className="font-medium text-gray-700">处理时间:</span>
                      <span className="ml-1 text-gray-600">
                        {predictionResult.processing_time.toFixed(2)}s
                      </span>
                    </span>
                    {predictionResult.confidence && (
                      <span>
                        <span className="font-medium text-gray-700">置信度:</span>
                        <span className="ml-1 text-gray-600">
                          {(predictionResult.confidence * 100).toFixed(1)}%
                        </span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => setShowPredictionModal(false)}
              className="btn-secondary"
            >
              关闭
            </button>
            
            <button
              onClick={handlePredict}
              disabled={predictionLoading || !predictionInput.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {predictionLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  预测中...
                </>
              ) : (
                '开始预测'
              )}
            </button>
          </div>
        </div>
      </div>
    )
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-dots">
          <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-1"></span>
          <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-1"></span>
          <span className="inline-block w-2 h-2 bg-blue-600 rounded-full"></span>
        </div>
        <span className="ml-2 text-gray-600">加载中...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">模型管理</h1>
        <p className="mt-2 text-sm text-gray-600">
          管理已训练的模型，支持部署、下载和预测功能
        </p>
      </div>

      {/* 模型统计 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
              <CubeIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">总模型数</p>
              <p className="text-2xl font-semibold text-gray-900">{models.length}</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
              <CheckCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">已部署</p>
              <p className="text-2xl font-semibold text-gray-900">
                {models.filter(m => m.is_deployed).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-3 rounded-lg bg-gray-500">
              <XCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">未部署</p>
              <p className="text-2xl font-semibold text-gray-900">
                {models.filter(m => !m.is_deployed).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 模型列表 */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">模型列表</h3>
          <button
            onClick={fetchModels}
            className="btn-secondary"
          >
            刷新
          </button>
        </div>

        {models.length === 0 ? (
          <div className="text-center py-8">
            <CubeIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">暂无已训练的模型</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-300">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header-cell">模型名称</th>
                  <th className="table-header-cell">大小</th>
                  <th className="table-header-cell">状态</th>
                  <th className="table-header-cell">创建时间</th>
                  <th className="table-header-cell">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {models.map((model) => (
                  <tr key={model.id} className="hover:bg-gray-50">
                    <td className="table-cell">
                      <div>
                        <p className="font-medium text-gray-900">
                          {model.model_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          ID: {model.id} | Job: {model.job_id}
                        </p>
                      </div>
                    </td>
                    
                    <td className="table-cell">
                      {model.model_size 
                        ? formatFileSize(model.model_size * 1024 * 1024)
                        : 'N/A'
                      }
                    </td>
                    
                    <td className="table-cell">
                      <div className="flex items-center space-x-2">
                        {model.is_deployed ? (
                          <>
                            <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                            <span className="text-sm text-green-700">已部署</span>
                          </>
                        ) : (
                          <>
                            <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                            <span className="text-sm text-gray-500">未部署</span>
                          </>
                        )}
                      </div>
                      {model.api_endpoint && (
                        <p className="text-xs text-gray-500 mt-1">
                          {model.api_endpoint}
                        </p>
                      )}
                    </td>
                    
                    <td className="table-cell">
                      <div className="text-sm text-gray-900">
                        {new Date(model.created_at).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(model.created_at).toLocaleTimeString()}
                      </div>
                    </td>
                    
                    <td className="table-cell">
                      <div className="flex items-center space-x-2">
                        {/* 下载按钮 */}
                        <button
                          onClick={() => handleDownload(model)}
                          className="text-blue-600 hover:text-blue-500"
                          title="下载模型"
                        >
                          <CloudArrowDownIcon className="h-4 w-4" />
                        </button>
                        
                        {/* 部署/取消部署按钮 */}
                        {model.is_deployed ? (
                          <button
                            onClick={() => handleUndeploy(model)}
                            className="text-red-600 hover:text-red-500"
                            title="取消部署"
                          >
                            <StopIcon className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleDeploy(model)}
                            className="text-green-600 hover:text-green-500"
                            title="部署模型"
                          >
                            <PlayIcon className="h-4 w-4" />
                          </button>
                        )}
                        
                        {/* 预测按钮 */}
                        {model.is_deployed && (
                          <button
                            onClick={() => {
                              setSelectedModel(model)
                              setShowPredictionModal(true)
                              setPredictionInput('')
                              setPredictionResult(null)
                            }}
                            className="text-purple-600 hover:text-purple-500"
                            title="测试预测"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                        )}
                        
                        {/* 删除按钮 */}
                        <button
                          onClick={() => handleDelete(model)}
                          className="text-red-600 hover:text-red-500"
                          title="删除模型"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 使用说明 */}
      <div className="card bg-blue-50 border-blue-200">
        <div className="flex items-start space-x-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900">模型操作说明</h4>
            <div className="mt-2 text-sm text-blue-800 space-y-1">
              <p>• <strong>下载</strong>: 下载训练好的模型文件，包含模型权重和配置</p>
              <p>• <strong>部署</strong>: 将模型部署为 REST API 服务，可用于在线预测</p>
              <p>• <strong>预测</strong>: 使用已部署的模型进行文本生成或分类预测</p>
              <p>• <strong>删除</strong>: 永久删除模型文件和相关记录，操作不可恢复</p>
            </div>
          </div>
        </div>
      </div>

      {/* 预测模态框 */}
      <PredictionModal />
    </div>
  )
}

export default ModelList
