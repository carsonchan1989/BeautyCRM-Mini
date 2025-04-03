// pages/test/api.js
const Logger = require('../../utils/logger');

Page({
  data: {
    apiUrl: 'https://api.siliconflow.cn/v1',
    apiKey: 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
    modelName: 'Pro/deepseek-ai/DeepSeek-R1',
    modelNameCorrect: 'deepseek-ai/deepseek-r1',
    logs: [],
    testResults: {
      connection: null,
      auth: null,
      models: null,
      modelExists: null
    },
    availableModels: [],
    testRunning: false,
    showCorrectModel: false
  },

  onLoad() {
    this.logger = new Logger({ debug: true });
    this.logger.info('API测试页面已加载');
  },

  // 清除日志
  clearLogs() {
    this.setData({
      logs: [],
      testResults: {
        connection: null,
        auth: null,
        models: null,
        modelExists: null
      },
      availableModels: []
    });
  },

  // 添加日志
  addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logs = this.data.logs;
    logs.unshift({
      time: timestamp,
      message: message,
      type: type
    });
    this.setData({ logs });
  },
  
  // 更新测试结果
  updateTestResult(key, value) {
    const testResults = this.data.testResults;
    testResults[key] = value;
    this.setData({ testResults });
  },

  // 测试API连接
  testConnection() {
    this.addLog('测试API连接...');
    this.updateTestResult('connection', 'testing');
    
    wx.request({
      url: this.data.apiUrl,
      method: 'GET',
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          this.addLog(`连接成功: ${res.statusCode}`, 'success');
          this.updateTestResult('connection', true);
        } else {
          this.addLog(`连接失败: ${res.statusCode}`, 'error');
          this.updateTestResult('connection', false);
        }
      },
      fail: (err) => {
        this.addLog(`连接错误: ${err.errMsg}`, 'error');
        this.updateTestResult('connection', false);
      }
    });
  },

  // 测试API授权
  testAuth() {
    this.addLog('测试API授权...');
    this.updateTestResult('auth', 'testing');
    
    wx.request({
      url: `${this.data.apiUrl}/models`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${this.data.apiKey}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.addLog('API授权成功', 'success');
          this.updateTestResult('auth', true);
          
          // 解析并存储模型列表
          if (res.data && res.data.data) {
            const models = res.data.data;
            this.setData({ availableModels: models });
            this.addLog(`获取到${models.length}个可用模型`, 'success');
            this.updateTestResult('models', true);
            
            // 检查模型是否存在
            this.checkModelExists();
          } else {
            this.addLog('模型列表为空或格式不正确', 'warning');
            this.updateTestResult('models', false);
          }
        } else {
          this.addLog(`API授权失败: ${res.statusCode}`, 'error');
          this.updateTestResult('auth', false);
        }
      },
      fail: (err) => {
        this.addLog(`API授权错误: ${err.errMsg}`, 'error');
        this.updateTestResult('auth', false);
      }
    });
  },

  // 检查模型是否存在
  checkModelExists() {
    this.addLog('检查模型是否存在...');
    this.updateTestResult('modelExists', 'testing');
    
    const models = this.data.availableModels;
    const modelName = this.data.modelName;
    const modelNameCorrect = this.data.modelNameCorrect;
    
    // 检查原始模型名称
    const modelExists = models.some(model => 
      model.id === modelName || model.name === modelName
    );
    
    // 检查修正后的模型名称
    const modelExistsCorrect = models.some(model => 
      model.id === modelNameCorrect || model.name === modelNameCorrect
    );
    
    if (modelExists) {
      this.addLog(`模型"${modelName}"存在!`, 'success');
      this.updateTestResult('modelExists', true);
    } else if (modelExistsCorrect) {
      this.addLog(`原始模型名"${modelName}"不存在，但修正后的名称"${modelNameCorrect}"存在!`, 'warning');
      this.setData({ showCorrectModel: true });
      this.updateTestResult('modelExists', 'corrected');
    } else {
      this.addLog(`模型不存在: 原始"${modelName}"和修正后"${modelNameCorrect}"都不可用`, 'error');
      this.addLog('建议检查可用模型列表并更新模型名称', 'info');
      this.updateTestResult('modelExists', false);
    }
    
    // 显示所有可用模型
    this.addLog('可用模型列表:', 'info');
    models.forEach(model => {
      this.addLog(`- ${model.id || model.name}`, 'info');
    });
  },

  // 测试简单API请求
  testSimpleRequest() {
    this.addLog('测试简单API请求...');
    const modelToTest = this.data.showCorrectModel ? this.data.modelNameCorrect : this.data.modelName;
    
    wx.request({
      url: `${this.data.apiUrl}/chat/completions`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${this.data.apiKey}`,
        'Content-Type': 'application/json'
      },
      data: {
        model: modelToTest,
        messages: [
          {role: 'system', content: '你是一位测试助手'},
          {role: 'user', content: '请回答"API测试成功"'}
        ],
        temperature: 0.7,
        max_tokens: 50
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.choices) {
          const content = res.data.choices[0].message.content;
          this.addLog(`API请求成功! 回复: ${content}`, 'success');
        } else {
          this.addLog(`API请求失败: ${JSON.stringify(res.data)}`, 'error');
        }
      },
      fail: (err) => {
        this.addLog(`API请求错误: ${err.errMsg}`, 'error');
      }
    });
  },

  // 运行所有测试
  runAllTests() {
    this.setData({ testRunning: true });
    this.clearLogs();
    this.addLog('开始全面API测试...', 'info');
    
    // 按顺序依次测试
    this.testConnection();
    
    setTimeout(() => {
      if (this.data.testResults.connection) {
        this.testAuth();
      } else {
        this.addLog('由于连接测试失败，跳过授权测试', 'warning');
      }
    }, 1000);
    
    setTimeout(() => {
      if (this.data.testResults.models) {
        this.testSimpleRequest();
      } else {
        this.addLog('由于模型列表测试失败，跳过API请求测试', 'warning');
      }
      this.setData({ testRunning: false });
    }, 3000);
  },

  // 更新API URL
  updateApiUrl(e) {
    this.setData({ apiUrl: e.detail.value });
  },

  // 更新API Key
  updateApiKey(e) {
    this.setData({ apiKey: e.detail.value });
  },

  // 更新模型名称
  updateModelName(e) {
    this.setData({ modelName: e.detail.value });
  },

  // 使用修正后的模型名称
  useCorrectModel() {
    this.setData({ 
      modelName: this.data.modelNameCorrect,
      showCorrectModel: false
    });
    this.addLog(`已更新模型名称为: ${this.data.modelNameCorrect}`, 'success');
  }
});