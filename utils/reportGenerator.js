/**
 * 报告生成器
 * 调用大模型API生成客户分析报告
 */
const apiConfig = require('../config/api');

class ReportGenerator {
  constructor(options = {}) {
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // 使用固定的模型名称
    const MODEL_NAME = "Pro/deepseek-ai/DeepSeek-R1";
    
    // 大模型API配置
    this.apiConfig = {
      url: options.apiUrl || 'https://api.siliconflow.cn/v1',
      apiKey: options.apiKey || 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
      model: MODEL_NAME, // 使用固定的模型名称
      temperature: options.temperature || 0.7,
      maxTokens: options.maxTokens || 2000
    };
    
    // API模型实际已验证可用，记录配置
    this.logger.info('初始化ReportGenerator，API配置:', {
      url: this.apiConfig.url,
      model: MODEL_NAME // 使用固定的模型名称
    });
    
    // 报告模板
    this.templates = {
      customer: {
        prompt: `我是一名美容养生店店长，请根据上述客户信息及数据，按照客户分析报告的框架，生成{{customerId}}客户的客户分析报告。要求：
1)结合对人性的理解以及大数据的分析； 
2)分析尽量详细，显示思考过程，不低于200字； 
3)根据这些分析，结合店内项目库，思考客户可能存在的需求，并提示可以满足这些需求的项目是什么； 
4)围绕这些需求如何进行销售，并编写相关沟通要点和销售话术，话术尽量涵盖不同沟通场景及切入点，单条话术不低于50字，话术不低于3条。
5)生成html格式的客户报告返回
6)根据以下客户分析报告模板生成内容:
{{customerId}}
客户分析报告
 

1. 客户基本情况分析
{{customerInfo}}

2. 客户消耗行为分析
{{consumptionRecords}}

3. 客户消费行为分析

4. 客户服务偏好与健康数据深化分析

5. 客户沟通记录分析

6. 客户需求总结
需求类型	显性需求	隐性需求
美容需求	
健康需求	
情感需求	

7. 可匹配项目推荐

8. 销售沟通要点与话术
场景1：
场景2：
场景3：`
      }
    };
    
    // 报告缓存键名
    this.cacheKeys = {
      reports: 'btyCRM_reports'
    };
    
    // 报告缓存
    this.reportsCache = this._loadReportsFromCache();
    
    // 初始化提示词导出工具
    try {
      const PromptExporter = require('./exportPrompt');
      this.promptExporter = new PromptExporter({ logger: this.logger });
      this.logger.info('提示词导出工具初始化成功');
    } catch (error) {
      this.logger.warn('提示词导出工具初始化失败', error);
      this.promptExporter = null;
    }
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
   * 调用大模型API
   * @param {String} prompt 提示词
   * @returns {Promise} API调用结果
   * @private
   */
  _callLargeModelAPI(prompt) {
    return new Promise((resolve, reject) => {
      const MODEL_NAME = "Pro/deepseek-ai/DeepSeek-R1"; // 固定的模型名称
      
      this.logger.info('调用大模型API', { 
        url: this.apiConfig.url, 
        model: MODEL_NAME, // 使用固定的模型名称
        promptLength: prompt.length 
      });
      
      // 检查是否有apiKey
      if (!this.apiConfig.apiKey) {
        this.logger.warn('未配置API密钥');
        return reject(new Error('未配置API密钥，请先设置API密钥'));
      }
      
      // 提取客户ID，用于存储报告
      let customerId = 'unknown';
      const idMatch = prompt.match(/生成(.*?)客户的客户分析报告/);
      if (idMatch && idMatch[1]) {
        customerId = idMatch[1].trim();
      }
      
      // 调用大模型API (使用已验证可用的DeepSeek API格式)
      wx.request({
        url: this.apiConfig.url + '/chat/completions',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiConfig.apiKey}`
        },
        data: {
          model: MODEL_NAME, // 使用固定的模型名称
          messages: [
            { role: "system", content: "你是一位专业的美容顾问助手，需要根据客户信息生成专业的分析报告。请务必返回HTML格式的内容。" },
            { role: "user", content: prompt }
          ],
          temperature: this.apiConfig.temperature,
          max_tokens: this.apiConfig.maxTokens,
          response_format: { type: "text" }
        },
        // 增加超时时间至3分钟(180000毫秒)
        timeout: 180000,
        success: (res) => {
          if (res.statusCode === 200 && res.data && res.data.choices && res.data.choices.length > 0) {
            const content = res.data.choices[0].message.content;
            this.logger.info('大模型API调用成功', { 
              responseLength: content.length,
              customerId: customerId
            });
            
            // 处理HTML内容
            let htmlContent = content;
            
            // 检查内容是否已经是HTML格式，如果不是则简单转换
            if (!content.includes('<html') && !content.includes('<body')) {
              htmlContent = `<div class="report-container">${content.replace(/\n/g, '<br>')}</div>`;
            }
            
            // 将返回的HTML内容保存到本地
            this._saveReportToStorage(customerId, htmlContent);
            
            // 同步报告到缓存系统
            this._syncReportToCache(customerId, {
              date: new Date().toISOString().split('T')[0],
              format: 'html',
              summary: '通过AI模型生成的客户分析报告'
            });
            
            // 返回HTML内容和普通文本内容
            resolve({
              html: htmlContent,
              text: content,
              customerId: customerId
            });
          } else {
            this.logger.error('大模型API调用失败', res);
            reject(new Error('API响应异常: ' + (res.data?.error?.message || '未知错误')));
          }
        },
        fail: (err) => {
          this.logger.error('大模型API调用失败', err);
          reject(new Error('API连接失败: ' + (err.errMsg || '网络错误或超时')));
        }
      });
    });
  }
  
  /**
   * 检查API是否可用
   * @returns {Promise<boolean>} API是否可用
   * @private
   */
  _checkApiAvailability() {
    // 固定的模型名称
    const MODEL_NAME = "Pro/deepseek-ai/DeepSeek-R1";
    
    return new Promise((resolve) => {
      wx.request({
        url: this.apiConfig.url + '/models',
        method: 'GET',
        header: {
          'Authorization': `Bearer ${this.apiConfig.apiKey}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            // 检查返回的模型列表中是否包含我们要使用的模型
            let modelExists = false;
            if (res.data && res.data.data) {
              const modelList = res.data.data;
              modelExists = modelList.some(model => 
                model.id === MODEL_NAME || 
                model.name === MODEL_NAME
              );
              
              if (!modelExists) {
                this.logger.warn('所需模型不在可用模型列表中', {
                  requestedModel: MODEL_NAME,
                  availableModels: modelList.map(m => m.id || m.name)
                });
              }
            }
            resolve(true); // 即使模型不存在，API服务本身是可用的
          } else {
            this.logger.error('API服务不可用', res);
            resolve(false);
          }
        },
        fail: () => {
          this.logger.error('API服务连接失败');
          resolve(false);
        }
      });
    });
  }
  
  /**
   * 保存HTML报告到本地存储
   * @param {String} customerId 客户ID
   * @param {String} htmlContent HTML内容
   * @private
   */
  _saveReportToStorage(customerId, htmlContent) {
    if (!customerId || !htmlContent) {
      this.logger.warn('保存报告时缺少必要参数', { customerId });
      return;
    }
    
    try {
      // 保存最新报告
      const latestKey = `html_report_${customerId}_latest`;
      wx.setStorageSync(latestKey, htmlContent);
      
      // 保存带日期的报告版本
      const date = new Date().toISOString().split('T')[0];
      const dateKey = `html_report_${customerId}_${date}`;
      wx.setStorageSync(dateKey, htmlContent);
      
      this.logger.info('HTML报告已保存到本地存储', { customerId, date });
    } catch (error) {
      this.logger.error('保存HTML报告失败', error);
    }
  }
  
  /**
   * 同步HTML报告到报告缓存系统
   * @param {String} customerId 客户ID 
   * @param {Object} metadata 报告元数据
   * @private
   */
  _syncReportToCache(customerId, metadata) {
    if (!customerId) {
      this.logger.warn('同步报告时缺少客户ID');
      return;
    }
    
    try {
      // 加载最新缓存
      this.reportsCache = this._loadReportsFromCache();
      
      // 确保客户在缓存中有记录
      if (!this.reportsCache[customerId]) {
        this.reportsCache[customerId] = [];
      }
      
      // 添加HTML报告记录
      const reportRecord = {
        date: metadata.date || new Date().toISOString().split('T')[0],
        format: metadata.format || 'html',
        type: metadata.type || 'full',
        summary: metadata.summary || '客户分析报告'
      };
      
      // 检查是否已有相同日期的报告，如果有则更新
      const existingIndex = this.reportsCache[customerId].findIndex(
        r => r.date === reportRecord.date && r.format === reportRecord.format
      );
      
      if (existingIndex >= 0) {
        this.reportsCache[customerId][existingIndex] = reportRecord;
      } else {
        this.reportsCache[customerId].push(reportRecord);
      }
      
      // 保存更新后的缓存
      this._saveReportsToCache(this.reportsCache);
      
      this.logger.info('HTML报告已同步到报告缓存系统', { customerId, date: reportRecord.date });
    } catch (error) {
      this.logger.error('同步HTML报告到缓存失败', error);
    }
  }
  
  /**
   * 获取项目库数据
   * @returns {Promise} 项目库数据
   * @private
   */
  _getProjectData() {
    return new Promise((resolve, reject) => {
      // 使用导入的apiConfig替代原来全局的apiConfig
      if (!apiConfig || !apiConfig.paths || !apiConfig.paths.project) {
        this.logger.warn('项目API路径未定义');
        return resolve([]);
      }
      
      wx.request({
        url: apiConfig.getUrl(apiConfig.paths.project.list),
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error('获取项目库数据失败'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
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
    let customerInfo = `${customer.name || '未知'}（${customer.age || '未知'}岁，${customer.occupation || '未知职业'}，年收入${customer.annual_income || '未知'}）呈现典型的"${customer.personality_tags || '未知'}"人格特征：`;
    customerInfo += `\n生活状态：${customer.family_structure || '未知'}，${customer.living_condition || '未知'}，作息规律（${customer.routine || '未知'}），偏好${customer.diet_preference || '未知'}，${customer.hobbies || '未知'}，消费决策${customer.consumption_decision || '未知'}，风险敏感度${customer.risk_sensitivity || '未知'}。`;
    customerInfo += `\n地域背景：${customer.hometown || '未知'}籍现居${customer.residence || '未知'}，居住时长${customer.residence_years || '未知'}，适应快节奏都市生活，对高效便捷服务需求显著。`;
    
    // 添加健康信息
    if (customer.health_records && customer.health_records.length > 0) {
      const health = customer.health_records[0];
      customerInfo += `\n健康数据：${health.skin_type || '未知肤质'}，存在${health.pores_blackheads || '未知'}、${health.wrinkles_texture || '未知'}、${health.photoaging_inflammation || '未知'}问题，中医体质为${health.tcm_constitution || '未知'}（${health.tongue_features || '未知'}），需${health.long_term_health_goal || '未知'}，改善${health.short_term_health_goal || '未知'}。`;
    }
    
    customerInfo += `\n人性洞察：高收入独立女性追求"内外兼修"，既需即时可见的美容效果（如${customer.health_records && customer.health_records.length > 0 ? customer.health_records[0].short_term_beauty_goal : '未知'}），也注重长期健康管理，同时渴望通过高品质服务获得身份认同感。`;
    
    // 格式化消费记录
    let consumptionRecords = '';
    
    if (!consumptions || consumptions.length === 0) {
      consumptionRecords = '无消费记录';
    } else {
      // 排序消费记录(按日期从近到远)
      const sortedConsumptions = [...consumptions].sort((a, b) => {
        // 使用iOS兼容的日期格式化方法
        const dateA = this._formatDateForIOS(a.date);
        const dateB = this._formatDateForIOS(b.date);
        return dateB - dateA;
      });
      
      let totalAmount = 0;
      const projectFrequency = {};
      const beauticianFrequency = {};
      let serviceCount = 0;
      
      // 统计项目和美容师频率
      for (const record of sortedConsumptions) {
        totalAmount += parseFloat(record.amount) || 0;
        serviceCount++;
        
        const projectName = record.project_name || '未知项目';
        projectFrequency[projectName] = (projectFrequency[projectName] || 0) + 1;
        
        // 如果有服务项目，统计美容师
        if (record.service_items && record.service_items.length > 0) {
          for (const item of record.service_items) {
            const beauticianName = item.beautician_name || '未知';
            beauticianFrequency[beauticianName] = (beauticianFrequency[beauticianName] || 0) + 1;
          }
        }
      }
      
      // 找出最常消费的项目
      let mostFrequentProject = '无';
      let maxProjectCount = 0;
      for (const project in projectFrequency) {
        if (projectFrequency[project] > maxProjectCount) {
          mostFrequentProject = project;
          maxProjectCount = projectFrequency[project];
        }
      }
      
      // 找出最常指定的美容师
      let mostFrequentBeautician = '无';
      let maxBeauticianCount = 0;
      for (const beautician in beauticianFrequency) {
        if (beauticianFrequency[beautician] > maxBeauticianCount) {
          mostFrequentBeautician = beautician;
          maxBeauticianCount = beauticianFrequency[beautician];
        }
      }
      
      // 计算指定美容师的比例
      const specifiedBeauticianRate = Math.round((maxBeauticianCount / serviceCount) * 100);
      
      // 格式化消费行为分析文本
      consumptionRecords = `耗卡特征：${sortedConsumptions[0].date ? sortedConsumptions[0].date.substring(0, 7) : '未知'}-${sortedConsumptions[sortedConsumptions.length-1].date ? sortedConsumptions[sortedConsumptions.length-1].date.substring(0, 7) : '未知'}到店${serviceCount}次，总耗卡金额${totalAmount.toFixed(2)}元，集中于${mostFrequentProject}（${maxProjectCount}次），单次耗卡金额波动${(totalAmount / serviceCount).toFixed(0)}元。\n\n`;
      
      consumptionRecords += `服务偏好：\n`;
      consumptionRecords += `项目组合：高频叠加${Object.keys(projectFrequency).slice(0, 3).join('、')}，体现多元化需求。\n`;
      consumptionRecords += `美容师指定：${specifiedBeauticianRate}%耗卡指定${mostFrequentBeautician}，反映对服务稳定性和情感连接的重视。\n`;
      
      // 添加满意度评价
      const satisfactionSum = sortedConsumptions.reduce((sum, record) => sum + (parseFloat(record.satisfaction) || 0), 0);
      const avgSatisfaction = satisfactionSum / sortedConsumptions.length;
      consumptionRecords += `满意度：平均评分${avgSatisfaction.toFixed(1)}/5，显示对品牌满意度良好。`;
    }
    
    return {
      customerInfo,
      consumptionRecords,
      customerId: customer.id || 'unknown'
    };
  }
  
  /**
   * 生成客户分析报告
   * @param {Object} customer 客户对象
   * @param {Array} consumptions 消费记录数组
   * @param {Object} options 配置选项
   * @returns {Promise} 报告生成结果
   */
  generateCustomerReport(customer, consumptions, options = {}) {
    return new Promise(async (resolve, reject) => {
      if (!customer || !customer.id) {
        this.logger.error('缺少有效的客户信息');
        return reject(new Error('缺少有效的客户信息'));
      }
      
      try {
        // 更新API配置
        if (options.aiConfig) {
          this.updateApiConfig(options.aiConfig);
        }
        
        // 检查是否强制刷新
        const forceRefresh = options.forceRefresh === true;
        
        // 检查缓存中是否有此客户的HTML报告
        const today = new Date(); // 当前日期不需要格式化，直接使用new Date()创建
        const dateStr = today.getFullYear() + '-' + 
                       String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                       String(today.getDate()).padStart(2, '0');
        
        const htmlCacheKey = `html_report_${customer.id}_latest`;
        
        // 如果不是强制刷新且有缓存，则使用缓存
        if (!forceRefresh) {
          const cachedHtml = wx.getStorageSync(htmlCacheKey);
          if (cachedHtml) {
            this.logger.info('使用缓存的HTML报告', { 
              customerId: customer.id,
              cacheDate: dateStr
            });
            
            // 确保缓存的HTML报告也同步到传统缓存系统中
            this._syncHtmlReportToCache(customer.id, cachedHtml, dateStr);
            
            return resolve({
              html: cachedHtml,
              text: cachedHtml, // 为了兼容性，也提供text属性
              customerId: customer.id,
              fromCache: true
            });
          }
        }
        
        // 格式化数据
        const { customerInfo, consumptionRecords, customerId } = this._formatCustomerData(customer, consumptions);
        
        // 获取项目库数据
        let projectList = [];
        try {
          projectList = await this._getProjectData();
          this.logger.info('获取项目库数据成功', { count: projectList.length });
        } catch (error) {
          this.logger.warn('获取项目库数据失败', error);
        }
        
        // 生成报告提示词
        let prompt = this.templates.customer.prompt
          .replace('{{customerInfo}}', customerInfo)
          .replace('{{consumptionRecords}}', consumptionRecords)
          .replace(/{{customerId}}/g, customerId); // 替换所有出现的customerId
          
        // 添加自定义提示词
        if (options.aiConfig && options.aiConfig.customPrompt) {
          prompt += '\n\n附加说明：' + options.aiConfig.customPrompt;
        }
        
        // 添加项目库数据
        if (projectList.length > 0) {
          prompt += '\n\n店内项目库：\n';
          for (let i = 0; i < Math.min(projectList.length, 10); i++) {
            const project = projectList[i];
            prompt += `${i+1}. ${project.name}: ${project.description || '无描述'}, 价格: ${project.price || '未定价'}\n`;
          }
        }
        
        this.logger.info('开始生成客户报告', { 
          customerId: customer.id,
          name: customer.name,
          consumptionCount: (consumptions || []).length
        });
        
        // 在调用大模型API之前，添加下面代码以导出提示词：
        if (options.exportPrompt && this.promptExporter) {
          try {
            // 构建文件名
            const timestamp = new Date().toISOString().split('T')[0];
            const filename = `customer_${customer.id}_${timestamp}.md`;
            
            // 导出提示词，不再传递fullPrompt
            const exportResult = await this.promptExporter.exportPromptToFile({
              customer,
              consumptions,
              projects: projectList,
              prompt: prompt,
              customPrompt: options.aiConfig?.customPrompt
            }, filename);
            
            this.logger.info('提示词导出完成', exportResult);
            
            if (options.showExportTip) {
              wx.showToast({
                title: '提示词导出成功',
                icon: 'success',
                duration: 2000
              });
            }
          } catch (error) {
            this.logger.warn('提示词导出失败', error);
          }
        }
        
        // 调用大模型API
        this._callLargeModelAPI(prompt)
          .then(result => {
            // 结果现在是一个对象，包含html和text属性
            resolve({
              ...result,
              fromCache: false
            });
          })
          .catch(error => {
            this.logger.error('报告生成失败', error);
            reject(new Error('报告生成失败: ' + error.message));
          });
      } catch (error) {
        this.logger.error('报告生成过程出错', error);
        reject(new Error('报告生成失败: ' + error.message));
      }
    });
  }
  
  /**
   * 获取客户报告
   * @param {String} customerId 客户ID
   * @param {String} date 报告日期，不指定则获取最新
   * @returns {Object|null} 报告内容
   */
  getCustomerReport(customerId, date) {
    if (!customerId) return null;
    
    try {
      // 构建存储键名
      const htmlKey = date 
        ? `html_report_${customerId}_${date}` 
        : `html_report_${customerId}_latest`;
      
      // 尝试获取HTML报告
      const htmlContent = wx.getStorageSync(htmlKey);
      if (htmlContent) {
        return {
          html: htmlContent,
          customerId: customerId,
          date: date || '最新'
        };
      }
      
      // 如果没有HTML报告，尝试获取传统报告
      const cachePattern = date 
        ? `customer_${customerId}_${date}`
        : `customer_${customerId}_`; 
      
      // 查找匹配的传统报告
      let report = null;
      if (date) {
        report = this.reportsCache[cachePattern];
      } else {
        // 找最新的报告
        let newestDate = '';
        Object.keys(this.reportsCache).forEach(key => {
          if (key.startsWith(cachePattern)) {
            const keyDate = key.substring(cachePattern.length);
            if (!newestDate || keyDate > newestDate) {
              newestDate = keyDate;
              report = this.reportsCache[key];
            }
          }
        });
      }
      
      if (report) {
        return {
          report: report,
          content: report.split('\n\n').filter(p => p.trim() !== ''),
          customerId: customerId,
          date: date || newestDate || '未知'
        };
      }
      
      return null;
    } catch (error) {
      this.logger.error('获取客户报告失败', {
        customerId, 
        date, 
        error
      });
      return null;
    }
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
   * 清除客户报告缓存
   * @param {String} customerId 客户ID
   */
  clearCustomerReportCache(customerId) {
    if (!customerId) return;
    
    // 查找客户的所有报告键
    const keysToRemove = Object.keys(this.reportsCache).filter(key =>
      key.startsWith(`customer_${customerId}_`)
    );
    
    // 删除缓存中的报告
    keysToRemove.forEach(key => {
      delete this.reportsCache[key];
    });
    
    // 保存更新的缓存
    this._saveReportsToCache(this.reportsCache);
    
    // 清理HTML报告缓存
    this._clearCustomerHtmlReports(customerId);
    
    this.logger.info(`已清除客户报告缓存`, {
      customerId,
      removedCount: keysToRemove.length
    });
  }
  
  /**
   * 清除所有报告缓存
   */
  clearAllReportCache() {
    // 清除传统报告缓存
    this.reportsCache = {};
    this._saveReportsToCache(this.reportsCache);
    
    // 清除HTML报告缓存
    this._clearAllHtmlReports();
    
    this.logger.info('已清除所有报告缓存');
  }
  
  /**
   * 清除特定客户的HTML报告
   * @param {String} customerId 客户ID
   * @private
   */
  _clearCustomerHtmlReports(customerId) {
    try {
      const keys = wx.getStorageInfoSync().keys;
      const htmlKeysPattern = `html_report_${customerId}_`;
      
      // 查找该客户的所有HTML报告
      for (const key of keys) {
        if (key.startsWith(htmlKeysPattern)) {
          wx.removeStorageSync(key);
        }
      }
      
      this.logger.info('已清除客户HTML报告', { customerId });
    } catch (error) {
      this.logger.error('清除客户HTML报告失败', error);
    }
  }
  
  /**
   * 清除所有HTML报告
   * @private
   */
  _clearAllHtmlReports() {
    try {
      const keys = wx.getStorageInfoSync().keys;
      
      // 查找所有HTML报告
      for (const key of keys) {
        if (key.startsWith('html_report_')) {
          wx.removeStorageSync(key);
        }
      }
      
      this.logger.info('已清除所有HTML报告');
    } catch (error) {
      this.logger.error('清除所有HTML报告失败', error);
    }
  }
  
  /**
   * 更新API配置
   * @param {Object} config 新的配置对象
   */
  updateApiConfig(config = {}) {
    if (!config) return;
    
    // 固定的模型名称
    const MODEL_NAME = "Pro/deepseek-ai/DeepSeek-R1";
    
    // 更新API URL
    if (config.apiUrl) {
      this.apiConfig.url = config.apiUrl;
    }
    
    // 更新API密钥
    if (config.apiKey) {
      this.apiConfig.apiKey = config.apiKey;
    }
    
    // 不再从配置中获取模型名称，而是使用固定值
    this.apiConfig.model = MODEL_NAME;
    this.logger.info('已固定使用模型', { model: MODEL_NAME });
    
    // 更新温度参数
    if (typeof config.temperature === 'number') {
      this.apiConfig.temperature = Math.max(0, Math.min(1, config.temperature));
    }
    
    // 更新最大Token数
    if (typeof config.maxTokens === 'number') {
      this.apiConfig.maxTokens = Math.max(100, Math.min(4000, config.maxTokens));
    }
    
    this.logger.info('API配置已更新', { 
      url: this.apiConfig.url,
      model: MODEL_NAME,
      temperature: this.apiConfig.temperature,
      maxTokens: this.apiConfig.maxTokens
    });
  }
  
  /**
   * 格式化日期为iOS兼容格式
   * @param {String} dateStr 日期字符串
   * @returns {Date} 日期对象
   * @private
   */
  _formatDateForIOS(dateStr) {
    if (!dateStr) return new Date();
    
    // 将日期格式转换为iOS兼容格式：YYYY-MM-DDThh:mm:ss
    return new Date(dateStr.replace(/\s+/g, 'T'));
  }
  
  /**
   * 同步HTML报告到传统缓存系统
   * @param {String} customerId 客户ID
   * @param {String} htmlContent HTML内容
   * @param {String} dateStr 日期字符串
   * @private
   */
  _syncHtmlReportToCache(customerId, htmlContent, dateStr) {
    try {
      // 构建传统缓存键
      const cacheKey = `customer_${customerId}_${dateStr}`;
      
      // 从HTML中提取一段纯文本作为摘要
      let textSummary = htmlContent
        .replace(/<[^>]*>/g, '')  // 移除HTML标签
        .replace(/\s+/g, ' ')     // 合并空格
        .trim()
        .substring(0, 1000);      // 限制长度
      
      // 添加到传统缓存
      this.reportsCache[cacheKey] = textSummary;
      
      // 保存缓存
      this._saveReportsToCache(this.reportsCache);
      
      this.logger.info('已同步HTML报告到传统缓存系统', {
        customerId,
        date: dateStr
      });
    } catch (error) {
      this.logger.error('同步HTML报告到传统缓存系统失败', error);
    }
  }
}

module.exports = ReportGenerator;