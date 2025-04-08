/**
 * 导出大模型提示词工具
 * 用于查看系统在发送给大模型前形成的完整提示文本
 */
const fs = wx.getFileSystemManager();
const apiConfig = require('../config/api');

class PromptExporter {
  constructor(options = {}) {
    this.logger = options.logger || console;
    
    // 导出文件的根目录
    this.exportDir = wx.env.USER_DATA_PATH + '/export/';
    
    // 确保导出目录存在
    try {
      fs.accessSync(this.exportDir);
    } catch (e) {
      fs.mkdirSync(this.exportDir, true);
    }
  }
  
  /**
   * 导出提示词到文件
   * @param {Object} data 包含提示词构建数据的对象
   * @param {String} filename 导出的文件名，默认为当前时间戳
   * @returns {Promise} 导出结果
   */
  exportPromptToFile(data, filename) {
    return new Promise(async (resolve, reject) => {
      try {
        // 如果未提供文件名，使用时间戳
        if (!filename) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          filename = `prompt_${timestamp}.md`;
        }
        
        // 确保文件名有.md后缀
        if (!filename.endsWith('.md')) {
          filename += '.md';
        }
        
        const filePath = this.exportDir + filename;
        
        // 日志记录导出开始
        this.logger.info('开始导出提示词', { 
          filename, 
          hasCustomer: !!data.customer,
          hasConsumptions: !!(data.consumptions && data.consumptions.length),
          hasProjects: !!(data.projects && data.projects.length)
        });
        
        // 如果没有传入项目数据，尝试从API获取
        if (!data.projects || data.projects.length === 0) {
          this.logger.info('未传入项目数据，尝试从API获取');
          try {
            data.projects = await this._fetchProjects();
            if (data.projects && data.projects.length > 0) {
              this.logger.info('从API获取项目数据成功', { count: data.projects.length });
            } else {
              this.logger.warn('从API获取到的项目数据为空');
            }
          } catch (error) {
            this.logger.warn('从API获取项目数据失败', error);
          }
        } else {
          this.logger.info('使用传入的项目数据', { count: data.projects.length });
        }
        
        // 获取客户的服务记录和沟通记录
        if (data.customer && data.customer.id) {
          try {
            // 获取服务记录
            if (!data.services || data.services.length === 0) {
              data.services = await this._fetchServices(data.customer.id);
              this.logger.info('获取服务记录成功', { count: data.services.length });
            }
            
            // 获取沟通记录
            if (!data.communications || data.communications.length === 0) {
              data.communications = await this._fetchCommunications(data.customer.id);
              this.logger.info('获取沟通记录成功', { count: data.communications.length });
            }
          } catch (error) {
            this.logger.warn('获取客户额外数据失败', error);
          }
        }
        
        // 确保项目数据是数组
        if (!Array.isArray(data.projects)) {
          this.logger.warn('项目数据不是数组，重置为空数组');
          data.projects = [];
        }
        
        // 构建Markdown内容
        const content = this._buildMarkdownContent(data);
        
        // 写入文件
        fs.writeFileSync(filePath, content, 'utf8');
        
        this.logger.info('提示词已导出', { 
          filePath,
          contentLength: content.length,
          projectCount: (data.projects || []).length
        });
        
        resolve({
          success: true,
          filePath,
          localPath: filePath,
          content
        });
      } catch (error) {
        this.logger.error('导出提示词失败', error);
        reject(error);
      }
    });
  }
  
  /**
   * 从API获取项目数据
   * @returns {Promise<Array>} 项目数据数组
   * @private
   */
  _fetchProjects() {
    return new Promise((resolve, reject) => {
      // 确保apiConfig存在且包含项目路径
      const apiConfig = require('../config/api');
      
      if (!apiConfig || !apiConfig.paths || !apiConfig.paths.project) {
        this.logger.warn('项目API路径未定义');
        return resolve([]);
      }
      
      this.logger.info('开始获取项目库数据...');
      
      // 构建API URL
      const url = apiConfig.getUrl(apiConfig.paths.project.list);
      this.logger.info('项目库API URL', { url });
      
      wx.request({
        url: url,
        method: 'GET',
        success: (res) => {
          this.logger.info(`项目库API响应状态码: ${res.statusCode}`);
          
          if (res.statusCode === 200) {
            let projects = [];
            
            // 尝试多种数据格式
            if (res.data && res.data.data && Array.isArray(res.data.data)) {
              // 标准格式：{ success: true, data: [...] }
              projects = res.data.data;
              this.logger.info('从标准格式响应中提取项目数据');
            } else if (Array.isArray(res.data)) {
              // 直接返回数组的格式
              projects = res.data;
              this.logger.info('从数组格式响应中提取项目数据');
            } else if (typeof res.data === 'object') {
              // 尝试在对象中查找项目数组
              this.logger.info(`API响应对象的键: ${Object.keys(res.data).join(', ')}`);
              
              // 尝试常见的数据字段名
              const possibleKeys = ['projects', 'items', 'results', 'list', 'records', 'data'];
              for (const key of possibleKeys) {
                if (res.data[key] && Array.isArray(res.data[key])) {
                  projects = res.data[key];
                  this.logger.info(`从响应对象的 "${key}" 字段中提取项目数据`);
                  break;
                }
              }
              
              // 如果仍然没有找到，尝试查找第一个数组类型的属性
              if (projects.length === 0) {
                for (const key in res.data) {
                  if (Array.isArray(res.data[key])) {
                    projects = res.data[key];
                    this.logger.info(`从响应对象的第一个数组字段 "${key}" 中提取项目数据`);
                    break;
                  }
                }
              }
            }
            
            // 如果找到项目数据
            if (projects && projects.length > 0) {
              this.logger.info(`成功获取项目库数据，共 ${projects.length} 条`);
              if (projects.length > 0) {
                this.logger.info(`样例项目数据: ${JSON.stringify(projects[0])}`);
              }
              resolve(projects);
            } else {
              this.logger.warn('API响应成功但未找到项目数据');
              // 打印整个响应内容用于调试
              this.logger.info(`完整响应内容: ${JSON.stringify(res.data).substring(0, 500)}...`);
              resolve([]);
            }
          } else {
            this.logger.error(`获取项目库数据失败，状态码: ${res.statusCode}`);
            reject(new Error(`获取项目库数据失败，状态码: ${res.statusCode}`));
          }
        },
        fail: (err) => {
          this.logger.error('请求项目库数据网络错误', err);
          reject(new Error('请求项目库数据失败: ' + (err.errMsg || '网络错误')));
        }
      });
    });
  }
  
  /**
   * 获取客户服务记录
   * @param {String} customerId 客户ID
   * @returns {Promise<Array>} 服务记录数组
   * @private
   */
  _fetchServices(customerId) {
    return new Promise((resolve, reject) => {
      if (!apiConfig || !apiConfig.paths || !apiConfig.paths.customer) {
        this.logger.warn('客户服务API路径未定义');
        return resolve([]);
      }
      
      wx.request({
        url: apiConfig.getUrl(apiConfig.paths.customer.service(customerId)),
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data || []);
          } else {
            reject(new Error('获取服务记录失败'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  }
  
  /**
   * 获取客户沟通记录
   * @param {String} customerId 客户ID
   * @returns {Promise<Array>} 沟通记录数组
   * @private
   */
  _fetchCommunications(customerId) {
    return new Promise((resolve, reject) => {
      if (!apiConfig || !apiConfig.paths || !apiConfig.paths.customer) {
        this.logger.warn('客户沟通API路径未定义');
        return resolve([]);
      }
      
      wx.request({
        url: apiConfig.getUrl(apiConfig.paths.customer.communication(customerId)),
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data || []);
          } else {
            reject(new Error('获取沟通记录失败'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  }
  
  /**
   * 英文健康档案字段转中文映射
   * @private
   */
  _getHealthFieldMapping() {
    return {
      // 基础字段
      'skin_type': '肤质',
      'pores_blackheads': '毛孔/黑头',
      'wrinkles_texture': '皱纹/纹理',
      'photoaging_inflammation': '光老化/炎症',
      'tcm_constitution': '中医体质',
      'tongue_features': '舌象特征',
      'long_term_health_goal': '长期健康目标',
      'short_term_health_goal': '短期健康目标',
      'short_term_beauty_goal': '短期美容目标',
      
      // 扩展健康信息字段
      'allergies': '过敏史',
      'medical_history': '病史',
      'current_medications': '当前用药',
      'skincare_routine': '护肤习惯',
      'diet_habits': '饮食习惯',
      'sleep_quality': '睡眠质量',
      'stress_level': '压力水平',
      'hydration': '水分摄入',
      'exercise_habits': '运动习惯',
      'major_concerns': '主要问题',
      'sensitivity': '敏感度',
      'previous_treatments': '过往治疗',
      
      // 生活习惯与喜好
      'care_time_flexibility': '护理时间灵活性',
      'diet_restrictions': '饮食限制',
      'environment_requirements': '环境要求',
      'exercise_pattern': '运动模式',
      'long_term_beauty_goal': '长期美容目标',
      'major_disease_history': '主要疾病史',
      'massage_pressure_preference': '按摩压力偏好',
      'medical_cosmetic_history': '医疗美容史',
      'oil_water_balance': '油水平衡',
      'pigmentation': '色素沉着',
      'pulse_data': '脉搏数据',
      'sleep_routine': '睡眠规律',
      'wellness_service_history': '健康服务史',
      'dry_sensitivity': '干性敏感',
      'condition': '状况',
      'treatment_frequency': '治疗频率',
      'preferred_treatment_type': '偏好治疗类型',
      'skin_concerns': '肌肤问题',
      'skin_goals': '肌肤目标',
      'facial_features': '面部特征',
      'age_spots': '老年斑',
      'fine_lines': '细纹',
      'redness': '发红',
      'acne': '痤疮',
      'eye_puffiness': '眼部浮肿',
      'dark_circles': '黑眼圈',
      'sun_exposure': '日晒程度',
      'family_skin_history': '家族肤质历史',
      'skincare_product_sensitivity': '护肤品敏感性',
      'metabolism_rate': '新陈代谢率',
      'circulation': '血液循环',
      'body_temperature': '体温',
      'preferred_scents': '偏好香味',
      'treatment_sensitivity': '治疗敏感度',
      'pain_tolerance': '疼痛耐受度',
      
      // 根据数据库模型添加的字段
      'menstrual_record': '生理期记录',
      'family_medical_history': '家族遗传病史',
      'family_age_distribution': '家庭人员年龄分布',
      'work_unit_type': '单位性质'
    };
  }
  
  /**
   * 获取健康字段的中文名称
   * @param {String} fieldName 英文字段名
   * @returns {String} 中文字段名
   * @private
   */
  _getChineseHealthFieldName(fieldName) {
    const mapping = this._getHealthFieldMapping();
    return mapping[fieldName] || fieldName;
  }
  
  /**
   * 格式化日期，只保留年月日
   * @param {String} dateString 日期字符串
   * @returns {String} 格式化后的日期
   * @private
   */
  _formatDateYMD(dateString) {
    if (!dateString) return '未知';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      
      return `${year}/${month}/${day}`;
    } catch (e) {
      return dateString;
    }
  }
  
  /**
   * 构建Markdown内容
   * @param {Object} data 提示词数据
   * @returns {String} Markdown格式的内容
   * @private
   */
  _buildMarkdownContent(data) {
    // 避免使用解构赋值，改用传统的对象属性访问
    const customer = data.customer;
    const consumptions = data.consumptions;
    const services = data.services;
    const communications = data.communications;
    const projects = data.projects;
    const prompt = data.prompt;
    const customPrompt = data.customPrompt;
    const templatePrompt = data.templatePrompt;
    
    let content = '# 大模型提示词内容导出\n\n';
    
    // 添加时间信息
    content += `> 导出时间: ${new Date().toLocaleString()}\n\n`;
    
    // ==== 第一部分：客户完整数据 ====
    content += `## 第一部分：客户完整数据\n\n`;
    
    // ==== 1. 客户基本信息 ====
    if (customer) {
      content += '### 1. 客户基本信息\n\n';
      
      // 格式化基本信息为表格
      content += `| 字段 | 值 |\n`;
      content += `| ---- | ---- |\n`;
      content += `| 客户ID | ${customer.id || '未知'} |\n`;
      content += `| 姓名 | ${customer.name || '未知'} |\n`;
      content += `| 性别 | ${customer.gender || '未知'} |\n`;
      content += `| 年龄 | ${customer.age || '未知'} |\n`;
      content += `| 电话 | ${customer.phone || '未知'} |\n`;
      
      // 基本信息表中可选字段
      if (customer.memberLevel) content += `| 会员等级 | ${customer.memberLevel} |\n`;
      if (customer.joinDate) content += `| 加入日期 | ${customer.joinDate} |\n`;
      if (customer.occupation) content += `| 职业 | ${customer.occupation} |\n`;
      if (customer.annual_income) content += `| 年收入 | ${customer.annual_income} |\n`;
      if (customer.personality_tags) content += `| 性格标签 | ${customer.personality_tags} |\n`;
      if (customer.family_structure) content += `| 家庭结构 | ${customer.family_structure} |\n`;
      if (customer.living_condition) content += `| 生活状况 | ${customer.living_condition} |\n`;
      if (customer.routine) content += `| 作息规律 | ${customer.routine} |\n`;
      if (customer.diet_preference) content += `| 饮食偏好 | ${customer.diet_preference} |\n`;
      if (customer.hobbies) content += `| 爱好 | ${customer.hobbies} |\n`;
      if (customer.consumption_decision) content += `| 消费决策 | ${customer.consumption_decision} |\n`;
      if (customer.risk_sensitivity) content += `| 风险敏感度 | ${customer.risk_sensitivity} |\n`;
      if (customer.hometown) content += `| 籍贯 | ${customer.hometown} |\n`;
      if (customer.residence) content += `| 现居地 | ${customer.residence} |\n`;
      if (customer.residence_years) content += `| 居住时长 | ${customer.residence_years} |\n`;
      
      // 显示标签和备注（如果有）
      if (customer.tags && customer.tags.length) {
        const tagsStr = Array.isArray(customer.tags) ? customer.tags.join(', ') : customer.tags;
        content += `| 标签 | ${tagsStr} |\n`;
      }
      if (customer.notes) {
        content += `| 备注 | ${customer.notes} |\n`;
      }
      
      content += '\n';
    }
    
    // ==== 2. 健康档案 ====
    if (customer && customer.health_records && customer.health_records.length > 0) {
      content += '### 2. 健康档案\n\n';
      
      // 使用最新的健康记录
      const health = customer.health_records[0];
      
      content += `| 类别 | 字段 | 值 |\n`;
      content += `| ------- | ---- | ---- |\n`;
      
      // 获取字段映射
      var healthMapping = this._getHealthFieldMapping();
      
      // 将健康档案字段按类别分组
      var healthCategories = {
        '皮肤状况': ['skin_type', 'oil_water_balance', 'pores_blackheads', 'wrinkles_texture', 'pigmentation', 'photoaging_inflammation'],
        '中医体质': ['tcm_constitution', 'tongue_features', 'pulse_data'],
        '生活习惯': ['sleep_routine', 'exercise_pattern', 'diet_restrictions'],
        '护理需求': ['care_time_flexibility', 'massage_pressure_preference', 'environment_requirements'],
        '美容健康目标': ['short_term_beauty_goal', 'long_term_beauty_goal', 'short_term_health_goal', 'long_term_health_goal'],
        '健康记录': ['medical_cosmetic_history', 'wellness_service_history', 'major_disease_history', 'allergies']
      };
      
      // 按分类显示字段
      for (var category in healthCategories) {
        var fields = healthCategories[category];
        for (var i = 0; i < fields.length; i++) {
          var field = fields[i];
          if (health && health.hasOwnProperty(field) && health[field]) {
            var chineseField = healthMapping[field] || field;
            content += `| ${category} | ${chineseField} | ${health[field]} |\n`;
          }
        }
      }
      
      // 检查是否有未分类的字段
      for (var key in health) {
        if (health.hasOwnProperty(key) && health[key]) {
          // 排除系统字段和已处理的分类字段
          var isSystemField = ['id', 'customer_id', 'created_at', 'updated_at'].includes(key);
          var isProcessed = false;
          
          // 检查该字段是否已在任何分类中处理过
          for (var category in healthCategories) {
            if (healthCategories[category].includes(key)) {
              isProcessed = true;
              break;
            }
          }
          
          // 如果字段未处理且不是系统字段
          if (!isProcessed && !isSystemField) {
            var chineseKey = this._getChineseHealthFieldName(key);
            content += `| 其他 | ${chineseKey} | ${health[key]} |\n`;
          }
        }
      }
      
      content += '\n';
    }
    
    // ==== 3. 消费记录 ====
    if (consumptions && consumptions.length > 0) {
      content += '### 3. 消费记录\n\n';
      
      // 添加消费记录统计
      let totalAmount = 0;
      for (var i = 0; i < consumptions.length; i++) {
        totalAmount += parseFloat(consumptions[i].amount) || 0;
      }
      
      content += `**总消费统计**\n\n`;
      content += `- 总消费次数: ${consumptions.length}次\n`;
      content += `- 总消费金额: ${totalAmount.toFixed(2)}元\n`;
      content += `- 平均单次消费: ${(totalAmount / consumptions.length).toFixed(2)}元\n\n`;
      
      // 按日期排序 - 避免使用Array扩展方法和解构赋值
      var sortedConsumptions = consumptions.slice(0);
      sortedConsumptions.sort(function(a, b) {
        return new Date(b.date || 0) - new Date(a.date || 0);
      });
      
      content += `**详细消费记录**\n\n`;
      content += `| 日期 | 项目 | 金额 | 支付方式 | 总次数 | 耗卡完成时间 | 满意度 | 备注 |\n`;
      content += `| ---- | ---- | ---- | -------- | ------ | ------------ | ------ | ---- |\n`;
      
      // 生成表格行
      for (var i = 0; i < sortedConsumptions.length; i++) {
        var record = sortedConsumptions[i];
        var projectName = record.project_name || record.projectName || '未知项目';
        var date = this._formatDateYMD(record.date) || '未知';
        var amount = record.amount || 0;
        var satisfaction = record.satisfaction || '未评价';
        var paymentMethod = record.payment_method || record.paymentMethod || '未知';
        var totalSessions = record.total_sessions || record.totalSessions || '-';
        var completionDate = this._formatDateYMD(record.completion_date || record.completionDate) || '-';
        var notes = record.notes || '';
        
        content += `| ${date} | ${projectName} | ${amount}元 | ${paymentMethod} | ${totalSessions} | ${completionDate} | ${satisfaction} | ${notes} |\n`;
      }
      
      content += '\n';
    }
    
    // ==== 4. 服务记录 ====
    if (services && services.length > 0) {
      content += '### 4. 服务记录\n\n';
      
      // 添加日志以排查服务记录数据格式
      this.logger.info('服务记录数据结构示例:', services.length > 0 ? JSON.stringify(services[0], null, 2) : '无服务记录');
      
      // 按日期排序
      var sortedServices = services.slice(0);
      sortedServices.sort(function(a, b) {
        return new Date(b.service_date || 0) - new Date(a.service_date || 0);
      });
      
      // 逐个显示服务记录（按单次形式）
      for (var i = 0; i < sortedServices.length; i++) {
        var service = sortedServices[i];
        
        // 尝试多种可能的字段名称以提高兼容性
        var serviceDate = this._formatDateYMD(service.service_date || service.date) || '未知';
        var totalAmount = service.total_amount || service.service_amount || service.amount || 0;
        
        // 从service_items_count或手动计算获取总次数
        var totalSessions = service.total_sessions || service.service_items_count || service.sessions || 0;
        var satisfaction = service.satisfaction || '未评价';
        var notes = service.notes || service.remarks || service.remark || '';
        
        // 检查服务项目数据 - 支持多种可能的字段名称
        var serviceItems = [];
        
        // 检查多种可能的项目字段名
        if (service.items && service.items.length > 0) {
          serviceItems = service.items;
        } else if (service.service_items && service.service_items.length > 0) {
          serviceItems = service.service_items;
        } else if (service.itemList && service.itemList.length > 0) {
          serviceItems = service.itemList;
        } else if (service.details && service.details.length > 0) {
          serviceItems = service.details;
        }
        
        // 记录日志以检查服务项目数据结构
        if (serviceItems.length > 0) {
          this.logger.info('服务项目数据结构示例:', JSON.stringify(serviceItems[0], null, 2));
        } else {
          this.logger.warn('未找到服务项目数据，service对象结构:', Object.keys(service).join(', '));
        }
        
        // 如果还是没有服务项目，尝试通过其他方式提取
        if (serviceItems.length === 0 && service.service_content) {
          // 假设service_content字段包含项目名称
          serviceItems = [{
            name: service.service_content,
            item_name: service.service_content,
            beautician: service.beautician || '未指定',
            price: totalAmount,
            amount: totalAmount
          }];
        }
        
        // 重新计算总次数（如果serviceItems有数据）
        if (serviceItems.length > 0 && totalSessions === 0) {
          totalSessions = 0;  // 重置为0以便从服务项目重新计算
          for (var j = 0; j < serviceItems.length; j++) {
            var item = serviceItems[j];
            var itemSessions = parseInt(item.session_count || item.sessions || item.quantity || 1);
            if (!isNaN(itemSessions)) {
              totalSessions += itemSessions;
            } else {
              totalSessions += 1;  // 如果无法解析次数，默认为1
            }
          }
        }
        
        // 当涉及到评分时，标准化为X.X/5的格式
        var satisfactionText = satisfaction;
        if (!isNaN(parseFloat(satisfaction))) {
          satisfactionText = parseFloat(satisfaction).toFixed(1) + '/5';
        }
        
        // 如果总次数仍然为0，设为默认值1
        if (totalSessions === 0) totalSessions = 1;
        
        // 服务记录标题行
        content += `${i+1}. 服务时间: ${serviceDate}, 耗卡总金额: ${totalAmount}元, 耗卡总次数: ${totalSessions}, 满意度: ${satisfactionText}\n`;
        
        // 服务项目详情
        if (serviceItems && serviceItems.length > 0) {
          for (var j = 0; j < serviceItems.length; j++) {
            var item = serviceItems[j];
            
            // 尝试多种可能的字段名
            var itemName = item.item_name || item.name || item.project_name || item.projectName || '未知项目';
            var beautician = item.beautician_name || item.beautician || item.staff || '未指定';
            var itemAmount = item.amount || item.price || item.unit_price || (totalAmount / serviceItems.length);
            var isDesignated = item.is_designated || item.isDesignated || item.is_specified || false;
            var itemSessions = item.session_count || item.sessions || item.quantity || 1;
            
            content += `  - 项目: ${itemName}, 美容师: ${beautician}, 金额: ${itemAmount}元, 次数: ${itemSessions}, 是否指定: ${isDesignated ? '是' : '否'}\n`;
          }
        } else {
          content += `  - 无详细项目记录\n`;
        }
        
        // 如果有备注，添加备注行
        if (notes) {
          content += `  备注: ${notes}\n`;
        }
        
        content += '\n';
      }
    }
    
    // ==== 5. 沟通记录 ====
    if (communications && communications.length > 0) {
      content += '### 5. 沟通记录\n\n';
      
      // 按日期排序
      var sortedCommunications = communications.slice(0);
      sortedCommunications.sort(function(a, b) {
        return new Date(b.communication_date || 0) - new Date(a.communication_date || 0);
      });
      
      content += `| 日期 | 沟通地点 | 沟通内容 |\n`;
      content += `| ---- | -------- | -------- |\n`;
      
      // 生成表格行
      for (var i = 0; i < sortedCommunications.length; i++) {
        var comm = sortedCommunications[i];
        var date = this._formatDateYMD(comm.communication_date) || '未知';
        // 将communication_type映射为沟通地点
        var location = comm.communication_type || comm.location || comm.communication_location || '未指定';
        var content_text = comm.communication_content || comm.content || '';
        
        content += `| ${date} | ${location} | ${content_text} |\n`;
      }
      
      content += '\n';
    }
    
    // ==== 6. 店内项目库 ====
    if (projects && projects.length > 0) {
      content += '### 6. 店内项目库\n\n';
      
      content += `**共有${projects.length}个项目**\n\n`;
      
      // 记录项目数据到日志
      this.logger.info(`处理项目库数据，共 ${projects.length} 个项目`);
      
      content += `| 项目名称 | 分类 | 价格 | 功效 | 建议次数 | 描述 |\n`;
      content += `| -------- | ---- | ---- | ---- | -------- | ---- |\n`;
      
      // 按分类和名称排序项目
      var sortedProjects = projects.slice(0);
      sortedProjects.sort(function(a, b) {
        var categoryA = a.category || a.type || '';
        var categoryB = b.category || b.type || '';
        
        if (categoryA === categoryB) {
          var nameA = a.name || a.project_name || '';
          var nameB = b.name || b.project_name || '';
          return nameA.localeCompare(nameB);
        }
        return categoryA.localeCompare(categoryB);
      });
      
      // 最多显示30个项目，避免文件过大
      var displayCount = Math.min(sortedProjects.length, 30);
      for (var i = 0; i < displayCount; i++) {
        var project = sortedProjects[i];
        
        // 使用多种可能的字段名
        var name = project.name || project.project_name || project.title || '未命名项目';
        var category = project.category || project.type || project.classification || '未分类';
        var price = project.price || project.cost || project.amount || 0;
        price = price ? `${price}元` : '未定价';
        var effects = project.effects || project.benefits || project.advantages || project.function || '';
        var sessions = project.sessions || project.recommended_sessions || project.times || project.total_sessions || '';
        sessions = sessions ? `${sessions}次` : '未指定';
        var description = project.description || project.details || project.summary || project.desc || '';
        
        content += `| ${name} | ${category} | ${price} | ${effects} | ${sessions} | ${description} |\n`;
      }
      
      if (sortedProjects.length > 30) {
        content += `\n*... 省略剩余${sortedProjects.length - 30}个项目 ...*\n`;
      }
      
      content += '\n';
    } else {
      this.logger.warn('没有项目库数据可显示');
      content += '### 6. 店内项目库\n\n';
      content += '**暂无项目数据**\n\n';
    }
    
    // ==== 第二部分：AI提示词 ====
    content += `## 第二部分：AI提示词\n\n`;
    
    // 添加提示词模板
    if (prompt) {
      content += '### 提示词模板\n\n';
      content += '```\n';
      // 从原始提示词中移除客户分析报告模板，保留第6点但移除模板内容
      let modifiedPrompt = prompt;
      if (modifiedPrompt.includes('根据以下客户分析报告模板生成内容')) {
        // 找到模板开始的标记
        const templateStartIndex = modifiedPrompt.indexOf('根据以下客户分析报告模板生成内容');
        if (templateStartIndex > 0) {
          // 寻找模板文本开始的位置（客户ID后的换行符）
          const customerIdLineEndIndex = modifiedPrompt.indexOf('\n', templateStartIndex);
          if (customerIdLineEndIndex > 0) {
            // 寻找模板文本结束的位置（通常是最后一个场景之后或文档结束）
            let templateEndIndex = modifiedPrompt.length;
            // 检查是否有附加内容
            const additionalContentIndex = modifiedPrompt.indexOf('报告内容详尽', customerIdLineEndIndex);
            if (additionalContentIndex > 0) {
              templateEndIndex = additionalContentIndex;
            }
            
            // 截取模板前的部分和附加要求部分（如果有）
            const beforeTemplate = modifiedPrompt.substring(0, customerIdLineEndIndex + 1);
            const afterTemplate = additionalContentIndex > 0 ? 
                                 modifiedPrompt.substring(additionalContentIndex) : 
                                 '';
            
            // 构建新的提示词，不包含具体模板内容
            modifiedPrompt = beforeTemplate + ' 请参考下方提供的模板生成内容\n' + afterTemplate;
          }
        }
      }
      
      content += modifiedPrompt;
      content += '\n```\n\n';
    }
    
    // 添加自定义提示词
    if (customPrompt) {
      content += '### 自定义提示词\n\n';
      content += '```\n';
      content += customPrompt;
      content += '\n```\n\n';
    }
    
    // 添加客户分析报告模板
    content += '### 根据以下客户分析报告模板生成内容\n\n';
    content += '```\n';
    content += `1. 客户基本情况分析
林晓薇（28岁，外资企业时尚编辑，年收入35万）呈现典型的"精致悦己型"人格特征：
生活状态：单身独居，自有公寓，作息规律（23:00-7:00），偏好轻食，注重护肤与健身，消费决策自主性强，风险敏感度低。
地域背景：杭州籍现居上海浦东，居住时长6年，适应快节奏都市生活，对高效便捷服务需求显著。
健康数据：混合偏油肤质（T区油U区干），存在鼻翼黑头、眼周细纹、光老化II级问题，中医体质为湿热质（舌红苔黄），需调节亚健康状态，改善失眠。
人性洞察：高收入独立女性追求"内外兼修"，既需即时可见的美容效果（如黑头淡化、抗初老），也注重长期健康管理，同时渴望通过高品质服务获得身份认同感。

2. 客户消耗行为分析
耗卡特征：2023年7-10月到店10次，总耗卡金额8,623元，集中于冰肌焕颜护理（4次）、黄金射频紧致疗程（3次）、帝王艾灸调理（3次），单次耗卡金额波动大（480-1,840元）。
服务偏好：
项目组合：高频叠加面部护理（冰肌焕颜）与抗衰项目（射频），辅以养生类艾灸调理，体现"美容+养生"双线需求。
美容师指定：70%耗卡指定李婷（操作轻柔、服务细致），反映对服务稳定性和情感连接的重视。
满意度：平均评分4.7/5，投诉记录1次（预约时间延误），补偿后未影响复购，显示对品牌容忍度较高但要求快速问题解决。

3. 客户消费行为分析
消费结构：3个月内累计消费12,880元，偏好高价抗衰项目（黄金射频占比52.8%），支付方式多元（支付宝、信用卡、储值卡），储值卡使用率低（仅1次）。
决策逻辑：
功效导向：优先选择"即时效果可见"项目（射频提升下颌线后主动追加颈部护理）。
社交属性：冰肌焕颜护理耗卡频次高，推测与职场形象维护强相关。
潜在机会点：未尝试身体护理（如经络排毒）、特色项目（极光泡泡），可能因时间限制或认知不足未触发需求。

4. 客户服务偏好与健康数据深化分析
服务场景需求：
时间灵活度：周末到店为主，工作日偏好晚间（结合作息23点入睡，推测19-21点为黄金时段）。
环境要求：香薰音乐氛围，排斥嘈杂环境，适合VIP室私密服务。
健康痛点：
短期：失眠改善（艾灸调理已初见成效）、黑头清洁。
长期：光老化防护、湿热体质调理（可能伴随痘痘反复风险）。
5. 客户沟通记录分析
核心诉求：
信息透明化（对比项目差异、术后修复细节）。
服务确定性（严格守时、指定技师）。
情感价值（被重视感，如投诉后补偿方案接受度高）。
沟通风格：理性直接（线上咨询占比40%），偏好图文说明而非电话沟通。
6. 客户需求总结
需求类型	显性需求	隐性需求
美容需求	抗初老、黑头清洁、颈部护理	职场竞争力提升、社交形象管理
健康需求	失眠改善、湿热体质调理	亚健康状态突破、预防潜在皮肤炎症
情感需求	服务稳定性、高效问题响应	被尊重感、个性化专属体验

7. 可匹配项目推荐
黑头专项管理套餐（冰肌焕颜+极光净透泡泡）：解决显性黑头问题，结合深层清洁与补水，预防毛孔粗大。
夜间焕肤护理（定制版射频+艾灸睡眠调理）：适配其作息时间，同步实现抗衰与助眠。
私人健康顾问服务（中医体质调理+年度光老化防护计划）：捆绑销售高频耗卡项目与长周期健康管理，提升客户粘性。
8. 销售沟通要点与话术
场景1：耗卡余额提醒+项目推荐
话术：
"晓薇您好，系统显示您的储值卡余额还剩1,200元，刚好可以体验我们新推出的【黑头专项管理套餐】。您一直做的冰肌焕颜主要针对补水提亮，而新增的极光泡泡能通过活氧吸附技术深入清洁鼻翼黑头（展示对比图）。考虑到您每周健身容易出汗加剧毛孔堵塞，这个组合能帮您实现'清洁+养护'一步到位。本周六李婷老师有专属预约档期，需要帮您锁定名额吗？"
设计逻辑：
数据关联（耗卡记录+健身习惯）增强专业感。
指定美容师触发情感偏好，限时预约制造紧迫感。
________________________________________
场景2：健康管理场景切入
话术：
"晓薇，注意到您最近三次艾灸调理都安排在傍晚，是否因为工作压力大影响睡眠？我们的中医团队针对湿热体质研发了【夜间焕肤护理】，在射频紧致后增加头部经络按摩助眠手法，搭配定制艾草精油。上周VIP客户反馈平均入睡时间提前了40分钟，您要不要试试？首次体验可赠送睡眠监测手环，方便您量化调理效果。"
设计逻辑：
从服务时间规律挖掘健康痛点，提供解决方案。
用客户案例与赠品降低决策门槛，突出"量身定制"。
________________________________________
场景3：社交场景激发升级消费
话术：
"晓薇，您之前提到常参加时尚活动，我们下月将举办'职场女神焕新计划'，参与即可获得专业妆造+品牌拍摄。您只需升级到【私人健康顾问服务】，即可免费尊享席位（展示往期活动照）。这个套餐包含全年光老化防护和季度体质检测，像您这样长期面对电脑的职场精英，不仅能维稳肌肤状态，还能优先体验抗蓝光新项目哦！"`;
    content += '\n```\n\n';
    
    return content;
  }
  
  /**
   * 组装完整的提示词
   * 注意：这个方法应该与reportGenerator.js中的逻辑保持一致，但不应该直接替换客户数据
   * @param {Object} data 提示词数据
   * @returns {String} 完整的提示词
   * @private
   */
  _assembleFullPrompt(data) {
    // 避免使用解构赋值
    const customer = data.customer;
    const consumptions = data.consumptions;
    const projects = data.projects;
    const prompt = data.prompt;
    const customPrompt = data.customPrompt;
    const templatePrompt = data.templatePrompt;
    
    // 如果已有组装好的提示词模板，直接返回
    if (templatePrompt) return templatePrompt;
    
    // 否则尝试使用实际的逻辑组装
    let fullPrompt = '# 客户分析报告生成提示词\n\n';
    
    // 第一部分：AI提示词
    fullPrompt += '## AI提示词\n\n';
    fullPrompt += prompt || '我是一名美容养生店店长，请根据以下客户信息及数据，生成一份客户分析报告。\n';
    
    // 添加自定义提示词
    if (customPrompt) {
      fullPrompt += '\n### 附加要求:\n' + customPrompt + '\n';
    }
    
    // 第二部分：报告格式示例
    fullPrompt += '\n## 根据以下客户分析报告模板生成内容\n\n';
    fullPrompt += `1. 客户基本情况分析
林晓薇（28岁，外资企业时尚编辑，年收入35万）呈现典型的"精致悦己型"人格特征：
生活状态：单身独居，自有公寓，作息规律（23:00-7:00），偏好轻食，注重护肤与健身，消费决策自主性强，风险敏感度低。
地域背景：杭州籍现居上海浦东，居住时长6年，适应快节奏都市生活，对高效便捷服务需求显著。
健康数据：混合偏油肤质（T区油U区干），存在鼻翼黑头、眼周细纹、光老化II级问题，中医体质为湿热质（舌红苔黄），需调节亚健康状态，改善失眠。
人性洞察：高收入独立女性追求"内外兼修"，既需即时可见的美容效果（如黑头淡化、抗初老），也注重长期健康管理，同时渴望通过高品质服务获得身份认同感。

2. 客户消耗行为分析
耗卡特征：2023年7-10月到店10次，总耗卡金额8,623元，集中于冰肌焕颜护理（4次）、黄金射频紧致疗程（3次）、帝王艾灸调理（3次），单次耗卡金额波动大（480-1,840元）。
服务偏好：
项目组合：高频叠加面部护理（冰肌焕颜）与抗衰项目（射频），辅以养生类艾灸调理，体现"美容+养生"双线需求。
美容师指定：70%耗卡指定李婷（操作轻柔、服务细致），反映对服务稳定性和情感连接的重视。
满意度：平均评分4.7/5，投诉记录1次（预约时间延误），补偿后未影响复购，显示对品牌容忍度较高但要求快速问题解决。

3. 客户消费行为分析
消费结构：3个月内累计消费12,880元，偏好高价抗衰项目（黄金射频占比52.8%），支付方式多元（支付宝、信用卡、储值卡），储值卡使用率低（仅1次）。
决策逻辑：
功效导向：优先选择"即时效果可见"项目（射频提升下颌线后主动追加颈部护理）。
社交属性：冰肌焕颜护理耗卡频次高，推测与职场形象维护强相关。
潜在机会点：未尝试身体护理（如经络排毒）、特色项目（极光泡泡），可能因时间限制或认知不足未触发需求。

4. 客户服务偏好与健康数据深化分析
服务场景需求：
时间灵活度：周末到店为主，工作日偏好晚间（结合作息23点入睡，推测19-21点为黄金时段）。
环境要求：香薰音乐氛围，排斥嘈杂环境，适合VIP室私密服务。
健康痛点：
短期：失眠改善（艾灸调理已初见成效）、黑头清洁。
长期：光老化防护、湿热体质调理（可能伴随痘痘反复风险）。
5. 客户沟通记录分析
核心诉求：
信息透明化（对比项目差异、术后修复细节）。
服务确定性（严格守时、指定技师）。
情感价值（被重视感，如投诉后补偿方案接受度高）。
沟通风格：理性直接（线上咨询占比40%），偏好图文说明而非电话沟通。
6. 客户需求总结
需求类型	显性需求	隐性需求
美容需求	抗初老、黑头清洁、颈部护理	职场竞争力提升、社交形象管理
健康需求	失眠改善、湿热体质调理	亚健康状态突破、预防潜在皮肤炎症
情感需求	服务稳定性、高效问题响应	被尊重感、个性化专属体验

7. 可匹配项目推荐
黑头专项管理套餐（冰肌焕颜+极光净透泡泡）：解决显性黑头问题，结合深层清洁与补水，预防毛孔粗大。
夜间焕肤护理（定制版射频+艾灸睡眠调理）：适配其作息时间，同步实现抗衰与助眠。
私人健康顾问服务（中医体质调理+年度光老化防护计划）：捆绑销售高频耗卡项目与长周期健康管理，提升客户粘性。
8. 销售沟通要点与话术
场景1：耗卡余额提醒+项目推荐
话术：
"晓薇您好，系统显示您的储值卡余额还剩1,200元，刚好可以体验我们新推出的【黑头专项管理套餐】。您一直做的冰肌焕颜主要针对补水提亮，而新增的极光泡泡能通过活氧吸附技术深入清洁鼻翼黑头（展示对比图）。考虑到您每周健身容易出汗加剧毛孔堵塞，这个组合能帮您实现'清洁+养护'一步到位。本周六李婷老师有专属预约档期，需要帮您锁定名额吗？"
设计逻辑：
数据关联（耗卡记录+健身习惯）增强专业感。
指定美容师触发情感偏好，限时预约制造紧迫感。
________________________________________
场景2：健康管理场景切入
话术：
"晓薇，注意到您最近三次艾灸调理都安排在傍晚，是否因为工作压力大影响睡眠？我们的中医团队针对湿热体质研发了【夜间焕肤护理】，在射频紧致后增加头部经络按摩助眠手法，搭配定制艾草精油。上周VIP客户反馈平均入睡时间提前了40分钟，您要不要试试？首次体验可赠送睡眠监测手环，方便您量化调理效果。"
设计逻辑：
从服务时间规律挖掘健康痛点，提供解决方案。
用客户案例与赠品降低决策门槛，突出"量身定制"。
________________________________________
场景3：社交场景激发升级消费
话术：
"晓薇，您之前提到常参加时尚活动，我们下月将举办'职场女神焕新计划'，参与即可获得专业妆造+品牌拍摄。您只需升级到【私人健康顾问服务】，即可免费尊享席位（展示往期活动照）。这个套餐包含全年光老化防护和季度体质检测，像您这样长期面对电脑的职场精英，不仅能维稳肌肤状态，还能优先体验抗蓝光新项目哦！"`;
    
    return fullPrompt;
  }
  
  /**
   * 获取导出的文件列表
   * @returns {Promise} 文件列表
   */
  getExportedFiles() {
    return new Promise((resolve, reject) => {
      try {
        const fileList = fs.readdirSync(this.exportDir);
        const mdFiles = fileList.filter(file => file.endsWith('.md'));
        
        resolve({
          success: true,
          files: mdFiles.map(file => ({
            name: file,
            path: this.exportDir + file,
            date: new Date() // 理想情况下应该获取文件的创建时间，但wx.fs不直接支持
          }))
        });
      } catch (error) {
        this.logger.error('获取导出文件列表失败', error);
        reject(error);
      }
    });
  }
  
  /**
   * 删除导出的文件
   * @param {String} filename 文件名
   * @returns {Promise} 删除结果
   */
  deleteExportedFile(filename) {
    return new Promise((resolve, reject) => {
      try {
        const filePath = this.exportDir + filename;
        fs.unlinkSync(filePath);
        
        resolve({
          success: true,
          message: `文件 ${filename} 已删除`
        });
      } catch (error) {
        this.logger.error('删除导出文件失败', error);
        reject(error);
      }
    });
  }
}

module.exports = PromptExporter;