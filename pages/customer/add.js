// pages/customer/add.js
const Logger = require('../../utils/logger');
const apiConfig = require('../../config/api');
const app = getApp();

Page({
  data: {
    isEdit: false, // 是否是编辑模式
    customerId: '', // 编辑时的客户ID
    loading: false, // 加载状态
    submitting: false, // 提交状态
    
    // 客户信息 - 与数据库模型匹配
    customer: {
      // 基本信息
      name: '',
      gender: '女',
      age: '',
      store: '总店',
      
      // 家庭及居住情况
      hometown: '',
      residence: '',
      residence_years: '',
      family_structure: '',
      family_age_distribution: '',
      living_condition: '',
      
      // 个性与生活习惯
      personality_tags: '',
      consumption_decision: '',
      risk_sensitivity: '',
      hobbies: '',
      routine: '',
      diet_preference: '',
      
      // 健康档案
      // 皮肤状况
      skin_type: '', // 肤质类型
      skin_oil_balance: '', // 水油平衡
      pore_condition: '', // 毛孔与黑头
      wrinkle_texture: '', // 皱纹与纹理
      pigmentation: '', // 色素沉着
      photoaging: '', // 光老化与炎症
      
      // 中医体质
      tcm_constitution: '', // 体质类型
      tongue_diagnosis: '', // 舌象特征
      pulse_diagnosis: '', // 脉象数据
      
      // 生活习惯
      daily_schedule: '', // 作息规律
      exercise_frequency: '', // 运动频率
      diet_taboo: '', // 饮食禁忌
      
      // 护理需求
      time_flexibility: '', // 时间灵活度
      massage_preference: '', // 手法力度偏好
      environment_preference: '', // 环境氛围
      
      // 美容健康目标
      short_term_beauty: '', // 短期美丽目标
      long_term_beauty: '', // 长期美丽目标
      short_term_health: '', // 短期健康目标
      long_term_health: '', // 长期健康目标
      
      // 健康记录
      medical_cosmetic_history: '', // 医美操作史
      health_service_history: '', // 大健康服务史
      allergy_history: '', // 过敏史
      major_disease_history: '', // 重大疾病历史
      
      // 职业与收入
      occupation: '',
      work_unit_type: '',
      annual_income: ''
    },
    
    // 选项数据
    genderOptions: ['女', '男', '未知'],
    storeOptions: ['总店', '北区店', '南区店', '东区店', '西区店'],
    consumptionDecisionOptions: ['自主决策', '家人影响', '朋友推荐', '专业建议'],
    riskSensitivityOptions: ['高度敏感', '中度敏感', '低度敏感', '不敏感'],
    workUnitTypeOptions: ['国企', '私企', '外企', '事业单位', '政府机构', '自由职业', '其他'],
    annualIncomeOptions: ['10万以下', '10-30万', '30-50万', '50-100万', '100万以上'],
    skinTypeOptions: ['油性', '干性', '中性', '混合性', '敏感性'],
    tcmConstitutionOptions: ['气虚质', '阳虚质', '阴虚质', '痰湿质', '湿热质', '血瘀质', '气郁质', '特禀质', '平和质'],
    timeFlexibilityOptions: ['工作日', '周末', '全天可约', '仅上午', '仅下午', '仅晚上'],
    massagePreferenceOptions: ['轻柔', '适中', '重力度'],
    
    // 表单验证
    errors: {},
    
    // 状态控制
    currentTab: 'basic' // 当前选中的标签页: basic, family, personality, health, work
  },
  
  onLoad(options) {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('客户添加/编辑页面已加载', options);
    
    // 检查是否是编辑模式
    if (options.id && options.edit === 'true') {
      this.setData({
        isEdit: true,
        customerId: options.id,
        loading: true
      });
      this.loadCustomerData(options.id);
    }
  },
  
  /**
   * 加载客户数据（编辑模式）
   */
  loadCustomerData(customerId) {
    const promises = [
      // 获取基本信息
      new Promise((resolve, reject) => {
        wx.request({
          url: apiConfig.getUrl(apiConfig.paths.customer.detail(customerId)),
          method: 'GET',
          success: (res) => res.statusCode === 200 ? resolve(res.data) : reject(res),
          fail: reject
        });
      })
    ];

    Promise.all(promises)
      .then(([customerData]) => {
        this.logger.info('客户数据加载成功', customerData);
        
        // 合并客户数据和健康档案
        const customer = { ...customerData };
        delete customer.id; // 保留在customerId中
        delete customer.created_at;
        delete customer.updated_at;
        
        // 将健康档案数据合并到客户数据中
        if (customerData.health_records && customerData.health_records.length > 0) {
          const latestHealth = customerData.health_records[0];
          this.logger.info('最新健康档案数据', latestHealth);
          
          // 皮肤状况
          customer.skin_type = latestHealth.skin_type || '';
          customer.skin_oil_balance = latestHealth.oil_water_balance || '';
          customer.pore_condition = latestHealth.pores_blackheads || '';
          customer.wrinkle_texture = latestHealth.wrinkles_texture || '';
          customer.pigmentation = latestHealth.pigmentation || '';
          customer.photoaging = latestHealth.photoaging_inflammation || '';
          
          // 中医体质
          customer.tcm_constitution = latestHealth.tcm_constitution || '';
          customer.tongue_diagnosis = latestHealth.tongue_features || '';
          customer.pulse_diagnosis = latestHealth.pulse_data || '';
          
          // 生活习惯
          customer.daily_schedule = latestHealth.sleep_routine || '';
          customer.exercise_frequency = latestHealth.exercise_pattern || '';
          customer.diet_taboo = latestHealth.diet_restrictions || '';
          
          // 护理需求
          customer.time_flexibility = latestHealth.care_time_flexibility || '';
          customer.massage_preference = latestHealth.massage_pressure_preference || '';
          customer.environment_preference = latestHealth.environment_requirements || '';
          
          // 美容健康目标
          customer.short_term_beauty = latestHealth.short_term_beauty_goal || '';
          customer.long_term_beauty = latestHealth.long_term_beauty_goal || '';
          customer.short_term_health = latestHealth.short_term_health_goal || '';
          customer.long_term_health = latestHealth.long_term_health_goal || '';
          
          // 健康记录
          customer.medical_cosmetic_history = latestHealth.medical_cosmetic_history || '';
          customer.health_service_history = latestHealth.wellness_service_history || '';
          customer.allergy_history = latestHealth.allergies || '';
          customer.major_disease_history = latestHealth.major_disease_history || '';
        }
        
        this.setData({
          customer: customer,
          loading: false
        });
        
        this.logger.info('设置客户数据完成', this.data.customer);
      })
      .catch((err) => {
        this.logger.error('加载客户数据失败', err);
        wx.showToast({
          title: '加载数据失败',
          icon: 'none'
        });
        this.setData({ loading: false });
      });
  },
  
  /**
   * 切换标签页
   */
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
  },
  
  /**
   * 处理单选框变更
   */
  handleRadioChange(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({
      [`customer.${field}`]: e.detail.value,
      [`errors.${field}`]: '' // 清除错误信息
    });
  },
  
  /**
   * 处理选择器变更
   */
  handlePickerChange(e) {
    const field = e.currentTarget.dataset.field;
    const index = e.detail.value;
    const options = this.data[`${field}Options`];
    const value = options[index];
    
    this.setData({
      [`customer.${field}`]: value,
      [`errors.${field}`]: '' // 清除错误信息
    });
  },
  
  /**
   * 处理输入框变更
   */
  handleInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({
      [`customer.${field}`]: e.detail.value,
      [`errors.${field}`]: '' // 清除错误信息
    });
  },
  
  /**
   * 验证表单
   */
  validateForm() {
    const customer = this.data.customer;
    const errors = {};
    let isValid = true;
    
    // 验证姓名
    if (!customer.name || customer.name.trim() === '') {
      errors.name = '请输入客户姓名';
      isValid = false;
    }
    
    // 验证年龄
    if (customer.age) {
      const age = parseInt(customer.age);
      if (isNaN(age) || age < 0 || age > 150) {
        errors.age = '请输入有效的年龄';
        isValid = false;
      }
    }
    
    this.setData({ errors });
    return isValid;
  },
  
  /**
   * 提交表单
   */
  submitForm() {
    if (!this.validateForm()) {
      wx.showToast({
        title: '请修正表单错误',
        icon: 'none'
      });
      return;
    }
    
    this.setData({ submitting: true });
    
    const customerData = { ...this.data.customer };
    
    // 处理整数字段
    if (customerData.age) {
      customerData.age = parseInt(customerData.age);
    }
    
    if (this.data.isEdit) {
      // 编辑现有客户
      this.updateCustomer(customerData);
    } else {
      // 创建新客户
      this.createCustomer(customerData);
    }
  },
  
  /**
   * 创建新客户
   */
  createCustomer(customerData) {
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.create),
      method: 'POST',
      data: customerData,
      success: (res) => {
        if (res.statusCode === 201) {
          this.logger.info('新客户创建成功', res.data);
          
          wx.showToast({
            title: '保存成功',
            icon: 'success',
            success: () => {
              // 延迟返回，让用户看到成功提示
              setTimeout(() => {
                wx.navigateBack();
              }, 1500);
            }
          });
        } else {
          wx.showToast({
            title: res.data.error || '创建失败',
            icon: 'none'
          });
          this.setData({ submitting: false });
        }
      },
      fail: (err) => {
        this.logger.error('创建客户请求失败', err);
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        });
        this.setData({ submitting: false });
      }
    });
  },
  
  /**
   * 更新现有客户
   */
  updateCustomer(customerData) {
    // 分离健康档案数据
    const healthData = {
      // 皮肤状况
      skin_type: customerData.skin_type,
      oil_water_balance: customerData.skin_oil_balance,
      pores_blackheads: customerData.pore_condition,
      wrinkles_texture: customerData.wrinkle_texture,
      pigmentation: customerData.pigmentation,
      photoaging_inflammation: customerData.photoaging,
      
      // 中医体质
      tcm_constitution: customerData.tcm_constitution,
      tongue_features: customerData.tongue_diagnosis,
      pulse_data: customerData.pulse_diagnosis,
      
      // 生活习惯
      sleep_routine: customerData.daily_schedule,
      exercise_pattern: customerData.exercise_frequency,
      diet_restrictions: customerData.diet_taboo,
      
      // 护理需求
      care_time_flexibility: customerData.time_flexibility,
      massage_pressure_preference: customerData.massage_preference,
      environment_requirements: customerData.environment_preference,
      
      // 美容健康目标
      short_term_beauty_goal: customerData.short_term_beauty,
      long_term_beauty_goal: customerData.long_term_beauty,
      short_term_health_goal: customerData.short_term_health,
      long_term_health_goal: customerData.long_term_health,
      
      // 健康记录
      medical_cosmetic_history: customerData.medical_cosmetic_history,
      wellness_service_history: customerData.health_service_history,
      allergies: customerData.allergy_history,
      major_disease_history: customerData.major_disease_history
    };

    // 从客户数据中移除健康档案字段
    const basicData = { ...customerData };
    delete basicData.skin_type;
    delete basicData.skin_oil_balance;
    delete basicData.pore_condition;
    delete basicData.wrinkle_texture;
    delete basicData.pigmentation;
    delete basicData.photoaging;
    delete basicData.tcm_constitution;
    delete basicData.tongue_diagnosis;
    delete basicData.pulse_diagnosis;
    delete basicData.daily_schedule;
    delete basicData.exercise_frequency;
    delete basicData.diet_taboo;
    delete basicData.time_flexibility;
    delete basicData.massage_preference;
    delete basicData.environment_preference;
    delete basicData.short_term_beauty;
    delete basicData.long_term_beauty;
    delete basicData.short_term_health;
    delete basicData.long_term_health;
    delete basicData.medical_cosmetic_history;
    delete basicData.health_service_history;
    delete basicData.allergy_history;
    delete basicData.major_disease_history;

    // 并行发送更新请求
    const promises = [
      // 更新基本信息
      new Promise((resolve, reject) => {
        wx.request({
          url: apiConfig.getUrl(apiConfig.paths.customer.update(this.data.customerId)),
          method: 'PUT',
          data: basicData,
          success: (res) => res.statusCode === 200 ? resolve(res) : reject(res),
          fail: reject
        });
      }),
      // 更新健康档案
      new Promise((resolve, reject) => {
        wx.request({
          url: apiConfig.getUrl(apiConfig.paths.customer.health(this.data.customerId)),
          method: 'POST',
          data: healthData,
          success: (res) => res.statusCode === 200 ? resolve(res) : reject(res),
          fail: reject
        });
      })
    ];

    Promise.all(promises)
      .then(() => {
        this.logger.info('客户信息和健康档案更新成功');
        wx.showToast({
          title: '更新成功',
          icon: 'success',
          success: () => {
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          }
        });
      })
      .catch((err) => {
        this.logger.error('更新失败', err);
        wx.showToast({
          title: '更新失败',
          icon: 'none'
        });
        this.setData({ submitting: false });
      });
  },
  
  /**
   * 取消操作
   */
  cancelForm() {
    wx.navigateBack();
  }
});