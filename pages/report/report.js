// pages/report/report.js
const DataStore = require('../../utils/dataStore')
const Logger = require('../../utils/logger')
const ReportGenerator = require('../../utils/reportGenerator')

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
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ 
      logger: this.logger,
      // 配置大模型API
      apiKey: '',
      apiUrl: 'https://api.example.com/v1/generate',
      model: 'gpt-3.5-turbo'
    });
    
    // 加载客户数据
    this.loadCustomerData();
  },
  
  /**
   * 加载客户数据
   */
  loadCustomerData() {
    this.setData({ isLoading: true });
    
    try {
      // 从DataStore获取所有客户
      const customers = this.dataStore.getAllCustomers();
      
      this.logger.info(`加载了${customers.length}位客户数据`);
      
      this.setData({
        customers: customers,
        filteredCustomers: customers,
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
    const selectedCustomer = this.data.customers.find(c => c.customerId === customerId);
    if (!selectedCustomer) return;
    
    // 获取客户消费记录
    const consumptions = this.dataStore.getCustomerConsumptions(customerId);
    
    // 更新选中的客户
    this.setData({
      selectedCustomerId: customerId,
      selectedCustomer: {
        ...selectedCustomer,
        consumptions: consumptions
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
    
    this.setData({
      isGenerating: true,
      errorMessage: ''
    });
    
    this.logger.info('开始生成客户分析报告', {
      customerId: this.data.selectedCustomerId,
      customerName: this.data.selectedCustomer.name
    });
    
    const customer = this.data.selectedCustomer;
    const consumptions = customer.consumptions || [];
    
    // 调用报告生成器
    this.reportGenerator.generateCustomerReport(customer, consumptions)
      .then(result => {
        this.logger.info('报告生成成功', {
          fromCache: result.fromCache
        });
        
        // 报告生成成功，跳转到报告查看页面
        wx.navigateTo({
          url: `/pages/report/detail?id=${this.data.selectedCustomerId}`,
          success: () => {
            // 重置状态
            this.setData({ isGenerating: false });
          }
        });
      })
      .catch(error => {
        this.logger.error('报告生成失败', error);
        
        this.setData({
          isGenerating: false,
          errorMessage: '报告生成失败: ' + (error.message || '未知错误')
        });
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