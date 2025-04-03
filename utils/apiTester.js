/**
 * API测试工具
 * 用于测试大模型API连接和模型可用性
 */
class ApiTester {
  constructor(options = {}) {
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // API配置
    this.apiConfig = {
      url: options.apiUrl || 'https://api.siliconflow.cn/v1',
      apiKey: options.apiKey || 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa'
    };
    
    // 要测试的模型名称
    this.modelToTest = options.model || 'Pro/deepseek-ai/DeepSeek-R1';
  }
  
  /**
   * 测试API连接
   * @returns {Promise<Object>} 测试结果
   */
  testApiConnection() {
    return new Promise((resolve) => {
      this.logger.info('测试API连接...', { url: this.apiConfig.url });
      
      wx.request({
        url: this.apiConfig.url + '/models',
        method: 'GET',
        header: {
          'Authorization': `Bearer ${this.apiConfig.apiKey}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            this.logger.info('API连接成功!', { statusCode: res.statusCode });
            resolve({
              success: true,
              statusCode: res.statusCode,
              data: res.data,
              message: 'API连接成功'
            });
          } else {
            this.logger.error('API连接失败', { 
              statusCode: res.statusCode,
              data: res.data
            });
            resolve({
              success: false,
              statusCode: res.statusCode,
              data: res.data,
              message: `API连接失败: ${res.statusCode}`
            });
          }
        },
        fail: (err) => {
          this.logger.error('API请求失败', err);
          resolve({
            success: false,
            error: err,
            message: `API请求失败: ${err.errMsg || '未知错误'}`
          });
        }
      });
    });
  }
  
  /**
   * 获取可用模型列表
   * @returns {Promise<Array>} 可用模型列表
   */
  getAvailableModels() {
    return new Promise((resolve, reject) => {
      this.testApiConnection()
        .then(result => {
          if (result.success && result.data && result.data.data) {
            const modelList = result.data.data;
            this.logger.info(`获取到${modelList.length}个可用模型`);
            
            // 提取模型ID、名称等信息
            const models = modelList.map(model => ({
              id: model.id,
              name: model.name || model.id,
              details: model
            }));
            
            resolve(models);
          } else {
            reject(new Error('获取模型列表失败: ' + result.message));
          }
        })
        .catch(err => {
          reject(err);
        });
    });
  }
  
  /**
   * 检查指定模型是否可用
   * @returns {Promise<Object>} 检查结果
   */
  checkModelAvailability() {
    return new Promise((resolve) => {
      this.getAvailableModels()
        .then(models => {
          // 检查我们要测试的模型是否在可用列表中
          const modelToTest = this.modelToTest;
          const exactMatch = models.find(m => 
            m.id === modelToTest || 
            m.name === modelToTest
          );
          
          // 模型ID可能有多种格式写法，也尝试不区分大小写匹配
          const lowercaseModelToTest = modelToTest.toLowerCase();
          const fuzzyMatch = models.find(m => 
            m.id.toLowerCase() === lowercaseModelToTest || 
            (m.name && m.name.toLowerCase() === lowercaseModelToTest) ||
            m.id.toLowerCase().replace(/[^a-z0-9]/g, '') === lowercaseModelToTest.replace(/[^a-z0-9]/g, '')
          );
          
          if (exactMatch) {
            this.logger.info('模型可用 (完全匹配)', exactMatch);
            resolve({
              available: true,
              model: exactMatch,
              matchType: 'exact',
              allModels: models,
              message: `模型 "${modelToTest}" 可用，完全匹配`
            });
          } else if (fuzzyMatch) {
            this.logger.info('模型可能可用 (模糊匹配)', { 
              tested: modelToTest, 
              matched: fuzzyMatch 
            });
            resolve({
              available: true,
              model: fuzzyMatch,
              matchType: 'fuzzy',
              allModels: models,
              message: `模型 "${modelToTest}" 可能可用，模糊匹配到 "${fuzzyMatch.id}"`
            });
          } else {
            this.logger.error('模型不可用', { 
              tested: modelToTest, 
              availableModels: models.map(m => m.id) 
            });
            resolve({
              available: false,
              allModels: models,
              message: `模型 "${modelToTest}" 不可用。可用模型: ${models.map(m => m.id).join(', ')}`
            });
          }
        })
        .catch(err => {
          this.logger.error('检查模型可用性失败', err);
          resolve({
            available: false,
            error: err,
            message: `检查模型可用性失败: ${err.message || '未知错误'}`
          });
        });
    });
  }
  
  /**
   * 测试模型调用
   * @returns {Promise<Object>} 测试结果
   */
  testModelCall() {
    return new Promise((resolve) => {
      // 先检查模型是否可用
      this.checkModelAvailability()
        .then(result => {
          if (!result.available) {
            return resolve({
              success: false,
              message: result.message
            });
          }
          
          // 使用正确的模型ID进行测试调用
          const modelId = result.model.id;
          this.logger.info('开始测试模型调用', { modelId });
          
          // 简单的测试提示词
          const testPrompt = "你好，请用一句话介绍自己。";
          
          wx.request({
            url: this.apiConfig.url + '/chat/completions',
            method: 'POST',
            header: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.apiConfig.apiKey}`
            },
            data: {
              model: modelId,
              messages: [
                { role: "system", content: "你是一位简洁专业的助手。" },
                { role: "user", content: testPrompt }
              ],
              temperature: 0.7,
              max_tokens: 100,
              response_format: { type: "text" }
            },
            success: (res) => {
              if (res.statusCode === 200 && res.data && res.data.choices && res.data.choices.length > 0) {
                const content = res.data.choices[0].message.content;
                this.logger.info('模型调用成功', { 
                  modelId,
                  response: content
                });
                
                resolve({
                  success: true,
                  modelId,
                  content,
                  data: res.data,
                  message: '模型调用成功'
                });
              } else {
                this.logger.error('模型调用失败', res);
                resolve({
                  success: false,
                  modelId,
                  status: res.statusCode,
                  data: res.data,
                  message: `模型调用失败: ${JSON.stringify(res.data)}`
                });
              }
            },
            fail: (err) => {
              this.logger.error('模型调用请求失败', err);
              resolve({
                success: false,
                modelId,
                error: err,
                message: `模型调用请求失败: ${err.errMsg || '未知错误'}`
              });
            }
          });
        });
    });
  }
  
  /**
   * 全面测试并提供修复建议
   * @returns {Promise<Object>} 测试结果和修复建议
   */
  runFullTest() {
    return new Promise(async (resolve) => {
      try {
        // 先测试API连接
        const connectionResult = await this.testApiConnection();
        if (!connectionResult.success) {
          return resolve({
            success: false,
            stage: 'connection',
            result: connectionResult,
            recommendation: '请检查API地址和API密钥是否正确，或者API服务是否可用。'
          });
        }
        
        // 检查模型可用性
        const availabilityResult = await this.checkModelAvailability();
        if (!availabilityResult.available) {
          // 查找名称相似的模型进行推荐
          const modelToTest = this.modelToTest.toLowerCase();
          const recommendations = availabilityResult.allModels
            .filter(m => {
              const id = m.id.toLowerCase();
              return id.includes('deepseek') || modelToTest.includes(id);
            })
            .map(m => m.id);
          
          return resolve({
            success: false,
            stage: 'availability',
            result: availabilityResult,
            recommendedModels: recommendations,
            recommendation: recommendations.length > 0 
              ? `模型 "${this.modelToTest}" 不可用。您可以尝试使用以下模型: ${recommendations.join(', ')}`
              : `模型 "${this.modelToTest}" 不可用。请从可用模型列表中选择: ${availabilityResult.allModels.map(m => m.id).join(', ')}`
          });
        }
        
        // 测试模型调用
        const callResult = await this.testModelCall();
        if (!callResult.success) {
          return resolve({
            success: false,
            stage: 'call',
            result: callResult,
            recommendation: '模型调用失败。请检查API密钥权限或重试。'
          });
        }
        
        // 全部测试通过
        resolve({
          success: true,
          connection: connectionResult,
          availability: availabilityResult,
          call: callResult,
          correctModelId: callResult.modelId,
          recommendation: `所有测试通过。应使用模型ID: "${callResult.modelId}" 来替换当前使用的 "${this.modelToTest}"`
        });
      } catch (error) {
        resolve({
          success: false,
          error,
          message: `测试过程发生错误: ${error.message || '未知错误'}`,
          recommendation: '请检查网络连接和API配置。'
        });
      }
    });
  }
}

module.exports = ApiTester;