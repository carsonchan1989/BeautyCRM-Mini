// pages/customer/customer.js
const DataStore = require('../../utils/dataStore')
const Logger = require('../../utils/logger')

Page({
  data: {
    customer: null,
    consumptions: [],
    isLoading: true,
    errorMessage: ''
  },
  
  onLoad(options) {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 获取客户ID参数
    const customerId = options.id;
    if (!customerId) {
      this.setData({
        isLoading: false,
        errorMessage: '缺少客户ID参数'
      });
      return;
    }
    
    // 加载客户数据
    this.loadCustomerData(customerId);
  },
  
  /**
   * 加载客户数据
   */
  loadCustomerData(customerId) {
    try {
      // 获取客户信息
      const customer = this.dataStore.getCustomerById(customerId);
      if (!customer) {
        this.setData({
          isLoading: false,
          errorMessage: '未找到该客户信息'
        });
        return;
      }
      
      // 获取客户消费记录
      const consumptions = this.dataStore.getCustomerConsumptions(customerId);
      
      this.setData({
        customer: customer,
        consumptions: consumptions,
        isLoading: false
      });
    } catch (error) {
      this.logger.error('加载客户数据失败', error);
      
      this.setData({
        isLoading: false,
        errorMessage: '加载客户数据失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 编辑客户信息
   */
  editCustomer() {
    if (!this.data.customer) return;
    
    wx.navigateTo({
      url: `/pages/customer/edit?id=${this.data.customer.customerId}`
    });
  },
  
  /**
   * 添加消费记录
   */
  addConsumption() {
    if (!this.data.customer) return;
    
    wx.navigateTo({
      url: `/pages/customer/consumption-add?id=${this.data.customer.customerId}`
    });
  },
  
  /**
   * 查看消费记录详情
   */
  viewConsumptionDetail(e) {
    const index = e.currentTarget.dataset.index;
    if (index === undefined || !this.data.consumptions[index]) return;
    
    // 将选中的消费记录存入缓存
    wx.setStorageSync('selectedConsumption', this.data.consumptions[index]);
    
    wx.navigateTo({
      url: `/pages/customer/consumption-detail?id=${this.data.customer.customerId}`
    });
  },
  
  /**
   * 生成分析报告
   */
  generateReport() {
    if (!this.data.customer) return;
    
    wx.navigateTo({
      url: `/pages/report/create?id=${this.data.customer.customerId}`
    });
  },
  
  /**
   * 返回客户列表
   */
  goBack() {
    wx.navigateBack();
  }
});