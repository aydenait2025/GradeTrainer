import React, { useState, useEffect } from 'react'
import { 
  PlayIcon, 
  PauseIcon, 
  StopIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { apiService, getStatusColor, getStatusText } from '../services/api'
import { TrainingJob, TrainingProgress as Progress, TrainingLog } from '../types'

function TrainingProgress() {
  const [jobs, setJobs] = useState<TrainingJob[]>([])
  const [selectedJob, setSelectedJob] = useState<TrainingJob | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [logs, setLogs] = useState<TrainingLog[]>([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    fetchJobs()
    
    // 自动刷新
    let interval: NodeJS.Timeout
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchJobs()
        if (selectedJob) {
          fetchJobDetails(selectedJob.id)
        }
      }, 5000) // 每5秒刷新
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, selectedJob])

  const fetchJobs = async () => {
    try {
      const data = await apiService.getTrainingJobs(0, 50)
      setJobs(data)
      
      // 如果没有选中的任务，自动选择第一个运行中的任务
      if (!selectedJob && data.length > 0) {
        const runningJob = data.find(job => job.status === 'running') || data[0]
        setSelectedJob(runningJob)
        fetchJobDetails(runningJob.id)
      }
    } catch (error) {
      console.error('获取训练任务失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchJobDetails = async (jobId: number) => {
    try {
      const [progressData, logsData] = await Promise.all([
        apiService.getTrainingProgress(jobId),
        apiService.getTrainingLogs(jobId, 0, 100)
      ])
      
      setProgress(progressData)
      setLogs(logsData.reverse()) // 最新的日志在前
    } catch (error) {
      console.error('获取任务详情失败:', error)
    }
  }

  const handleJobAction = async (jobId: number, action: 'stop' | 'restart') => {
    try {
      if (action === 'stop') {
        await apiService.stopTrainingJob(jobId)
      } else if (action === 'restart') {
        await apiService.restartTrainingJob(jobId)
      }
      
      // 刷新任务列表
      fetchJobs()
    } catch (error) {
      console.error(`${action} 任务失败:`, error)
    }
  }

  const formatDuration = (seconds: number): string => {
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

  const getProgressPercentage = () => {
    if (!progress || progress.total_epochs === 0) return 0
    return Math.round((progress.current_epoch / progress.total_epochs) * 100)
  }

  const getStepProgressPercentage = () => {
    if (!progress || progress.total_steps === 0) return 0
    return Math.round((progress.current_step / progress.total_steps) * 100)
  }

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">训练进度</h1>
          <p className="mt-2 text-sm text-gray-600">
            实时监控模型训练进度和日志
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <label className="flex items-center text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
            />
            自动刷新
          </label>
          
          <button
            onClick={fetchJobs}
            className="btn-secondary flex items-center"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            刷新
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 任务列表 */}
        <div className="lg:col-span-1">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">训练任务</h3>
            
            {jobs.length === 0 ? (
              <div className="text-center py-8">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">暂无训练任务</p>
              </div>
            ) : (
              <div className="space-y-2">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    onClick={() => {
                      setSelectedJob(job)
                      fetchJobDetails(job.id)
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors duration-200 ${
                      selectedJob?.id === job.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {job.job_name}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {job.model_name}
                        </p>
                      </div>
                      
                      <div className="ml-2 flex-shrink-0">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                          {getStatusText(job.status)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500">
                      创建于 {new Date(job.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 训练详情 */}
        <div className="lg:col-span-2 space-y-6">
          {selectedJob ? (
            <>
              {/* 任务信息和控制 */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{selectedJob.job_name}</h3>
                    <p className="text-sm text-gray-600">{selectedJob.model_name}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedJob.status)}`}>
                      {getStatusText(selectedJob.status)}
                    </span>
                    
                    {selectedJob.status === 'running' && (
                      <button
                        onClick={() => handleJobAction(selectedJob.id, 'stop')}
                        className="btn-danger flex items-center"
                      >
                        <StopIcon className="h-4 w-4 mr-1" />
                        停止
                      </button>
                    )}
                    
                    {(selectedJob.status === 'failed' || selectedJob.status === 'stopped') && (
                      <button
                        onClick={() => handleJobAction(selectedJob.id, 'restart')}
                        className="btn-primary flex items-center"
                      >
                        <PlayIcon className="h-4 w-4 mr-1" />
                        重启
                      </button>
                    )}
                  </div>
                </div>

                {/* 训练参数 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">训练轮数:</span>
                    <span className="ml-1 text-gray-600">{selectedJob.epochs}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">批次大小:</span>
                    <span className="ml-1 text-gray-600">{selectedJob.batch_size}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">学习率:</span>
                    <span className="ml-1 text-gray-600">{selectedJob.learning_rate}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">LoRA Rank:</span>
                    <span className="ml-1 text-gray-600">{selectedJob.lora_r}</span>
                  </div>
                </div>
              </div>

              {/* 训练进度 */}
              {progress && selectedJob.status === 'running' && (
                <div className="card">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">训练进度</h4>
                  
                  <div className="space-y-4">
                    {/* Epoch 进度 */}
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          Epoch 进度: {progress.current_epoch}/{progress.total_epochs}
                        </span>
                        <span className="text-sm text-gray-500">
                          {getProgressPercentage()}%
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${getProgressPercentage()}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    {/* Step 进度 */}
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          Step 进度: {progress.current_step}/{progress.total_steps}
                        </span>
                        <span className="text-sm text-gray-500">
                          {getStepProgressPercentage()}%
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${getStepProgressPercentage()}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    {/* 训练指标 */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      {progress.current_loss && (
                        <div>
                          <span className="font-medium text-gray-700">当前损失:</span>
                          <span className="ml-1 text-gray-600">{progress.current_loss.toFixed(4)}</span>
                        </div>
                      )}
                      
                      {progress.learning_rate && (
                        <div>
                          <span className="font-medium text-gray-700">学习率:</span>
                          <span className="ml-1 text-gray-600">{progress.learning_rate.toExponential(2)}</span>
                        </div>
                      )}
                      
                      {progress.estimated_remaining && (
                        <div>
                          <span className="font-medium text-gray-700">预计剩余:</span>
                          <span className="ml-1 text-gray-600">{formatDuration(progress.estimated_remaining)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* 训练结果 */}
              {selectedJob.status === 'completed' && (
                <div className="card bg-green-50 border-green-200">
                  <div className="flex items-center mb-4">
                    <CheckCircleIcon className="h-6 w-6 text-green-600 mr-2" />
                    <h4 className="text-lg font-medium text-green-900">训练完成</h4>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    {selectedJob.final_loss && (
                      <div>
                        <span className="font-medium text-green-800">最终损失:</span>
                        <span className="ml-1 text-green-700">{selectedJob.final_loss.toFixed(4)}</span>
                      </div>
                    )}
                    
                    {selectedJob.validation_accuracy && (
                      <div>
                        <span className="font-medium text-green-800">验证准确率:</span>
                        <span className="ml-1 text-green-700">{(selectedJob.validation_accuracy * 100).toFixed(2)}%</span>
                      </div>
                    )}
                    
                    {selectedJob.completed_at && selectedJob.started_at && (
                      <div>
                        <span className="font-medium text-green-800">训练时长:</span>
                        <span className="ml-1 text-green-700">
                          {formatDuration(
                            (new Date(selectedJob.completed_at).getTime() - 
                             new Date(selectedJob.started_at).getTime()) / 1000
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 训练日志 */}
              <div className="card">
                <h4 className="text-lg font-medium text-gray-900 mb-4">训练日志</h4>
                
                <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
                  <div className="space-y-1 text-sm font-mono">
                    {logs.length === 0 ? (
                      <div className="text-gray-400">暂无日志...</div>
                    ) : (
                      logs.map((log) => (
                        <div
                          key={log.id}
                          className={`${
                            log.log_level === 'ERROR' ? 'text-red-400' :
                            log.log_level === 'WARNING' ? 'text-yellow-400' :
                            'text-green-400'
                          }`}
                        >
                          <span className="text-gray-500">
                            [{new Date(log.timestamp).toLocaleTimeString()}]
                          </span>
                          <span className="ml-2">[{log.log_level}]</span>
                          <span className="ml-2">{log.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <div className="text-center py-8">
                <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">请选择一个训练任务查看详情</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TrainingProgress
