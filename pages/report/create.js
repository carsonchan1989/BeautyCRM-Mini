// pages/report/create.js
const Logger = require('../../utils/logger')
const DataStore = require('../../utils/dataStore')
const ReportGenerator = require('../../utils/reportGenerator')
const apiConfig = require('../../config/api');

Page({
  data: {
    // 客户ID
    customerId: '',
    
    // 客户信息
    customer: null,
    
    // 消费记录
    consumptions: [],
    
    // AI配置
    aiConfig: {
      temperature: 0.7,
      maxTokens: 2000,
      model: 'gpt-3.5-turbo',
      customPrompt: ''
    },
    
    // 报告配置
    reportConfig: {
      includeBasicInfo: true,
      includeConsumptionHistory: true,
      includeSkinAnalysis: true,
      includeRecommendations: true,
      maxLength: 'medium' // short, medium, long
    },
    
    // 页面状态
    isGenerating: false,
    generationProgress: 0,
    errorMessage: '',
    
    // 当前激活的标签页
    activeTab: 'basic' // basic, advanced
  },
  
  onLoad(options) {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('报告生成页面已加载', options);
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ 
      logger: this.logger,
      // 读取本地存储的API配置
      apiKey: wx.getStorageSync('apiKey') || '',
      apiUrl: wx.getStorageSync('apiUrl') || 'https://api.example.com/v1/generate',
      model: wx.getStorageSync('modelName') || 'gpt-3.5-turbo'
    });
    
    // 获取客户ID参数
    const customerId = options.customerId || options.id;
    if (!customerId) {
      this.setData({
        errorMessage: '缺少客户ID参数'
      });
      return;
    }
    
    this.setData({ customerId });
    
    // 加载客户数据
    this.loadCustomerData(customerId);
    
    // 加载已保存的配置
    this.loadSavedConfig();
  },
  
  /**
   * 加载已保存的配置
   */
  loadSavedConfig() {
    try {
      const savedConfig = wx.getStorageSync('reportConfig');
      if (savedConfig) {
        this.setData({
          reportConfig: savedConfig
        });
      }
      
      const savedAiConfig = wx.getStorageSync('aiConfig');
      if (savedAiConfig) {
        this.setData({
          aiConfig: savedAiConfig
        });
      }
    } catch (error) {
      this.logger.error('加载已保存配置失败', error);
    }
  },
  
  /**
   * 加载客户数据
   */
  loadCustomerData(customerId) {
    try {
      this.logger.info('开始加载客户数据', { customerId });
      
      // 从API获取客户信息
      wx.request({
        url: apiConfig.getUrl(apiConfig.paths.customer.detail(customerId)),
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            const customer = res.data;
            this.logger.info('客户基本数据加载成功', customer);
            
            // 获取客户消费记录
            this.loadCustomerConsumptions(customerId, customer);
          } else {
            this.setData({
              errorMessage: '获取客户信息失败: ' + (res.data.error || '未知错误')
            });
          }
        },
        fail: (err) => {
          this.logger.error('获取客户信息请求失败', err);
          this.setData({
            errorMessage: '网络请求失败: ' + (err.errMsg || '未知错误')
          });
        }
      });
    } catch (error) {
      this.logger.error('加载客户数据失败', error);
      
      this.setData({
        errorMessage: '加载客户数据失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 加载客户消费记录
   */
  loadCustomerConsumptions(customerId, customer) {
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.consumption(customerId)),
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200) {
          const consumptions = res.data;
          this.logger.info('客户消费记录加载成功', { count: consumptions.length });
          
          this.setData({
            customer,
            consumptions
          });
        } else {
          // 即使消费记录获取失败，也设置客户信息
          this.setData({
            customer,
            consumptions: []
          });
          
          this.logger.warn('获取客户消费记录失败', res.data);
        }
      },
      fail: (err) => {
        // 即使消费记录获取失败，也设置客户信息
        this.setData({
          customer,
          consumptions: []
        });
        
        this.logger.error('获取客户消费记录请求失败', err);
      }
    });
  },
  
  /**
   * 切换标签页
   */
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },
  
  /**
   * 更新报告配置
   */
  updateReportConfig(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`reportConfig.${field}`]: value
    });
    
    // 保存配置到本地存储
    wx.setStorageSync('reportConfig', this.data.reportConfig);
  },
  
  /**
   * 更新开关类型的配置
   */
  updateSwitchConfig(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`reportConfig.${field}`]: value
    });
    
    // 保存配置到本地存储
    wx.setStorageSync('reportConfig', this.data.reportConfig);
  },
  
  /**
   * 更新AI配置
   */
  updateAiConfig(e) {
    const field = e.currentTarget.dataset.field;
    let value = e.detail.value;
    
    // 数值类型转换
    if (field === 'temperature' || field === 'maxTokens') {
      value = parseFloat(value);
    }
    
    this.setData({
      [`aiConfig.${field}`]: value
    });
    
    // 保存配置到本地存储
    wx.setStorageSync('aiConfig', this.data.aiConfig);
  },
  
  /**
   * 生成报告
   */
  generateReport() {
    if (!this.data.customer) {
      this.setData({
        errorMessage: '客户信息未加载'
      });
      return;
    }
    
    this.setData({
      isGenerating: true,
      generationProgress: 10,
      errorMessage: ''
    });
    
    this.logger.info('开始生成客户分析报告', {
      customerId: this.data.customerId,
      customerName: this.data.customer.name,
      configOptions: this.data.reportConfig
    });
    
    // 模拟进度更新
    let progress = 10;
    const progressInterval = setInterval(() => {
      progress += 5;
      if (progress > 90) {
        clearInterval(progressInterval);
      }
      this.setData({ generationProgress: progress });
    }, 200);
    
    // 调用报告生成器
    this.reportGenerator.generateCustomerReport(
      this.data.customer, 
      this.data.consumptions,
      {
        ...this.data.reportConfig,
        aiConfig: this.data.aiConfig
      }
    )
      .then(result => {
        // 清除进度定时器
        clearInterval(progressInterval);
        
        this.logger.info('报告生成成功', {
          customerId: this.data.customerId,
          fromCache: result.fromCache
        });
        
        this.setData({
          isGenerating: false,
          generationProgress: 100
        });
        
        // 生成成功，跳转到报告详情页面
        wx.navigateTo({
          url: `/pages/report/detail?id=${this.data.customerId}`
        });
      })
      .catch(error => {
        // 清除进度定时器
        clearInterval(progressInterval);
        
        this.logger.error('报告生成失败', error);
        
        this.setData({
          isGenerating: false,
          generationProgress: 0,
          errorMessage: '报告生成失败: ' + (error.message || '未知错误')
        });
      });
  },
  
  /**
   * 返回上一页
   */
  goBack() {
    wx.navigateBack();
  },
  
  /**
   * 重置配置为默认值
   */
  resetConfig() {
    wx.showModal({
      title: '重置确认',
      content: '确定要重置所有配置为默认值吗？',
      success: (res) => {
        if (res.confirm) {
          const defaultReportConfig = {
            includeBasicInfo: true,
            includeConsumptionHistory: true,
            includeSkinAnalysis: true,
            includeRecommendations: true,
            maxLength: 'medium'
          };
          
          const defaultAiConfig = {
            temperature: 0.7,
            maxTokens: 2000,
            model: 'gpt-3.5-turbo',
            customPrompt: ''
          };
          
          this.setData({
            reportConfig: defaultReportConfig,
            aiConfig: defaultAiConfig
          });
          
          // 保存到本地存储
          wx.setStorageSync('reportConfig', defaultReportConfig);
          wx.setStorageSync('aiConfig', defaultAiConfig);
          
          wx.showToast({
            title: '已重置为默认值',
            icon: 'success'
          });
        }
      }
    });
  }
});