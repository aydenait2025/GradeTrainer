import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  ServerIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { apiService } from '../services/api'
import { SystemStatus, TrainingJob } from '../types'

interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  color: string
}

function StatsCard({ title, value, icon: Icon, color }: StatsCardProps) {
  return (
    <div className="card">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

function Dashboard() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [recentJobs, setRecentJobs] = useState<TrainingJob[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    // 每30秒刷新一次数据
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [statusData, jobsData] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getTrainingJobs(0, 5)
      ])
      setSystemStatus(statusData)
      setRecentJobs(jobsData)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
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

  const getStatusBadge = (status: string) => {
    const statusMap = {
      pending: 'status-pending',
      running: 'status-running',
      completed: 'status-completed',
      failed: 'status-failed'
    }
    return statusMap[status as keyof typeof statusMap] || 'status-pending'
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">系统仪表板</h1>
        <p className="mt-2 text-sm text-gray-600">
          监控训练任务状态和系统资源使用情况
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="总任务数"
          value={systemStatus?.total_jobs || 0}
          icon={ChartBarIcon}
          color="bg-blue-500"
        />
        <StatsCard
          title="运行中"
          value={systemStatus?.running_jobs || 0}
          icon={ClockIcon}
          color="bg-yellow-500"
        />
        <StatsCard
          title="已完成"
          value={systemStatus?.completed_jobs || 0}
          icon={CheckCircleIcon}
          color="bg-green-500"
        />
        <StatsCard
          title="失败任务"
          value={systemStatus?.failed_jobs || 0}
          icon={XCircleIcon}
          color="bg-red-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 系统资源 */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">系统资源</h3>
          
          {systemStatus?.gpu_usage?.available ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">GPU 使用率</span>
                  <span className="text-sm text-gray-500">
                    {systemStatus.gpu_usage.devices?.[0]?.utilization?.gpu_percent || 0}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ 
                      width: `${systemStatus.gpu_usage.devices?.[0]?.utilization?.gpu_percent || 0}%` 
                    }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">GPU 内存</span>
                  <span className="text-sm text-gray-500">
                    {systemStatus.gpu_usage.devices?.[0]?.memory?.usage_percent?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ 
                      width: `${systemStatus.gpu_usage.devices?.[0]?.memory?.usage_percent || 0}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <CpuChipIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">未检测到 GPU</p>
            </div>
          )}

          <div className="mt-6 space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">内存使用率</span>
                <span className="text-sm text-gray-500">
                  {systemStatus?.memory_usage?.usage_percent?.toFixed(1) || 0}%
                </span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${systemStatus?.memory_usage?.usage_percent || 0}%` 
                  }}
                ></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">磁盘使用率</span>
                <span className="text-sm text-gray-500">
                  {systemStatus?.disk_usage?.usage_percent?.toFixed(1) || 0}%
                </span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${systemStatus?.disk_usage?.usage_percent || 0}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* 最近任务 */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">最近任务</h3>
          
          {recentJobs.length > 0 ? (
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{job.job_name}</p>
                    <p className="text-xs text-gray-500">{job.model_name}</p>
                  </div>
                  <div className="text-right">
                    <span className={`${getStatusBadge(job.status)}`}>
                      {job.status === 'pending' && '等待中'}
                      {job.status === 'running' && '运行中'}
                      {job.status === 'completed' && '已完成'}
                      {job.status === 'failed' && '失败'}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <ServerIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">暂无训练任务</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
