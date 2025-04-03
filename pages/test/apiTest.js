// pages/test/apiTest.js
const Logger = require('../../utils/logger');
const ApiTester = require('../../utils/apiTester');
const apiConfig = require('../../config/api');

Page({
  data: {
    apiUrl: 'https://api.siliconflow.cn/v1',
    apiKey: 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
    model: 'Pro/deepseek-ai/DeepSeek-R1',
    
    // 状态
    testing: false,
    
    // 结果
    connectionResult: null,
    modelAvailability: null,
    testCallResult: null,
    fullTestResult: null,
    
    // 可用模型列表
    availableModels: [],
    
    // 选中的正确模型ID
    correctModelId: '',
    
    // 日志记录
    logs: []
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ 
      debug: true,
      callback: (level, message, data) => {
        // 将日志添加到页面显示
        const logs = this.data.logs.slice();
        logs.unshift({
          time: new Date().toLocaleTimeString(),
          level,
          message,
          data: data ? JSON.stringify(data) : ''
        });
        
        this.setData({ logs: logs.slice(0, 50) }); // 只保留最近的50条日志
      }
    });
    
    this.logger.info('API测试页面已加载');
    
    // 初始化ApiTester
    this.initTester();
  },
  
  /**
   * 初始化API测试器
   */
  initTester() {
    this.apiTester = new ApiTester({
      logger: this.logger,
      apiUrl: this.data.apiUrl,
      apiKey: this.data.apiKey,
      model: this.data.model
    });
    
    this.logger.info('API测试器已初始化', {
      apiUrl: this.data.apiUrl,
      model: this.data.model
    });
  },
  
  /**
   * 更新API配置
   */
  updateConfig(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [field]: value
    });
    
    // 使用新配置重新初始化测试器
    this.initTester();
    
    this.logger.info('API配置已更新', { [field]: value });
  },
  
  /**
   * 测试API连接
   */
  testConnection() {
    this.setData({ 
      testing: true,
      connectionResult: null
    });
    
    this.logger.info('开始测试API连接...');
    
    this.apiTester.testApiConnection()
      .then(result => {
        this.setData({
          testing: false,
          connectionResult: result
        });
      })
      .catch(error => {
        this.logger.error('测试API连接出错', error);
        this.setData({
          testing: false,
          connectionResult: {
            success: false,
            error,
            message: `测试出错: ${error.message || '未知错误'}`
          }
        });
      });
  },
  
  /**
   * 获取可用模型列表
   */
  getAvailableModels() {
    this.setData({ 
      testing: true,
      availableModels: []
    });
    
    this.logger.info('开始获取可用模型列表...');
    
    this.apiTester.getAvailableModels()
      .then(models => {
        this.setData({
          testing: false,
          availableModels: models
        });
      })
      .catch(error => {
        this.logger.error('获取可用模型列表出错', error);
        this.setData({
          testing: false,
          connectionResult: {
            success: false,
            error,
            message: `获取出错: ${error.message || '未知错误'}`
          }
        });
      });
  },
  
  /**
   * 检查模型可用性
   */
  checkModelAvailability() {
    this.setData({ 
      testing: true,
      modelAvailability: null
    });
    
    this.logger.info('开始检查模型可用性...');
    
    this.apiTester.checkModelAvailability()
      .then(result => {
        this.setData({
          testing: false,
          modelAvailability: result
        });
        
        if (result.available && result.model) {
          this.setData({
            correctModelId: result.model.id
          });
        }
      })
      .catch(error => {
        this.logger.error('检查模型可用性出错', error);
        this.setData({
          testing: false,
          modelAvailability: {
            available: false,
            error,
            message: `检查出错: ${error.message || '未知错误'}`
          }
        });
      });
  },
  
  /**
   * 测试模型调用
   */
  testModelCall() {
    this.setData({ 
      testing: true,
      testCallResult: null
    });
    
    this.logger.info('开始测试模型调用...');
    
    this.apiTester.testModelCall()
      .then(result => {
        this.setData({
          testing: false,
          testCallResult: result
        });
        
        if (result.success) {
          this.setData({
            correctModelId: result.modelId
          });
        }
      })
      .catch(error => {
        this.logger.error('测试模型调用出错', error);
        this.setData({
          testing: false,
          testCallResult: {
            success: false,
            error,
            message: `测试出错: ${error.message || '未知错误'}`
          }
        });
      });
  },
  
  /**
   * 运行全面测试
   */
  runFullTest() {
    this.setData({ 
      testing: true,
      fullTestResult: null,
      connectionResult: null,
      modelAvailability: null,
      testCallResult: null
    });
    
    this.logger.info('开始运行全面测试...');
    
    this.apiTester.runFullTest()
      .then(result => {
        this.setData({
          testing: false,
          fullTestResult: result
        });
        
        if (result.success && result.correctModelId) {
          this.setData({
            correctModelId: result.correctModelId
          });
          
          // 显示成功提示
          wx.showModal({
            title: '测试成功',
            content: `模型可用，正确的模型ID是: "${result.correctModelId}"。是否更新项目中的模型配置？`,
            confirmText: '更新配置',
            success: (res) => {
              if (res.confirm) {
                this.updateProjectConfig(result.correctModelId);
              }
            }
          });
        } else if (result.recommendedModels && result.recommendedModels.length > 0) {
          // 有推荐模型，提示用户选择
          wx.showActionSheet({
            itemList: result.recommendedModels,
            success: (res) => {
              const selectedModel = result.recommendedModels[res.tapIndex];
              this.setData({
                model: selectedModel,
                correctModelId: selectedModel
              });
              this.initTester();
              
              // 询问是否更新配置
              wx.showModal({
                title: '更新模型',
                content: `您选择了模型: "${selectedModel}"。是否更新项目中的模型配置？`,
                confirmText: '更新配置',
                success: (modalRes) => {
                  if (modalRes.confirm) {
                    this.updateProjectConfig(selectedModel);
                  }
                }
              });
            }
          });
        }
      })
      .catch(error => {
        this.logger.error('运行全面测试出错', error);
        this.setData({
          testing: false,
          fullTestResult: {
            success: false,
            error,
            message: `测试出错: ${error.message || '未知错误'}`
          }
        });
      });
  },
  
  /**
   * 更新项目中的模型配置
   */
  updateProjectConfig(modelId) {
    if (!modelId) {
      this.logger.error('无法更新配置: 模型ID为空');
      return;
    }
    
    this.logger.info('开始更新项目配置...', { modelId });
    
    // 显示加载中提示
    wx.showLoading({
      title: '正在更新配置...',
      mask: true
    });
    
    // 这里需要由开发者实现文件修改逻辑
    // 由于微信小程序环境下无法直接修改源码文件
    // 所以我们设置一个全局配置来替代
    
    // 1. 保存到本地存储中
    try {
      wx.setStorageSync('apiModelConfig', {
        url: this.data.apiUrl,
        apiKey: this.data.apiKey,
        model: modelId,
        updatedAt: new Date().toISOString()
      });
      
      this.logger.info('配置已保存到本地存储');
      
      // 2. 如果需要，还可以发送到服务器保存
      
      wx.hideLoading();
      wx.showToast({
        title: '配置已更新',
        icon: 'success'
      });
    } catch (error) {
      wx.hideLoading();
      this.logger.error('保存配置失败', error);
      
      wx.showModal({
        title: '配置更新失败',
        content: `保存配置时出错: ${error.message || '未知错误'}`,
        showCancel: false
      });
    }
  },
  
  /**
   * 复制正确模型ID到剪贴板
   */
  copyModelId() {
    if (!this.data.correctModelId) {
      wx.showToast({
        title: '没有可用的模型ID',
        icon: 'none'
      });
      return;
    }
    
    wx.setClipboardData({
      data: this.data.correctModelId,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板'
        });
      }
    });
  },
  
  /**
   * 返回上一页
   */
  goBack() {
    wx.navigateBack();
  }
});