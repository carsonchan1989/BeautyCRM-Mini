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
      model: 'Pro/deepseek-ai/DeepSeek-R1',
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
    activeTab: 'basic', // basic, advanced
    
    // 是否需要强制刷新
    forceRefresh: false
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
      apiKey: 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
      apiUrl: 'https://api.siliconflow.cn/v1',
      model: 'Pro/deepseek-ai/DeepSeek-R1'
    });
    
    // 获取客户ID参数
    const customerId = options.customerId || options.id;
    if (!customerId) {
      this.setData({
        errorMessage: '缺少客户ID参数'
      });
      return;
    }
    
    // 检查是否需要强制刷新(新增:支持true字符串或布尔值)
    const forceRefresh = options.forceRefresh === 'true' || options.forceRefresh === true;
    
    this.setData({ 
      customerId,
      forceRefresh 
    });
    
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
   * 开始生成报告
   */
  startGenerating() {
    // 获取所选客户ID
    const customerId = this.data.customerId;
    if (!customerId) {
      wx.showToast({
        title: '请先选择客户',
        icon: 'none'
      });
      return;
    }
    
    // 设置为生成中状态
    this.setData({
      isGenerating: true,
      generationProgress: 0,
      generationStatus: '正在准备生成报告...'
    });
    
    // 创建进度条更新定时器 - 每200ms更新一次进度
    this.progressTimer = setInterval(() => {
      let progress = this.data.generationProgress;
      if (progress < 98) {
        // 前20%快速增加
        if (progress < 20) {
          progress += 2;
        } 
        // 20%-80%缓慢增加
        else if (progress < 80) {
          progress += 0.5;
        }
        // 80%-98%极慢增加
        else {
          progress += 0.1;
        }
        
        // 更新状态文本
        let status = '正在准备生成报告...';
        if (progress >= 10 && progress < 30) {
          status = '正在获取客户信息...';
        } else if (progress >= 30 && progress < 60) {
          status = '正在分析客户数据...';
        } else if (progress >= 60 && progress < 90) {
          status = '正在生成报告内容...';
        } else if (progress >= 90) {
          status = '正在处理结果...';
        }
        
        this.setData({
          generationProgress: progress,
          generationStatus: status
        });
      }
    }, 200);
    
    // 开始生成报告
    this.generateCustomerReport(customerId)
      .then(result => {
        // 清除进度条定时器
        if (this.progressTimer) {
          clearInterval(this.progressTimer);
        }
        
        // 设置为100%完成
        this.setData({
          generationProgress: 100,
          generationStatus: '报告生成完成!'
        });
        
        // 延迟显示成功消息，给用户时间看到100%
        setTimeout(() => {
          // 显示成功消息
          wx.showToast({
            title: '报告生成成功!',
            icon: 'success',
            duration: 2000
          });
          
          // 延迟页面跳转
          setTimeout(() => {
            // 重置状态
            this.setData({
              isGenerating: false,
              generationProgress: 0
            });
            
            // 跳转到报告详情页
            wx.navigateTo({
              url: `/pages/report/detail?id=${customerId}&date=${result.date}&format=html`
            });
          }, 1000);
        }, 500);
      })
      .catch(error => {
        // 清除进度条定时器
        if (this.progressTimer) {
          clearInterval(this.progressTimer);
        }
        
        // 重置状态
        this.setData({
          isGenerating: false,
          generationProgress: 0
        });
        
        // 显示错误消息
        wx.showModal({
          title: '生成失败',
          content: error.message || '报告生成失败，请重试',
          showCancel: false
        });
        
        this.logger.error('生成报告失败', error);
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
            model: 'Pro/deepseek-ai/DeepSeek-R1',
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
  },
  
  /**
   * 更新高级配置
   * @param {Event} e 事件对象
   */
  updateAdvancedConfig(e) {
    const { type, value } = e.currentTarget.dataset;
    
    if (type === 'model') {
      // 始终使用固定的模型名称
      this.setData({
        'advancedConfig.model': 'Pro/deepseek-ai/DeepSeek-R1'
      });
      return;
    }
    
    // 其他配置项正常处理
    this.setData({
      [`advancedConfig.${type}`]: value
    });
    
    wx.showToast({
      title: '配置已更新',
      icon: 'success'
    });
  },
  
  /**
   * 显示API状态提示框
   * @param {String} message 提示消息
   * @param {Boolean} success 是否成功
   */
  showApiStatusTip(message, success = false) {
    wx.showModal({
      title: success ? '成功' : '提示',
      content: message,
      showCancel: false
    });
  },
  
  /**
   * 处理报告生成结果
   * @param {Object} result 报告生成结果
   * @param {Object} customer 客户信息
   */
  handleReportResult(result, customer) {
    // 更新状态
    this.setData({
      generating: false,
      progress: 100
    });
    
    if (result.fromCache) {
      this.showApiStatusTip('使用了本地缓存的报告', true);
    } else {
      // 真实API返回的结果
      this.showApiStatusTip('报告生成成功!', true);
    }
    
    // 格式化HTML内容，确保能正确显示
    let formattedHtml = '';
    if (result.html) {
      // 包装HTML使其能正确显示
      formattedHtml = `<div style="padding: 20rpx; color: #333; font-size: 28rpx; line-height: 1.6;">
        <h1 style="font-size: 36rpx; color: #0066cc; margin-bottom: 20rpx;">客户分析报告</h1>
        ${result.html}
      </div>`;
    } else if (result.text) {
      // 将纯文本转换为HTML
      formattedHtml = `<div style="padding: 20rpx; color: #333; font-size: 28rpx; line-height: 1.6;">
        <h1 style="font-size: 36rpx; color: #0066cc; margin-bottom: 20rpx;">客户分析报告</h1>
        <p style="margin-bottom: 10rpx;">${result.text.replace(/\n/g, '</p><p style="margin-bottom: 10rpx;">')}</p>
      </div>`;
    }
    
    // 将生成的报告添加到页面数据和上下文中
    this.setData({
      'reportData.html': formattedHtml,
      'reportData.text': result.text,
      'reportData.customer': customer,
      'reportData.ready': true
    });
    
    // 保存到本地存储 - 确保使用标准化的格式
    try {
      // 今日日期
      const today = new Date();
      const yyyy = today.getFullYear();
      const mm = String(today.getMonth() + 1).padStart(2, '0');
      const dd = String(today.getDate()).padStart(2, '0');
      const dateStr = `${yyyy}-${mm}-${dd}`;
      
      // 存储HTML报告
      const dateKey = `html_report_${customer.id}_${dateStr}`;
      const latestKey = `html_report_${customer.id}_latest`;
      
      wx.setStorageSync(dateKey, formattedHtml);
      wx.setStorageSync(latestKey, formattedHtml);
      
      console.log('报告已保存到本地存储', { 
        dateKey, 
        latestKey, 
        contentLength: formattedHtml.length
      });
    } catch (e) {
      console.error('保存报告到本地存储失败', e);
    }
    
    // 清理进度条定时器
    if (this.data.progressTimer) {
      clearInterval(this.data.progressTimer);
    }
  },
  
  /**
   * 模拟进度条
   * @private
   */
  _simulateProgress() {
    // 清理可能存在的定时器
    if (this.data.progressTimer) {
      clearInterval(this.data.progressTimer);
    }
    
    let progress = 10;
    const progressTimer = setInterval(() => {
      // 进度接近90%时减缓增长速度
      if (progress >= 90) {
        // 停止进度条，等待实际结果
        clearInterval(progressTimer);
      } else if (progress >= 80) {
        progress += 0.5;
      } else if (progress >= 60) {
        progress += 1;
      } else {
        progress += 3;
      }
      
      this.setData({
        generationProgress: progress,
        progressTimer
      });
    }, 600);
    
    this.setData({ progressTimer });
  },
  
  /**
   * 切换强制刷新选项
   */
  toggleForceRefresh(e) {
    const forceRefresh = e.detail.value;
    this.setData({ forceRefresh });
    
    if (forceRefresh) {
      wx.showToast({
        title: '将强制生成新报告',
        icon: 'none'
      });
    }
  },
  
  /**
   * 查看导出的提示词
   */
  viewExportedPrompts() {
    wx.navigateTo({
      url: '/pages/report/prompt'
    });
  },
  
  /**
   * 生成客户报告
   * @param {String} customerId 客户ID
   * @returns {Promise} 生成报告的Promise
   */
  generateCustomerReport(customerId) {
    return new Promise((resolve, reject) => {
      if (!customerId || !this.data.customer) {
        return reject(new Error('客户信息不完整'));
      }
      
      // 配置AI参数
      const options = {
        forceRefresh: true, // 总是强制刷新，确保每次都调用API
        aiConfig: this.data.aiConfig,
        exportPrompt: true, // 启用提示词导出
        showExportTip: true // 显示导出成功提示
      };
      
      // 根据报告配置修改自定义提示词
      let customPrompt = this.data.aiConfig.customPrompt || '';
      
      // 根据报告内容选项增加提示词
      if (!this.data.reportConfig.includeBasicInfo) {
        customPrompt += ' 不需要包含基本信息部分。';
      }
      
      if (!this.data.reportConfig.includeConsumptionHistory) {
        customPrompt += ' 不需要包含消费历史部分。';
      }
      
      if (!this.data.reportConfig.includeSkinAnalysis) {
        customPrompt += ' 不需要包含肌肤分析部分。';
      }
      
      if (!this.data.reportConfig.includeRecommendations) {
        customPrompt += ' 不需要包含个性化建议部分。';
      }
      
      // 设置报告长度
      if (this.data.reportConfig.maxLength === 'short') {
        customPrompt += ' 报告内容简洁，不超过500字。';
      } else if (this.data.reportConfig.maxLength === 'long') {
        customPrompt += ' 报告内容详尽，不少于1500字。';
      }
      
      // 更新AI配置中的自定义提示词
      if (customPrompt) {
        options.aiConfig.customPrompt = customPrompt;
      }
      
      this.logger.info('开始生成客户报告', { 
        customerId,
        options,
        forceRefresh: true // 记录日志表明强制刷新
      });
      
      // 调用报告生成器
      this.reportGenerator.generateCustomerReport(
        this.data.customer,
        this.data.consumptions,
        options
      )
      .then(result => {
        this.logger.info('报告生成成功', {
          customerId,
          fromCache: result.fromCache
        });
        
        // 将日期添加到结果
        result.date = new Date().toISOString().split('T')[0];
        resolve(result);
      })
      .catch(error => {
        this.logger.error('报告生成失败', error);
        reject(error);
      });
    });
  }
});