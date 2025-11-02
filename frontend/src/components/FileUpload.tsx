import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { apiService } from '../services/api'
import { FileUploadResponse } from '../types'

interface UploadedFile {
  file: File
  preview?: FileUploadResponse
  uploading: boolean
  error?: string
}

function FileUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setDragActive(false)
    
    const newFiles = acceptedFiles.map(file => ({
      file,
      uploading: true
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // 上传文件
    acceptedFiles.forEach((file, index) => {
      uploadFile(file, uploadedFiles.length + index)
    })
  }, [uploadedFiles.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
    accept: {
      'application/zip': ['.zip'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false
  })

  const uploadFile = async (file: File, index: number) => {
    try {
      const response = await apiService.uploadFile(file)
      
      setUploadedFiles(prev => 
        prev.map((item, i) => 
          i === index 
            ? { ...item, uploading: false, preview: response }
            : item
        )
      )
    } catch (error) {
      console.error('上传失败:', error)
      setUploadedFiles(prev => 
        prev.map((item, i) => 
          i === index 
            ? { ...item, uploading: false, error: '上传失败' }
            : item
        )
      )
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">文件上传</h1>
        <p className="mt-2 text-sm text-gray-600">
          上传包含作业和评分数据的文件，支持 ZIP、CSV、XLSX 格式
        </p>
      </div>

      {/* 支持格式说明 */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">支持的文件格式</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900">ZIP 压缩包</h4>
            <p className="text-sm text-gray-600 mt-1">
              包含作业文件和评分 CSV 的压缩包
            </p>
            <ul className="text-xs text-gray-500 mt-2 space-y-1">
              <li>• 必须包含至少一个 CSV 文件</li>
              <li>• CSV 需要包含: student_id, assignment, score 列</li>
              <li>• 可包含作业文件 (.txt, .md, .pdf, .docx)</li>
            </ul>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900">CSV 文件</h4>
            <p className="text-sm text-gray-600 mt-1">
              逗号分隔值文件
            </p>
            <ul className="text-xs text-gray-500 mt-2 space-y-1">
              <li>• 建议包含: student_id, assignment, score 列</li>
              <li>• 使用 UTF-8 编码</li>
            </ul>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900">XLSX 文件</h4>
            <p className="text-sm text-gray-600 mt-1">
              Excel 电子表格
            </p>
            <ul className="text-xs text-gray-500 mt-2 space-y-1">
              <li>• 建议包含: student_id, assignment, score 列</li>
              <li>• 使用第一个工作表</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 文件上传区域 */}
      <div className="card">
        <div
          {...getRootProps()}
          className={`upload-zone ${isDragActive || dragActive ? 'dragover' : ''} 
                     rounded-lg p-8 text-center cursor-pointer transition-colors duration-200`}
        >
          <input {...getInputProps()} />
          
          <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          
          {isDragActive ? (
            <p className="text-blue-600 font-medium">释放文件以上传</p>
          ) : (
            <div>
              <p className="text-gray-600 font-medium mb-2">
                拖拽文件到此处，或 <span className="text-blue-600">点击选择文件</span>
              </p>
              <p className="text-sm text-gray-500">
                支持 ZIP、CSV、XLSX 格式，最大 100MB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 已上传文件列表 */}
      {uploadedFiles.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">已上传文件</h3>
          
          <div className="space-y-4">
            {uploadedFiles.map((item, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <DocumentIcon className="h-8 w-8 text-gray-400 flex-shrink-0 mt-1" />
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(item.file.size)}
                      </p>
                      
                      {/* 上传状态 */}
                      <div className="mt-2">
                        {item.uploading && (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            <span className="text-sm text-blue-600">上传中...</span>
                          </div>
                        )}
                        
                        {item.error && (
                          <div className="flex items-center space-x-2">
                            <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                            <span className="text-sm text-red-600">{item.error}</span>
                          </div>
                        )}
                        
                        {item.preview && (
                          <div className="flex items-center space-x-2">
                            <CheckCircleIcon className="h-4 w-4 text-green-600" />
                            <span className="text-sm text-green-600">上传成功</span>
                          </div>
                        )}
                      </div>
                      
                      {/* 数据预览 */}
                      {item.preview?.data_preview && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <h4 className="text-sm font-medium text-gray-900 mb-2">数据预览</h4>
                          <div className="text-xs text-gray-600 space-y-1">
                            {item.preview.data_preview.total_records && (
                              <p>总记录数: {item.preview.data_preview.total_records}</p>
                            )}
                            {item.preview.data_preview.students && (
                              <p>学生数: {item.preview.data_preview.students}</p>
                            )}
                            {item.preview.data_preview.assignments && (
                              <p>作业数: {item.preview.data_preview.assignments}</p>
                            )}
                            {item.preview.data_preview.score_range && (
                              <p>
                                分数范围: {item.preview.data_preview.score_range.min} - {item.preview.data_preview.score_range.max}
                                (平均: {item.preview.data_preview.score_range.mean?.toFixed(1)})
                              </p>
                            )}
                          </div>
                          
                          {/* 示例数据 */}
                          {item.preview.data_preview.sample_data && (
                            <div className="mt-3">
                              <p className="text-xs font-medium text-gray-700 mb-2">示例数据:</p>
                              <div className="overflow-x-auto">
                                <table className="min-w-full text-xs">
                                  <thead>
                                    <tr className="bg-gray-100">
                                      {item.preview.data_preview.column_names?.slice(0, 5).map((col, i) => (
                                        <th key={i} className="px-2 py-1 text-left font-medium text-gray-700">
                                          {col}
                                        </th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {item.preview.data_preview.sample_data.slice(0, 3).map((row, i) => (
                                      <tr key={i} className="border-b border-gray-200">
                                        {Object.values(row).slice(0, 5).map((value, j) => (
                                          <td key={j} className="px-2 py-1 text-gray-600">
                                            {String(value).substring(0, 20)}
                                            {String(value).length > 20 ? '...' : ''}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => removeFile(index)}
                    className="ml-4 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {/* 操作按钮 */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => setUploadedFiles([])}
              className="btn-secondary"
            >
              清空列表
            </button>
            
            {uploadedFiles.some(item => item.preview) && (
              <button
                onClick={() => {
                  // 跳转到训练配置页面，传递文件信息
                  const successFiles = uploadedFiles.filter(item => item.preview)
                  if (successFiles.length > 0) {
                    // 这里可以使用 router 跳转并传递数据
                    console.log('准备配置训练:', successFiles)
                  }
                }}
                className="btn-primary"
              >
                配置训练
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
