// index.js
const Logger = require('../../utils/logger')
const apiConfig = require('../../config/api')

// 确保Page调用是正确的
Page({
  data: {
    // 功能模块
    modules: [
      {
        id: 'upload',
        name: '档案导入',
        icon: 'cloud-upload',
        color: '#10aeff',
        url: '/pages/upload/upload'
      },
      {
        id: 'customer',
        name: '客户管理',
        icon: 'user',
        color: '#07c160',
        url: '/pages/customer/list'
      },
      {
        id: 'report',
        name: '智能分析',
        icon: 'chart',
        color: '#ff9500',
        url: '/pages/report/report'
      },
      {
        id: 'history',
        name: '历史报告',
        icon: 'file',
        color: '#8a2be2',
        url: '/pages/history/history'
      }
    ],
    
    // 快捷操作
    quickActions: [
      {
        name: '新增客户',
        icon: 'user-add',
        url: '/pages/customer/add'
      },
      {
        name: 'Excel导入',
        icon: 'excel',
        url: '/pages/excel/import'
      },
      {
        name: '生成报告',
        icon: 'ai',
        url: '/pages/report/create'
      }
    ],
    
    // 统计数据
    stats: {
      customerCount: 0,
      reportCount: 0,
      lastUpdateTime: ''
    },
    
    // 用户信息
    userInfo: null,
    hasUserInfo: false,
    canIUseGetUserProfile: false,
    
    // 系统信息
    systemInfo: null,

    customerCount: 0,
    projectCount: 0,
    lastUpdate: '',
    version: '1.0.0'
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('首页加载');
    
    // 检查是否可以使用getUserProfile
    if (wx.getUserProfile) {
      this.setData({
        canIUseGetUserProfile: true
      });
    }
    
    // 获取系统信息
    try {
      const systemInfo = wx.getSystemInfoSync();
      this.setData({ systemInfo });
    } catch (e) {
      this.logger.error('获取系统信息失败', e);
    }

    this.loadStatistics();
  },
  
  onShow() {
    this.loadStatistics();
  },
  
  loadStatistics() {
    const self = this;
    wx.showLoading({
      title: '加载中...',
    });

    // 调用API获取统计数据
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.stats),
      method: 'GET',
      success: function(res) {
        self.logger.info('统计数据返回:', res.data);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          self.logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            self.logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                self.logger.info(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode === 200) {
                  // 处理重定向后的成功响应
                  self.processStatisticsData(redirectRes.data);
                } else {
                  self.logger.error('重定向请求失败', { 
                    statusCode: redirectRes.statusCode,
                    data: redirectRes.data 
                  });
                }
              },
              fail: (redirectErr) => {
                self.logger.error('重定向请求错误', redirectErr);
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        // 处理不同格式的返回数据
        if(res.statusCode === 200) {
          self.processStatisticsData(res.data);
        } else {
          self.logger.error('获取统计数据失败，状态码:', res.statusCode);
        }
      },
      fail: function(err) {
        self.logger.error('统计数据请求失败:', err);
      },
      complete: function() {
        wx.hideLoading();
      }
    });
  },
  
  // 处理统计数据
  processStatisticsData(data) {
    if(data && data.success && data.data) {
      // 返回格式为 {success: true, data: {...}}
      this.setData({
        customerCount: data.data.total_customers || 0,
        projectCount: data.data.project_count || 0,
        lastUpdate: this.formatDate(new Date())
      });
    } else if(data && data.items) {
      // 返回格式为 {items: [...], total: 3}
      this.setData({
        customerCount: data.total || 0,
        projectCount: 0, // 项目数据可能需要单独请求
        lastUpdate: this.formatDate(new Date())
      });
    } else if(data && typeof data === 'object') {
      // 返回直接就是数据对象
      this.setData({
        customerCount: data.total_customers || data.customer_count || 0,
        projectCount: data.project_count || 0,
        lastUpdate: this.formatDate(new Date())
      });
    }
  },
  
  // 格式化日期
  formatDate(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
  },
  
  // 获取用户信息
  getUserProfile() {
    // 推荐使用 wx.getUserProfile 获取用户信息，开发者每次通过该接口获取用户个人信息均需用户确认
    wx.getUserProfile({
      desc: '用于完善用户资料', 
      success: (res) => {
        this.setData({
          userInfo: res.userInfo,
          hasUserInfo: true
        });
      }
    });
  },
  
  // 跳转到指定页面
  navigateTo(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return;
    
    wx.navigateTo({
      url: url
    });
  },
  
  // 刷新统计数据
  refreshStats() {
    this.loadStatistics();
  },

  // 导航到客户管理页面
  navigateToCustomer() {
    wx.navigateTo({
      url: '/pages/customer/list'
    });
  },

  // 导航到项目管理页面
  navigateToProject() {
    wx.navigateTo({
      url: '/pages/project/list'
    });
  },

  // 点击客户数量统计
  onCustomerStatsTap() {
    this.navigateToCustomer();
  },

  // 点击项目数量统计
  onProjectStatsTap() {
    this.navigateToProject();
  },

  // 导航到项目管理
  navigateToProjectManagement() {
    wx.navigateTo({
      url: '/pages/project/list'
    });
  },

  // 导航到Excel导入
  navigateToExcelImport() {
    wx.navigateTo({
      url: '/pages/excel/import'
    });
  },

  // 导航到智能分析
  navigateToAnalysis() {
    wx.navigateTo({
      url: '/pages/report/report'
    });
  },

  // 导航到历史报告
  navigateToHistory() {
    wx.navigateTo({
      url: '/pages/history/history'
    });
  },

  // 导航到添加客户
  navigateToAddCustomer() {
    wx.navigateTo({
      url: '/pages/customer/add'
    });
  },

  // 导航到创建报告
  navigateToCreateReport() {
    wx.navigateTo({
      url: '/pages/report/create'
    });
  },

  // 导航到客户列表
  navigateToCustomerList() {
    wx.navigateTo({
      url: '/pages/customer/list'
    });
  }
})