/**
 * API配置文件
 * 集中管理所有API接口地址
 */

// 基础URL，从全局配置获取
const getBaseUrl = () => {
  const app = getApp();
  return (app && app.globalData && app.globalData.apiBaseUrl) || 'http://localhost:5000';
};

module.exports = {
  // 获取基础URL
  getBaseUrl,
  
  // 构建API URL
  getUrl: function(path) {
    return `${getBaseUrl()}${path}`;
  },

  // API路径
  paths: {
    // 健康检查
    health: '/health',

    // 客户相关API
    customer: {
      base: '/customers',
      list: '/customers',
      detail: (id) => `/customers/${id}`,
      create: '/customers',
      update: (id) => `/customers/${id}`,
      delete: (id) => `/customers/${id}`,
      stats: '/customers/stats',

      // 客户关联记录
      health: (id) => `/customers/${id}/health`,
      consumption: (id) => `/customers/${id}/consumption`,
      service: (id) => `/customers/${id}/service`,
      communication: (id) => `/customers/${id}/communication`,
    },

    // 服务记录相关API
    service: {
      list: '/services/list',
      detail: (id) => `/services/${id}`,
      create: '/services/create',
      update: (id) => `/services/${id}`,
      delete: (id) => `/services/${id}`,
    },

    // 沟通记录相关API
    communication: {
      detail: (id) => `/customers/communications/${id}`,
      delete: (id) => `/customers/communications/${id}`,
    },

    // Excel处理相关API
    excel: {
      preCheck: '/excel/import', // 预检查使用相同的URL，通过formData中的action参数区分
      import: '/excel/import',
      export: '/excel/export',
    }
  }
};