// pages/report/report.js
const DataStore = require('../../utils/dataStore')
const Logger = require('../../utils/logger')
const ReportGenerator = require('../../utils/reportGenerator')
const apiConfig = require('../../config/api') // 添加API配置引用

Page({
  data: {
    // 客户列表
    customers: [],
    filteredCustomers: [],
    
    // 搜索关键字
    searchKeyword: '',
    
    // 加载状态
    isLoading: true,
    
    // 选中的客户
    selectedCustomerId: '',
    selectedCustomer: null,
    
    // 报告生成状态
    isGenerating: false,
    
    // 错误信息
    errorMessage: ''
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('报告页面已加载');
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ 
      logger: this.logger,
      // 配置大模型API
      apiKey: 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
      apiUrl: 'https://api.siliconflow.cn/v1',
      model: 'Pro/deepseek-ai/DeepSeek-R1'
    });
    
    // 加载客户数据
    this.loadCustomerData();
  },
  
  /**
   * 加载客户数据
   */
  loadCustomerData() {
    this.setData({ 
      isLoading: true,
      errorMessage: '' 
    });
    
    // 从服务器API获取客户数据，而不是从本地DataStore
    wx.showLoading({
      title: '加载客户数据...'
    });
    
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.list),
      method: 'GET',
      success: (res) => {
        this.logger.info(`客户数据响应: 状态码 ${res.statusCode}`);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          this.logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            this.logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                this.logger.info(`重定向请求响应: 状态码 ${redirectRes.statusCode}`);
                if (redirectRes.statusCode === 200) {
                  // 直接使用API返回的items数组作为客户列表
                  const customers = redirectRes.data.items || [];
                  
                  this.logger.info(`从重定向API加载了${customers.length}位客户数据`);
                  
                  this.setData({
                    customers: customers,
                    filteredCustomers: customers,
                    isLoading: false,
                    errorMessage: customers.length > 0 ? '' : '暂无客户数据'
                  });
                } else {
                  this.logger.error('重定向后加载客户数据失败', redirectRes.data);
                  this.setData({
                    isLoading: false,
                    errorMessage: '加载客户数据失败: ' + 
                      (redirectRes.data && redirectRes.data.message ? redirectRes.data.message : '重定向请求失败')
                  });
                }
              },
              fail: (redirectErr) => {
                this.logger.error('重定向请求错误:', redirectErr);
                this.setData({
                  isLoading: false,
                  errorMessage: '网络请求失败: 重定向错误'
                });
              },
              complete: () => {
                wx.hideLoading();
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        // 检查响应是否成功
        if (res.statusCode === 200) {
          // 直接使用API返回的items数组作为客户列表
          const customers = res.data.items || [];
          
          this.logger.info(`从API加载了${customers.length}位客户数据`);
          
          this.setData({
            customers: customers,
            filteredCustomers: customers,
            isLoading: false,
            errorMessage: customers.length > 0 ? '' : '暂无客户数据'
          });
        } else {
          this.logger.error('从API加载客户数据失败', res.data);
          this.setData({
            isLoading: false,
            errorMessage: '加载客户数据失败: ' + (res.data && res.data.message ? res.data.message : '未知错误')
          });
        }
      },
      fail: (err) => {
        this.logger.error('客户数据请求失败', err);
        this.setData({
          isLoading: false,
          errorMessage: '网络请求失败: ' + (err.errMsg || '未知错误')
        });
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },
  
  /**
   * 搜索客户
   */
  searchCustomers(e) {
    const keyword = e.detail.value;
    this.setData({ searchKeyword: keyword });
    
    if (!keyword) {
      this.setData({ filteredCustomers: this.data.customers });
      return;
    }
    
    // 按名称或手机号筛选
    const filteredCustomers = this.data.customers.filter(customer => {
      return (
        (customer.name && customer.name.toLowerCase().includes(keyword.toLowerCase())) ||
        (customer.phone && customer.phone.includes(keyword))
      );
    });
    
    this.setData({ filteredCustomers });
  },
  
  /**
   * 选择客户
   */
  selectCustomer(e) {
    const customerId = e.currentTarget.dataset.id;
    if (!customerId) return;
    
    // 查找选中的客户
    const selectedCustomer = this.data.customers.find(c => c.id === customerId);
    if (!selectedCustomer) {
      this.logger.warn('未找到选中的客户', { customerId });
      return;
    }
    
    this.logger.info('选中客户', { 
      customerId, 
      name: selectedCustomer.name 
    });
    
    // 获取客户消费记录
    this.loadCustomerConsumptions(customerId, selectedCustomer);
  },
  
  /**
   * 加载客户消费记录
   */
  loadCustomerConsumptions(customerId, selectedCustomer) {
    // 显示加载中状态
    wx.showLoading({
      title: '加载消费记录...',
      mask: true
    });
    
    // 从API获取客户消费记录
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.service.list) + `?customer_id=${customerId}`,
      method: 'GET',
      success: (res) => {
        this.logger.info(`消费记录响应: 状态码 ${res.statusCode}`);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          this.logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            this.logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                wx.hideLoading();
                this.logger.info(`重定向请求响应: 状态码 ${redirectRes.statusCode}`);
                if (redirectRes.statusCode === 200) {
                  // 直接使用返回的items数组作为消费记录
                  const consumptions = redirectRes.data.items || [];
                  
                  this.logger.info(`从重定向API加载了${consumptions.length}条消费记录`, { customerId });
                  
                  // 更新选中的客户
                  this.setData({
                    selectedCustomerId: customerId,
                    selectedCustomer: {
                      ...selectedCustomer,
                      consumptions: consumptions
                    }
                  });
                } else {
                  this.logger.error('重定向后加载消费记录失败', redirectRes.data);
                  
                  // 即使消费记录失败，也更新客户信息
                  this.setData({
                    selectedCustomerId: customerId,
                    selectedCustomer: {
                      ...selectedCustomer,
                      consumptions: []
                    }
                  });
                  
                  wx.showToast({
                    title: '获取消费记录失败',
                    icon: 'none'
                  });
                }
              },
              fail: (redirectErr) => {
                wx.hideLoading();
                this.logger.error('重定向请求错误:', redirectErr);
                
                // 即使请求失败，也更新客户信息
                this.setData({
                  selectedCustomerId: customerId,
                  selectedCustomer: {
                    ...selectedCustomer,
                    consumptions: []
                  }
                });
                
                wx.showToast({
                  title: '网络请求失败',
                  icon: 'none'
                });
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        wx.hideLoading();
        
        if (res.statusCode === 200) {
          // 直接使用返回的items数组作为消费记录
          const consumptions = res.data.items || [];
          
          this.logger.info(`加载了${consumptions.length}条消费记录`, { customerId });
          
          // 更新选中的客户
          this.setData({
            selectedCustomerId: customerId,
            selectedCustomer: {
              ...selectedCustomer,
              consumptions: consumptions
            }
          });
        } else {
          this.logger.error('加载消费记录失败', res.data);
          
          // 即使消费记录失败，也更新客户信息
          this.setData({
            selectedCustomerId: customerId,
            selectedCustomer: {
              ...selectedCustomer,
              consumptions: []
            }
          });
          
          wx.showToast({
            title: '获取消费记录失败',
            icon: 'none'
          });
        }
      },
      fail: (err) => {
        wx.hideLoading();
        this.logger.error('消费记录请求失败', err);
        
        // 即使请求失败，也更新客户信息
        this.setData({
          selectedCustomerId: customerId,
          selectedCustomer: {
            ...selectedCustomer,
            consumptions: []
          }
        });
        
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        });
      }
    });
  },
  
  /**
   * 生成分析报告
   */
  generateReport() {
    if (!this.data.selectedCustomerId) {
      this.setData({ errorMessage: '请先选择客户' });
      return;
    }
    
    // 直接导航到报告创建页面，而不是在此处生成报告
    wx.navigateTo({
      url: `/pages/report/create?id=${this.data.selectedCustomerId}`,
      success: () => {
        this.logger.info('已导航到报告创建页面', { 
          customerId: this.data.selectedCustomerId 
        });
      },
      fail: (err) => {
        this.logger.error('导航到报告创建页面失败', err);
        
        this.setData({
          errorMessage: '无法打开报告创建页面: ' + (err.errMsg || '未知错误')
        });
      }
    });
  },
  
  /**
   * 查看历史报告
   */
  viewHistoryReports() {
    wx.navigateTo({
      url: '/pages/history/history'
    });
  },
  
  /**
   * 返回首页
   */
  goToHome() {
    wx.navigateBack();
  }
});