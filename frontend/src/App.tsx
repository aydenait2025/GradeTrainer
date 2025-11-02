import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  CloudArrowUpIcon, 
  CogIcon, 
  ChartBarIcon,
  CubeIcon
} from '@heroicons/react/24/outline'

// Import components
import Dashboard from './components/Dashboard'
import FileUpload from './components/FileUpload'
import TrainingConfig from './components/TrainingConfig'
import TrainingProgress from './components/TrainingProgress'
import ModelList from './components/ModelList'
import { NotificationProvider } from './components/Notification'

function Navigation() {
  const location = useLocation()
  
  const navigation = [
    { name: '仪表板', href: '/', icon: HomeIcon },
    { name: '文件上传', href: '/upload', icon: CloudArrowUpIcon },
    { name: '训练配置', href: '/training', icon: CogIcon },
    { name: '训练进度', href: '/progress', icon: ChartBarIcon },
    { name: '模型管理', href: '/models', icon: CubeIcon },
  ]

  return (
    <nav className="bg-gray-800">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-white font-bold text-xl">AI 模型微调系统</h1>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`${
                        isActive
                          ? 'bg-gray-900 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      } flex items-center px-3 py-2 rounded-md text-sm font-medium`}
                    >
                      <item.icon className="h-5 w-5 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <NotificationProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          
          <main className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<FileUpload />} />
                <Route path="/training" element={<TrainingConfig />} />
                <Route path="/progress" element={<TrainingProgress />} />
                <Route path="/models" element={<ModelList />} />
              </Routes>
            </div>
          </main>
        </div>
      </Router>
    </NotificationProvider>
  )
}

export default App
