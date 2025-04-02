/**
 * 数据存储服务
 * 提供保存和检索Excel处理后的客户数据功能
 */
class DataStore {
  constructor(options = {}) {
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // 数据缓存
    this.cache = {
      customers: [],
      consumptions: [],
      lastUpdated: null
    };
    
    // 缓存键名
    this.cacheKeys = {
      customers: 'btyCRM_customers',
      consumptions: 'btyCRM_consumptions',
      lastUpdated: 'btyCRM_lastUpdated'
    };
    
    // 初始化
    this._initialize();
  }
  
  /**
   * 初始化数据存储
   * @private
   */
  _initialize() {
    this.logger.info('初始化数据存储服务');
    
    try {
      // 从本地缓存加载数据
      const customersCache = wx.getStorageSync(this.cacheKeys.customers);
      const consumptionsCache = wx.getStorageSync(this.cacheKeys.consumptions);
      const lastUpdated = wx.getStorageSync(this.cacheKeys.lastUpdated);
      
      if (customersCache) {
        this.cache.customers = JSON.parse(customersCache);
        this.logger.info(`从缓存加载客户数据: ${this.cache.customers.length}条`);
      }
      
      if (consumptionsCache) {
        this.cache.consumptions = JSON.parse(consumptionsCache);
        this.logger.info(`从缓存加载消费记录: ${this.cache.consumptions.length}条`);
      }
      
      if (lastUpdated) {
        this.cache.lastUpdated = lastUpdated;
        this.logger.info(`数据最后更新时间: ${lastUpdated}`);
      }
    } catch (error) {
      this.logger.error('初始化数据存储失败', error);
      // 出错时清空缓存，重新初始化
      this.cache = {
        customers: [],
        consumptions: [],
        lastUpdated: null
      };
    }
  }
  
  /**
   * 保存处理后的Excel数据
   * @param {Object} processedData 处理后的数据对象
   * @param {Boolean} merge 是否与现有数据合并
   * @returns {Promise} 保存结果
   */
  saveData(processedData, merge = true) {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('开始保存数据', {
          customerCount: processedData.customers.length,
          consumptionCount: processedData.consumptions.length,
          mergeMode: merge
        });
        
        // 更新内存缓存
        if (merge) {
          // 合并模式：保留原有数据，添加新数据
          this._mergeCustomers(processedData.customers);
          this._mergeConsumptions(processedData.consumptions);
        } else {
          // 覆盖模式：直接替换数据
          this.cache.customers = processedData.customers;
          this.cache.consumptions = processedData.consumptions;
        }
        
        // 更新最后修改时间
        const now = new Date().toISOString();
        this.cache.lastUpdated = now;
        
        // 保存到本地存储
        wx.setStorageSync(this.cacheKeys.customers, JSON.stringify(this.cache.customers));
        wx.setStorageSync(this.cacheKeys.consumptions, JSON.stringify(this.cache.consumptions));
        wx.setStorageSync(this.cacheKeys.lastUpdated, now);
        
        this.logger.info('数据保存成功', {
          totalCustomers: this.cache.customers.length,
          totalConsumptions: this.cache.consumptions.length,
          timestamp: now
        });
        
        resolve({
          success: true,
          customerCount: this.cache.customers.length,
          consumptionCount: this.cache.consumptions.length,
          lastUpdated: now
        });
      } catch (error) {
        this.logger.error('保存数据失败', error);
        reject(new Error('保存数据失败: ' + error.message));
      }
    });
  }
  
  /**
   * 合并客户数据，以customerId为唯一标识
   * @param {Array} newCustomers 新客户数据
   * @private
   */
  _mergeCustomers(newCustomers) {
    if (!Array.isArray(newCustomers) || newCustomers.length === 0) return;
    
    // 创建现有客户ID索引
    const existingIds = new Set(this.cache.customers.map(c => c.customerId));
    
    // 添加新客户
    for (const customer of newCustomers) {
      if (!customer.customerId) {
        // 生成唯一ID
        customer.customerId = `CUST_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      }
      
      if (existingIds.has(customer.customerId)) {
        // 更新现有客户信息
        const index = this.cache.customers.findIndex(c => c.customerId === customer.customerId);
        if (index !== -1) {
          // 合并对象，保留新字段
          this.cache.customers[index] = { ...this.cache.customers[index], ...customer };
        }
      } else {
        // 添加新客户
        this.cache.customers.push(customer);
        existingIds.add(customer.customerId);
      }
    }
  }
  
  /**
   * 合并消费记录
   * @param {Array} newConsumptions 新消费记录
   * @private
   */
  _mergeConsumptions(newConsumptions) {
    if (!Array.isArray(newConsumptions) || newConsumptions.length === 0) return;
    
    // 对于消费记录，我们生成唯一ID用于去重
    // 消费记录的唯一性基于客户ID + 日期 + 项目 + 金额
    const existingConsumptionKeys = new Set();
    
    // 创建现有消费记录的唯一键
    for (const consumption of this.cache.consumptions) {
      const key = `${consumption.customerId}_${consumption.date}_${consumption.projectName}_${consumption.amount}`;
      existingConsumptionKeys.add(key);
    }
    
    // 添加新消费记录
    for (const consumption of newConsumptions) {
      const key = `${consumption.customerId}_${consumption.date}_${consumption.projectName}_${consumption.amount}`;
      
      if (!existingConsumptionKeys.has(key)) {
        this.cache.consumptions.push(consumption);
        existingConsumptionKeys.add(key);
      }
    }
  }
  
  /**
   * 获取所有客户列表
   * @returns {Array} 客户列表
   */
  getAllCustomers() {
    return this.cache.customers;
  }
  
  /**
   * 获取所有消费记录
   * @returns {Array} 消费记录列表
   */
  getAllConsumptions() {
    return this.cache.consumptions;
  }
  
  /**
   * 获取特定客户的消费记录
   * @param {String} customerId 客户ID
   * @returns {Array} 客户消费记录
   */
  getCustomerConsumptions(customerId) {
    return this.cache.consumptions.filter(c => c.customerId === customerId);
  }
  
  /**
   * 获取特定客户信息
   * @param {String} customerId 客户ID
   * @returns {Object} 客户信息
   */
  getCustomerById(customerId) {
    return this.cache.customers.find(c => c.customerId === customerId);
  }
  
  /**
   * 通过名称或手机号搜索客户
   * @param {String} keyword 搜索关键词
   * @returns {Array} 匹配的客户列表
   */
  searchCustomers(keyword) {
    if (!keyword) return [];
    
    // 转换为小写以进行不区分大小写的搜索
    const lowerKeyword = keyword.toLowerCase();
    
    return this.cache.customers.filter(customer => {
      const name = (customer.name || '').toLowerCase();
      const phone = (customer.phone || '').toLowerCase();
      
      return name.includes(lowerKeyword) || phone.includes(lowerKeyword);
    });
  }
  
  /**
   * 清空所有数据
   * @returns {Promise} 操作结果
   */
  clearAllData() {
    return new Promise((resolve) => {
      this.logger.info('清空所有数据');
      
      // 清空内存缓存
      this.cache = {
        customers: [],
        consumptions: [],
        lastUpdated: null
      };
      
      // 清空本地存储
      wx.removeStorageSync(this.cacheKeys.customers);
      wx.removeStorageSync(this.cacheKeys.consumptions);
      wx.removeStorageSync(this.cacheKeys.lastUpdated);
      
      this.logger.info('数据清空完成');
      resolve({ success: true });
    });
  }
  
  /**
   * 获取数据统计信息
   * @returns {Object} 统计信息
   */
  getStatistics() {
    // 计算各项统计数据
    const customerCount = this.cache.customers.length;
    const consumptionCount = this.cache.consumptions.length;
    let totalAmount = 0;
    
    // 计算总消费金额
    for (const record of this.cache.consumptions) {
      totalAmount += parseFloat(record.amount) || 0;
    }
    
    // 按门店分组
    const storeGroups = {};
    for (const customer of this.cache.customers) {
      const store = customer.store || '未知门店';
      if (!storeGroups[store]) {
        storeGroups[store] = 0;
      }
      storeGroups[store]++;
    }
    
    return {
      customerCount,
      consumptionCount,
      totalAmount,
      storeDistribution: storeGroups,
      lastUpdated: this.cache.lastUpdated
    };
  }
  
  /**
   * 导出数据为JSON文件
   * @returns {Object} 导出的数据对象
   */
  exportData() {
    return {
      customers: this.cache.customers,
      consumptions: this.cache.consumptions,
      exportTime: new Date().toISOString(),
      statistics: this.getStatistics()
    };
  }
}

module.exports = DataStore;