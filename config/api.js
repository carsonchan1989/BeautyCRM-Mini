/**
 * API配置文件
 * 集中管理所有API接口地址
 */

// 检测运行环境
const isDevTools = function() {
  const systemInfo = wx.getSystemInfoSync();
  return systemInfo.platform === 'devtools';
};

// 配置不同环境的API基础URL
const config = {
  // 开发环境使用IP地址，确保手机也能访问
  baseUrl: '1.12.60.202:5000'  // 直接使用IP地址
};

// 获取基础URL，确保带有http前缀
const getBaseUrl = () => {
  let baseUrl = config.baseUrl;
  
  // 确保URL有http/https前缀
  if (!baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
    baseUrl = 'http://' + baseUrl;
  }
  
  return baseUrl;
};

module.exports = {
  // 获取基础URL
  getBaseUrl,
  
  // 构建API URL
  getUrl: function(path) {
    const base = getBaseUrl();
    const cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return `${base}/${cleanPath}`;
  },

  // API路径
  paths: {
    // 健康检查
    health: '/api/health',

    // 客户相关API
    customer: {
      base: '/api/customers',
      list: '/api/customers',
      detail: (id) => `/api/customers/${id}`,
      create: '/api/customers',
      update: (id) => `/api/customers/${id}`,
      delete: (id) => `/api/customers/${id}`,
      stats: '/api/customers/stats',

      // 客户关联记录
      health: (id) => `/api/customers/${id}/health`,
      consumption: (id) => `/api/customers/${id}/consumption`,
      service: (id) => `/api/customers/${id}/service`,
      communication: (id) => `/api/customers/${id}/communication`,
    },

    // 服务记录相关API
    service: {
      list: '/api/service/list',
      detail: (id) => `/api/service/${id}`,
      create: '/api/service/create',
      update: (id) => `/api/service/${id}`,
      delete: (id) => `/api/service/${id}`,
    },

    // 沟通记录相关API
    communication: {
      detail: (id) => `/api/customers/communications/${id}`,
      delete: (id) => `/api/customers/communications/${id}`,
    },

    // 项目库相关API
    project: {
      list: '/api/projects',
      detail: (id) => `/api/projects/${id}`,
      create: '/api/projects',
      update: (id) => `/api/projects/${id}`,
      delete: (id) => `/api/projects/${id}`,
      categories: '/api/projects/categories',
      stats: '/api/projects/stats',
      import: '/api/projects/import/excel',
      confirm: '/api/projects/import/confirm'
    },

    // Excel处理相关API
    excel: {
      preCheck: '/api/excel/import',
      import: '/api/excel/import',
      export: '/api/excel/export',
    }
  }
};