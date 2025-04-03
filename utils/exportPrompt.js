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
        
        // 如果没有传入项目数据，尝试从API获取
        if (!data.projects || data.projects.length === 0) {
          try {
            data.projects = await this._fetchProjects();
            this.logger.info('从API获取项目数据成功', { count: data.projects.length });
          } catch (error) {
            this.logger.warn('从API获取项目数据失败', error);
          }
        }
        
        // 获取客户的服务记录和沟通记录
        if (data.customer && data.customer.id) {
          try {
            // 获取服务记录
            data.services = await this._fetchServices(data.customer.id);
            this.logger.info('获取服务记录成功', { count: data.services.length });
            
            // 获取沟通记录
            data.communications = await this._fetchCommunications(data.customer.id);
            this.logger.info('获取沟通记录成功', { count: data.communications.length });
          } catch (error) {
            this.logger.warn('获取客户额外数据失败', error);
          }
        }
        
        // 构建Markdown内容
        const content = this._buildMarkdownContent(data);
        
        // 写入文件
        fs.writeFileSync(filePath, content, 'utf8');
        
        this.logger.info('提示词已导出', { filePath });
        
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
      if (!apiConfig || !apiConfig.paths || !apiConfig.paths.project) {
        this.logger.warn('项目API路径未定义');
        return resolve([]);
      }
      
      wx.request({
        url: apiConfig.getUrl(apiConfig.paths.project.list),
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200 && res.data) {
            // 根据API返回格式提取项目数据
            const projects = res.data.data || [];
            resolve(projects);
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
      
      content += `| 字段 | 值 |\n`;
      content += `| ---- | ---- |\n`;
      
      // 获取字段映射
      var healthMapping = this._getHealthFieldMapping();
      
      // 预定义的主要健康字段，按顺序显示
      var mainHealthFields = [
        'skin_type', 'pores_blackheads', 'wrinkles_texture', 'photoaging_inflammation',
        'tcm_constitution', 'tongue_features', 'long_term_health_goal', 'short_term_health_goal', 
        'short_term_beauty_goal'
      ];
      
      // 先添加主要健康字段
      for (var i = 0; i < mainHealthFields.length; i++) {
        var field = mainHealthFields[i];
        if (health && health.hasOwnProperty(field)) {
          var chineseField = healthMapping[field] || field;
          content += `| ${chineseField} | ${health[field] || '未知'} |\n`;
        }
      }
      
      // 再添加其他健康字段
      for (var key in health) {
        if (health.hasOwnProperty(key)) {
          // 排除已添加的主要字段和系统字段
          var excludedKeys = mainHealthFields.concat(['id', 'customer_id', 'created_at', 'updated_at']);
          
          var isExcluded = false;
          for (var i = 0; i < excludedKeys.length; i++) {
            if (key === excludedKeys[i]) {
              isExcluded = true;
              break;
            }
          }
          
          if (!isExcluded && health[key]) {
            var chineseKey = this._getChineseHealthFieldName(key);
            content += `| ${chineseKey} | ${health[key]} |\n`;
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
      
      // 检查项目数据结构，记录日志
      if (projects.length > 0) {
        this.logger.info('项目库数据结构示例:', JSON.stringify(projects[0], null, 2));
      }
      
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
    }
    
    // ==== 第二部分：AI提示词 ====
    content += `## 第二部分：AI提示词\n\n`;
    
    // 添加提示词模板
    if (prompt) {
      content += '### 提示词模板\n\n';
      content += '```\n';
      content += prompt;
      content += '\n```\n\n';
    }
    
    // 添加自定义提示词
    if (customPrompt) {
      content += '### 自定义提示词\n\n';
      content += '```\n';
      content += customPrompt;
      content += '\n```\n\n';
    }
    
    // ==== 第三部分：报告示例格式 ====
    content += `## 第三部分：报告示例格式\n\n`;
    content += '```\n';
    content += `客户分析报告

1. 客户基本情况分析
[在此处提供客户的基本情况分析]

2. 客户消耗行为分析
[在此处提供客户的消耗行为分析]

3. 客户消费行为分析
[在此处提供客户的消费行为分析]

4. 客户服务偏好与健康数据深化分析
[在此处提供客户的服务偏好与健康数据分析]

5. 客户沟通记录分析
[在此处提供客户的沟通记录分析]

6. 客户需求总结
需求类型	显性需求	隐性需求
美容需求	[填写显性需求]	[填写隐性需求]
健康需求	[填写显性需求]	[填写隐性需求]
情感需求	[填写显性需求]	[填写隐性需求]

7. 可匹配项目推荐
[在此处提供可匹配的项目推荐]

8. 销售沟通要点与话术
场景1：[描述场景]
[在此处提供销售话术，不少于50字]

场景2：[描述场景]
[在此处提供销售话术，不少于50字]

场景3：[描述场景]
[在此处提供销售话术，不少于50字]`;
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
    fullPrompt += '\n## 报告格式示例\n\n';
    fullPrompt += `客户分析报告
    
1. 客户基本情况分析
[在此处提供客户的基本情况分析]

2. 客户消耗行为分析
[在此处提供客户的消耗行为分析]

3. 客户消费行为分析
[在此处提供客户的消费行为分析]

4. 客户服务偏好与健康数据深化分析
[在此处提供客户的服务偏好与健康数据分析]

5. 客户沟通记录分析
[在此处提供客户的沟通记录分析]

6. 客户需求总结
需求类型\t显性需求\t隐性需求
美容需求\t[填写显性需求]\t[填写隐性需求]
健康需求\t[填写显性需求]\t[填写隐性需求]
情感需求\t[填写显性需求]\t[填写隐性需求]

7. 可匹配项目推荐
[在此处提供可匹配的项目推荐]

8. 销售沟通要点与话术
场景1：[描述场景]
[在此处提供销售话术，不少于50字]

场景2：[描述场景]
[在此处提供销售话术，不少于50字]

场景3：[描述场景]
[在此处提供销售话术，不少于50字]`;
    
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