import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: string
  className?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  color = 'text-blue-600',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-current ${sizeClasses[size]} ${color} ${className}`} />
  )
}

interface LoadingDotsProps {
  size?: 'sm' | 'md' | 'lg'
  color?: string
  className?: string
}

export const LoadingDots: React.FC<LoadingDotsProps> = ({ 
  size = 'md',
  color = 'bg-blue-600',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-1 h-1',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  }

  return (
    <div className={`flex space-x-1 ${className}`}>
      <div className={`${sizeClasses[size]} ${color} rounded-full animate-pulse`} style={{ animationDelay: '0ms' }} />
      <div className={`${sizeClasses[size]} ${color} rounded-full animate-pulse`} style={{ animationDelay: '150ms' }} />
      <div className={`${sizeClasses[size]} ${color} rounded-full animate-pulse`} style={{ animationDelay: '300ms' }} />
    </div>
  )
}

interface LoadingOverlayProps {
  show: boolean
  message?: string
  children?: React.ReactNode
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  show, 
  message = '加载中...',
  children 
}) => {
  if (!show) return <>{children}</>

  return (
    <div className="relative">
      {children}
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div className="flex flex-col items-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-gray-600 text-sm">{message}</p>
        </div>
      </div>
    </div>
  )
}

interface SkeletonProps {
  className?: string
  rows?: number
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '',
  rows = 1 
}) => {
  if (rows === 1) {
    return (
      <div className={`animate-pulse bg-gray-300 rounded ${className}`} />
    )
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div 
          key={index}
          className={`animate-pulse bg-gray-300 rounded h-4 ${className}`}
          style={{ width: `${Math.random() * 40 + 60}%` }}
        />
      ))}
    </div>
  )
}

interface ProgressBarProps {
  progress: number
  size?: 'sm' | 'md' | 'lg'
  color?: string
  backgroundColor?: string
  showPercentage?: boolean
  className?: string
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  size = 'md',
  color = 'bg-blue-600',
  backgroundColor = 'bg-gray-200',
  showPercentage = false,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const clampedProgress = Math.max(0, Math.min(100, progress))

  return (
    <div className={`relative ${className}`}>
      <div className={`w-full ${backgroundColor} rounded-full ${sizeClasses[size]}`}>
        <div 
          className={`${color} ${sizeClasses[size]} rounded-full transition-all duration-300 ease-in-out`}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
      {showPercentage && (
        <div className="flex justify-between text-xs text-gray-600 mt-1">
          <span>{clampedProgress.toFixed(1)}%</span>
        </div>
      )}
    </div>
  )
}

interface PageLoadingProps {
  message?: string
}

export const PageLoading: React.FC<PageLoadingProps> = ({ 
  message = '页面加载中...' 
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <LoadingSpinner size="xl" className="mx-auto mb-4" />
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  )
}

interface CardSkeletonProps {
  rows?: number
  className?: string
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ 
  rows = 3,
  className = ''
}) => {
  return (
    <div className={`bg-white rounded-lg shadow-md border border-gray-200 p-6 ${className}`}>
      <Skeleton className="h-6 w-3/4 mb-4" />
      <Skeleton rows={rows} />
    </div>
  )
}

interface TableSkeletonProps {
  rows?: number
  columns?: number
  className?: string
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({ 
  rows = 5,
  columns = 4,
  className = ''
}) => {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            {Array.from({ length: columns }).map((_, index) => (
              <th key={index} className="px-6 py-3">
                <Skeleton className="h-4" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="px-6 py-4">
                  <Skeleton className="h-4" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default {
  LoadingSpinner,
  LoadingDots,
  LoadingOverlay,
  Skeleton,
  ProgressBar,
  PageLoading,
  CardSkeleton,
  TableSkeleton
}
