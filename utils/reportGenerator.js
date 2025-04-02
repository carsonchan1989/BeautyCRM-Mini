/**
 * 报告生成器
 * 调用大模型API生成客户分析报告
 */
class ReportGenerator {
  constructor(options = {}) {
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // 大模型API配置
    this.apiConfig = {
      url: options.apiUrl || 'https://api.example.com/v1/generate',
      apiKey: options.apiKey || '',
      model: options.model || 'gpt-3.5-turbo',
      temperature: options.temperature || 0.5,
      maxTokens: options.maxTokens || 2000
    };
    
    // 报告模板
    this.templates = {
      customer: {
        prompt: `请根据以下客户信息生成一份详细的分析报告：
        
客户基本信息：
{{customerInfo}}

消费记录：
{{consumptionRecords}}

请按照以下结构输出分析报告：
1. 客户概况：总结客户的基本信息和消费习惯
2. 消费分析：分析客户的消费金额、频率、项目偏好等
3. 客户画像：根据上述信息，描绘客户的性格特点、消费习惯、生活方式等
4. 推荐方案：根据客户画像，推荐适合该客户的产品和服务
5. 客户维护建议：如何维护和提升该客户的满意度和忠诚度

请使用专业的美容行业术语，报告风格要专业但易于理解。`
      }
    };
    
    // 报告缓存键名
    this.cacheKeys = {
      reports: 'btyCRM_reports'
    };
    
    // 报告缓存
    this.reportsCache = this._loadReportsFromCache();
  }
  
  /**
   * 从缓存加载报告
   * @returns {Object} 报告缓存对象
   * @private
   */
  _loadReportsFromCache() {
    try {
      const cachedReports = wx.getStorageSync(this.cacheKeys.reports);
      if (cachedReports) {
        const reports = JSON.parse(cachedReports);
        this.logger.info(`从缓存加载报告数据: ${Object.keys(reports).length}条`);
        return reports;
      }
    } catch (error) {
      this.logger.error('加载缓存报告失败', error);
    }
    
    return {};
  }
  
  /**
   * 保存报告到缓存
   * @param {Object} reports 报告对象
   * @private
   */
  _saveReportsToCache(reports) {
    try {
      wx.setStorageSync(this.cacheKeys.reports, JSON.stringify(reports));
      this.logger.info(`报告数据已保存到缓存: ${Object.keys(reports).length}条`);
    } catch (error) {
      this.logger.error('保存报告到缓存失败', error);
    }
  }
  
  /**
   * 格式化客户信息用于报告生成
   * @param {Object} customer 客户对象
   * @param {Array} consumptions 消费记录数组
   * @returns {Object} 格式化后的数据
   * @private
   */
  _formatCustomerData(customer, consumptions) {
    if (!customer) {
      return { customerInfo: '无客户信息', consumptionRecords: '无消费记录' };
    }
    
    // 格式化客户基本信息
    let customerInfo = `ID: ${customer.customerId}\n`;
    customerInfo += `姓名: ${customer.name || '未知'}\n`;
    customerInfo += `性别: ${customer.gender || '未知'}\n`;
    customerInfo += `年龄: ${customer.age || '未知'}\n`;
    customerInfo += `手机: ${customer.phone || '未知'}\n`;
    customerInfo += `地址: ${customer.address || '未知'}\n`;
    customerInfo += `生日: ${customer.birthday || '未知'}\n`;
    customerInfo += `会员卡号: ${customer.memberCardNo || '未知'}\n`;
    customerInfo += `会员等级: ${customer.memberLevel || '未知'}\n`;
    customerInfo += `所属门店: ${customer.store || '未知'}\n`;
    
    // 添加健康信息
    if (customer.health) {
      customerInfo += `\n健康信息:\n`;
      customerInfo += `健康状况: ${customer.health.condition || '未知'}\n`;
      customerInfo += `过敏史: ${customer.health.allergies || '未知'}\n`;
      customerInfo += `慢性病: ${customer.health.chronicDiseases || '未知'}\n`;
      customerInfo += `病史: ${customer.health.medicalHistory || '未知'}\n`;
      customerInfo += `体重: ${customer.health.weight || '未知'}\n`;
      customerInfo += `身高: ${customer.health.height || '未知'}\n`;
      customerInfo += `血型: ${customer.health.bloodType || '未知'}\n`;
    }
    
    // 添加生活习惯
    if (customer.habits) {
      customerInfo += `\n生活习惯:\n`;
      customerInfo += `生活习惯: ${customer.habits.lifeHabits || '未知'}\n`;
      customerInfo += `睡眠习惯: ${customer.habits.sleepPattern || '未知'}\n`;
      customerInfo += `饮食习惯: ${customer.habits.dietHabits || '未知'}\n`;
      customerInfo += `运动习惯: ${customer.habits.exercise || '未知'}\n`;
      customerInfo += `兴趣爱好: ${customer.habits.hobbies || '未知'}\n`;
    }
    
    // 备注信息
    customerInfo += `\n备注信息: ${customer.remarks || '无'}\n`;
    
    // 格式化消费记录
    let consumptionRecords = '';
    
    if (!consumptions || consumptions.length === 0) {
      consumptionRecords = '无消费记录';
    } else {
      // 排序消费记录(按日期从近到远)
      const sortedConsumptions = [...consumptions].sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return dateB - dateA;
      });
      
      let totalAmount = 0;
      
      // 添加消费记录详情
      for (let i = 0; i < sortedConsumptions.length; i++) {
        const record = sortedConsumptions[i];
        consumptionRecords += `${i+1}. 日期: ${record.date || '未知日期'}, `;
        consumptionRecords += `项目: ${record.projectName || '未知项目'}, `;
        consumptionRecords += `金额: ¥${record.amount || 0}, `;
        consumptionRecords += `支付方式: ${record.paymentMethod || '未知'}, `;
        consumptionRecords += `技师: ${record.technician || '未知'}, `;
        consumptionRecords += `满意度: ${record.satisfaction || '未评价'}\n`;
        
        totalAmount += parseFloat(record.amount) || 0;
      }
      
      // 添加消费统计
      consumptionRecords += `\n消费统计:\n`;
      consumptionRecords += `总消费次数: ${sortedConsumptions.length}次\n`;
      consumptionRecords += `总消费金额: ¥${totalAmount.toFixed(2)}\n`;
      consumptionRecords += `平均每次消费: ¥${(totalAmount / sortedConsumptions.length).toFixed(2)}\n`;
      
      // 计算最常消费的项目
      const projectCounts = {};
      sortedConsumptions.forEach(record => {
        const project = record.projectName || '未知项目';
        projectCounts[project] = (projectCounts[project] || 0) + 1;
      });
      
      let mostFrequentProject = '无';
      let maxCount = 0;
      
      Object.keys(projectCounts).forEach(project => {
        if (projectCounts[project] > maxCount) {
          mostFrequentProject = project;
          maxCount = projectCounts[project];
        }
      });
      
      consumptionRecords += `最常消费项目: ${mostFrequentProject} (${maxCount}次)\n`;
    }
    
    return {
      customerInfo,
      consumptionRecords
    };
  }
  
  /**
   * 生成客户分析报告
   * @param {Object} customer 客户对象
   * @param {Array} consumptions 消费记录数组
   * @returns {Promise} 报告生成结果
   */
  generateCustomerReport(customer, consumptions) {
    return new Promise((resolve, reject) => {
      if (!customer || !customer.customerId) {
        this.logger.error('缺少有效的客户信息');
        return reject(new Error('缺少有效的客户信息'));
      }
      
      // 检查缓存中是否有此客户的报告
      const cacheKey = `customer_${customer.customerId}_${new Date().toISOString().split('T')[0]}`;
      if (this.reportsCache[cacheKey]) {
        this.logger.info('使用缓存的报告', { customerId: customer.customerId });
        return resolve({
          report: this.reportsCache[cacheKey],
          fromCache: true
        });
      }
      
      // 格式化数据
      const { customerInfo, consumptionRecords } = this._formatCustomerData(customer, consumptions);
      
      // 生成报告提示词
      const prompt = this.templates.customer.prompt
        .replace('{{customerInfo}}', customerInfo)
        .replace('{{consumptionRecords}}', consumptionRecords);
        
      this.logger.info('开始生成客户报告', { 
        customerId: customer.customerId,
        name: customer.name,
        consumptionCount: (consumptions || []).length
      });
      
      // 调用大模型API
      this._callLargeModelAPI(prompt)
        .then(result => {
          // 保存到缓存
          this.reportsCache[cacheKey] = result;
          this._saveReportsToCache(this.reportsCache);
          
          resolve({
            report: result,
            fromCache: false
          });
        })
        .catch(error => {
          this.logger.error('报告生成失败', error);
          reject(new Error('报告生成失败: ' + error.message));
        });
    });
  }
  
  /**
   * 获取客户的历史报告
   * @param {String} customerId 客户ID
   * @returns {Array} 历史报告列表
   */
  getCustomerReportHistory(customerId) {
    if (!customerId) return [];
    
    const pattern = `customer_${customerId}_`;
    const reports = [];
    
    // 查找该客户的所有报告
    Object.keys(this.reportsCache).forEach(key => {
      if (key.startsWith(pattern)) {
        const datePart = key.substring(pattern.length);
        reports.push({
          date: datePart,
          key: key,
          report: this.reportsCache[key]
        });
      }
    });
    
    // 按日期从新到旧排序
    reports.sort((a, b) => {
      return new Date(b.date) - new Date(a.date);
    });
    
    return reports;
  }
  
  /**
   * 获取所有历史报告
   * @returns {Array} 所有历史报告
   */
  getAllReports() {
    const allReports = [];
    
    Object.keys(this.reportsCache).forEach(key => {
      // 解析报告键以获取客户ID和日期
      // 格式: customer_[customerId]_[date]
      const parts = key.split('_');
      if (parts.length >= 3 && parts[0] === 'customer') {
        const customerId = parts[1];
        const datePart = parts.slice(2).join('_');
        
        allReports.push({
          key: key,
          customerId: customerId,
          date: datePart,
          report: this.reportsCache[key]
        });
      }
    });
    
    // 按日期从新到旧排序
    allReports.sort((a, b) => {
      return new Date(b.date) - new Date(a.date);
    });
    
    return allReports;
  }
  
  /**
   * 清除特定客户的报告缓存
   * @param {String} customerId 客户ID
   */
  clearCustomerReportCache(customerId) {
    if (!customerId) return;
    
    const pattern = `customer_${customerId}_`;
    const keysToRemove = [];
    
    // 查找要删除的键
    Object.keys(this.reportsCache).forEach(key => {
      if (key.startsWith(pattern)) {
        keysToRemove.push(key);
      }
    });
    
    // 删除缓存中的报告
    keysToRemove.forEach(key => {
      delete this.reportsCache[key];
    });
    
    // 保存更新的缓存
    this._saveReportsToCache(this.reportsCache);
    
    this.logger.info(`已清除客户报告缓存`, {
      customerId,
      removedCount: keysToRemove.length
    });
  }
  
  /**
   * 清除所有报告缓存
   */
  clearAllReportCache() {
    this.reportsCache = {};
    this._saveReportsToCache(this.reportsCache);
    
    this.logger.info('已清除所有报告缓存');
  }
  
  /**
   * 调用大模型API
   * @param {String} prompt 提示词
   * @returns {Promise} API调用结果
   * @private
   */
  _callLargeModelAPI(prompt) {
    return new Promise((resolve, reject) => {
      this.logger.info('调用大模型API', { 
        url: this.apiConfig.url, 
        model: this.apiConfig.model,
        promptLength: prompt.length 
      });
      
      // 检查是否有apiKey
      if (!this.apiConfig.apiKey) {
        this.logger.warn('未配置API密钥，使用本地模拟数据');
        
        // 返回模拟数据(开发阶段)
        setTimeout(() => {
          resolve(this._getMockReport());
        }, 1500);
        
        return;
      }
      
      // 调用大模型API
      wx.request({
        url: this.apiConfig.url,
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiConfig.apiKey}`
        },
        data: {
          model: this.apiConfig.model,
          messages: [
            { role: "system", content: "你是一位专业的美容顾问助手，需要根据客户信息生成专业的分析报告。" },
            { role: "user", content: prompt }
          ],
          temperature: this.apiConfig.temperature,
          max_tokens: this.apiConfig.maxTokens
        },
        success: (res) => {
          if (res.statusCode === 200 && res.data && res.data.choices && res.data.choices.length > 0) {
            const content = res.data.choices[0].message.content;
            this.logger.info('大模型API调用成功', { 
              responseLength: content.length 
            });
            resolve(content);
          } else {
            this.logger.error('大模型API调用失败', res);
            reject(new Error('API响应异常: ' + JSON.stringify(res.data)));
          }
        },
        fail: (err) => {
          this.logger.error('大模型API调用失败', err);
          
          // 开发阶段，API失败时使用模拟数据
          this.logger.warn('API失败，使用本地模拟数据');
          setTimeout(() => {
            resolve(this._getMockReport());
          }, 1000);
        }
      });
    });
  }
  
  /**
   * 获取模拟报告（开发阶段使用）
   * @returns {String} 模拟报告内容
   * @private
   */
  _getMockReport() {
    return `# 客户分析报告

## 1. 客户概况

该客户是一位30岁的女性，会员等级为钻石会员，隶属于总店。客户居住在市中心区域，是一位有稳定消费能力的高价值客户。从消费记录来看，该客户对面部护理和身体护理项目都有较高的消费频率，总体消费水平较高，平均每次消费额度在800元以上。

## 2. 消费分析

- **消费金额**：过去半年内总共消费12次，累计消费金额达10,600元，平均每次消费883.33元
- **消费频率**：平均每半个月到店一次，消费频率稳定
- **项目偏好**：最常消费的项目为"补水焕肤护理"，共4次，其次是"深层清洁"和"精油SPA"
- **消费习惯**：倾向于选择套餐服务，多采用会员卡支付方式
- **满意度**：大部分服务评价为"非常满意"，个别项目评价为"满意"，无负面评价

## 3. 客户画像

该客户属于事业型女性，生活节奏较快，注重个人形象管理。从其消费选择和健康信息来看：

- **性格特点**：细致、注重品质、对美容护理有较高要求
- **消费习惯**：注重性价比，偏好高效、效果明显的护理项目
- **生活方式**：工作压力较大，睡眠质量不佳，饮食不太规律，有轻度运动习惯

健康状况方面，客户有轻度皮肤敏感情况，对某些化学成分存在过敏反应，需特别注意护理产品的选择。

## 4. 推荐方案

根据客户画像，推荐以下产品和服务：

1. **护理方案**：
   - 定制"敏感肌舒缓修复系列"，帮助改善皮肤敏感状况
   - "抗压舒缓SPA套餐"，缓解工作压力，改善睡眠
   - "水氧活肤"季卡服务，针对缺水问题提供长期解决方案

2. **产品推荐**：
   - 敏感肌专用修复精华，无刺激成分
   - 深层补水面膜（建议每周使用2-3次）
   - 舒压助眠喷雾，帮助改善睡眠质量

3. **会员专享**：
   - 推荐升级至黑钻会员，享受定制护理方案和产品折扣
   - 生日月专属"全身SPA放松疗程"

## 5. 客户维护建议

1. **沟通策略**：
   - 保持每月一次的微信问候，关注客户皮肤状况变化
   - 活动通知提前一周预约，避免客户因工作繁忙错过

2. **个性化服务**：
   - 记录客户喜好（如室温、音乐、茶饮偏好等）
   - 预约时间优先考虑傍晚时段（客户常选时间）

3. **满意度提升**：
   - 针对"精油SPA"项目的评价提升，建议由该客户最满意的技师王丽提供服务
   - 每季度进行一次深度的皮肤评估和方案调整

4. **忠诚度建设**：
   - 邀请参与新品体验会，收集反馈意见
   - 推荐"会员介绍计划"，增强客户归属感

客户属于高价值、高潜力群体，建议纳入VIP客户管理计划，由店长定期回访，确保服务质量和客户满意度。`;
  }
  
  /**
   * 更新API配置
   * @param {Object} config 新的API配置
   */
  updateApiConfig(config) {
    if (!config) return;
    
    // 更新现有配置
    this.apiConfig = {
      ...this.apiConfig,
      ...config
    };
    
    this.logger.info('API配置已更新', {
      url: this.apiConfig.url,
      model: this.apiConfig.model
    });
  }
}

module.exports = ReportGenerator;