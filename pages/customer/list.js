// pages/customer/list.js
const DataStore = require('../../utils/dataStore')
const Logger = require('../../utils/logger')
const apiConfig = require('../../config/api')

Page({
  data: {
    // 客户数据
    allCustomers: [],
    customers: [],
    
    // 加载状态
    isLoading: true,
    errorMessage: '',
    
    // 搜索和筛选
    searchValue: '',
    filterOptions: {
      gender: '',
      memberLevel: '',
      store: ''
    },
    
    // 下拉刷新
    isRefreshing: false,
    
    // 选项数据
    genderOptions: ['全部', '女', '男', '未知'],
    levelOptions: ['全部', '标准会员', '银卡会员', '金卡会员', '钻石会员', 'VIP会员'],
    storeOptions: ['全部', '总店', '分店A', '分店B', '分店C', '其他'],
    
    // 是否显示筛选面板
    showFilterPanel: false
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    this.logger.info('客户列表页面已加载');
    
    // 加载客户数据
    this.loadCustomerData();
  },
  
  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadCustomerData(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },
  
  /**
   * 加载客户数据
   */
  loadCustomerData(callback) {
    const that = this;
    const url = apiConfig.getUrl(apiConfig.paths.customer.list);
    
    this.logger.info('开始加载客户数据', { url });
    
    this.setData({ loading: true, errorMessage: '' });
    
    wx.request({
      url: url,
      method: 'GET',
      timeout: 10000, // 设置10秒超时
      enableHttp2: false, // 禁用HTTP/2
      enableQuic: false, // 禁用QUIC
      success: function(res) {
        that.logger.info('收到服务器响应', { 
          statusCode: res.statusCode,
          data: res.data && res.data.items ? `${res.data.items.length}条记录` : '无数据'
        });
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          that.logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            that.logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                that.logger.info(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode === 200) {
                  // 处理重定向后的成功响应
                  const customers = redirectRes.data && redirectRes.data.items ? redirectRes.data.items : [];
                  that.logger.info(`从重定向API加载了${customers.length}位客户`);
                  
                  // 确保客户ID存在
                  const processedCustomers = customers.map(item => ({
                    ...item,
                    id: item.id || item.customerId // 确保id字段存在
                  }));
                  
                  // 更新到本地存储
                  that.dataStore.saveData({
                    customers: processedCustomers,
                    consumptions: []
                  }, false);
                  
                  that.setData({
                    allCustomers: processedCustomers,
                    customers: processedCustomers,
                    loading: false,
                    isEmpty: processedCustomers.length === 0
                  });
                  
                  // 应用当前的搜索和筛选
                  that.applySearchAndFilter();
                } else {
                  that.logger.error('重定向请求失败', { 
                    statusCode: redirectRes.statusCode,
                    data: redirectRes.data 
                  });
                  that.setData({ 
                    loading: false,
                    isEmpty: true,
                    errorMessage: '加载失败：' + (redirectRes.data && redirectRes.data.error ? redirectRes.data.error : '重定向请求失败')
                  });
                }
              },
              fail: (redirectErr) => {
                that.logger.error('重定向请求错误', redirectErr);
                that.setData({ 
                  loading: false,
                  isEmpty: true,
                  errorMessage: '重定向请求错误'
                });
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        if (res.statusCode === 200) {
          // 正确处理返回的数据格式：{items: [...]}
          const customers = res.data && res.data.items ? res.data.items : [];
          that.logger.info(`从API加载了${customers.length}位客户`);
          
          // 确保客户ID存在
          const processedCustomers = customers.map(item => ({
            ...item,
            id: item.id || item.customerId // 确保id字段存在
          }));
          
          // 更新到本地存储
          that.dataStore.saveData({
            customers: processedCustomers,
            consumptions: []
          }, false);
          
          that.setData({
            allCustomers: processedCustomers,
            customers: processedCustomers,
            loading: false,
            isEmpty: processedCustomers.length === 0
          });
          
          // 应用当前的搜索和筛选
          that.applySearchAndFilter();
        } else {
          that.logger.error('请求失败', { 
            statusCode: res.statusCode,
            data: res.data 
          });
          that.setData({ 
            loading: false,
            isEmpty: true,
            errorMessage: '加载失败：' + (res.data && res.data.error ? res.data.error : '未知错误')
          });
        }
        
        if (callback && typeof callback === 'function') {
          callback();
        }
      },
      fail: function(err) {
        that.logger.error('请求客户数据失败', err);
        
        // 尝试从本地存储加载
        const localData = that.dataStore.getData();
        if (localData && localData.customers && localData.customers.length > 0) {
          that.logger.info('从本地缓存加载客户数据', { count: localData.customers.length });
          that.setData({
            allCustomers: localData.customers,
            customers: localData.customers,
            loading: false,
            errorMessage: '网络请求失败，显示本地缓存数据'
          });
          that.applySearchAndFilter();
          return;
        }
        
        // 显示具体的错误信息
        let errorMsg = '网络请求失败';
        if (err.errMsg.includes('timeout')) {
          errorMsg = '请求超时，请检查网络连接';
        } else if (err.errMsg.includes('fail')) {
          errorMsg = '无法连接到服务器，请确认服务器地址是否正确';
        }
        
        that.setData({
          loading: false,
          isEmpty: true,
          errorMessage: errorMsg
        });
        
        // 显示错误提示
        wx.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 2000
        });
        
        if (callback && typeof callback === 'function') {
          callback();
        }
      }
    });
  },

  /**
   * 从本地存储加载客户数据（作为备用）
   */
  loadFromLocalStorage() {
    try {
      // 获取所有客户
      const customers = this.dataStore.getAllCustomers().map(item => ({
        ...item,
        id: item.id || item.customerId // 确保id字段存在
      }));
      
      this.logger.info(`从本地存储加载了${customers.length}位客户`);
      
      this.setData({
        allCustomers: customers,
        customers: customers,
        isLoading: false
      });
      
      // 应用当前的搜索和筛选
      this.applySearchAndFilter();
    } catch (error) {
      this.logger.error('加载本地客户数据失败', error);
      
      this.setData({
        isLoading: false,
        errorMessage: '加载客户数据失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 搜索客户
   */
  searchCustomer(e) {
    const value = e.detail.value;
    this.setData({ searchValue: value });
    this.applySearchAndFilter();
  },
  
  /**
   * 切换筛选面板
   */
  toggleFilterPanel() {
    this.setData({
      showFilterPanel: !this.data.showFilterPanel
    });
  },
  
  /**
   * 应用筛选
   */
  applyFilter(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    // 获取选项值
    let selectedValue = '';
    if (field === 'gender') {
      selectedValue = this.data.genderOptions[value] === '全部' ? '' : this.data.genderOptions[value];
    } else if (field === 'memberLevel') {
      selectedValue = this.data.levelOptions[value] === '全部' ? '' : this.data.levelOptions[value];
    } else if (field === 'store') {
      selectedValue = this.data.storeOptions[value] === '全部' ? '' : this.data.storeOptions[value];
    }
    
    this.setData({
      [`filterOptions.${field}`]: selectedValue
    });
    
    this.applySearchAndFilter();
  },
  
  /**
   * 重置筛选
   */
  resetFilter() {
    this.setData({
      filterOptions: {
        gender: '',
        memberLevel: '',
        store: ''
      }
    });
    
    this.applySearchAndFilter();
  },
  
  /**
   * 应用搜索和筛选
   */
  applySearchAndFilter() {
    const { searchValue, filterOptions, allCustomers } = this.data;
    
    // 筛选客户
    let filteredCustomers = allCustomers;
    
    // 应用搜索
    if (searchValue) {
      const lowerSearchValue = searchValue.toLowerCase();
      filteredCustomers = filteredCustomers.filter(customer => {
        return (
          (customer.name && customer.name.toLowerCase().includes(lowerSearchValue)) ||
          (customer.phone && customer.phone.includes(searchValue))
        );
      });
    }
    
    // 应用筛选
    if (filterOptions.gender) {
      filteredCustomers = filteredCustomers.filter(customer => customer.gender === filterOptions.gender);
    }
    
    if (filterOptions.memberLevel) {
      filteredCustomers = filteredCustomers.filter(customer => customer.memberLevel === filterOptions.memberLevel);
    }
    
    if (filterOptions.store) {
      filteredCustomers = filteredCustomers.filter(customer => customer.store === filterOptions.store);
    }
    
    this.setData({ customers: filteredCustomers });
  },
  
  /**
   * 查看客户详情
   */
  viewCustomerDetail(e) {
    const customerId = e.currentTarget.dataset.id;
    if (!customerId) {
      this.logger.error('未找到客户ID');
      return;
    }
    
    wx.navigateTo({
      url: `/pages/customer/detail?id=${customerId}`,
      fail: (err) => {
        this.logger.error('跳转客户详情页失败', err);
        wx.showToast({
          title: '页面跳转失败',
          icon: 'none'
        });
      }
    });
  },

  /**
   * 编辑客户
   */
  editCustomer(e) {
    const customerId = e.currentTarget.dataset.id;
    if (!customerId) {
      this.logger.error('未找到客户ID');
      return;
    }
    
    wx.navigateTo({
      url: `/pages/customer/edit?id=${customerId}`,
      fail: (err) => {
        this.logger.error('跳转编辑页面失败', err);
        wx.showToast({
          title: '页面跳转失败',
          icon: 'none'
        });
      }
    });
  },

  /**
   * 删除客户
   */
  deleteCustomer(e) {
    const customerId = e.currentTarget.dataset.id;
    if (!customerId) {
      this.logger.error('未找到客户ID');
      return;
    }
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这位客户吗？此操作不可恢复。',
      success: (res) => {
        if (res.confirm) {
          // 调用删除API
          wx.request({
            url: apiConfig.getUrl(apiConfig.paths.customer.delete(customerId)),
            method: 'DELETE',
            success: (res) => {
              if (res.statusCode === 200) {
                this.logger.info('客户删除成功');
                
                // 从本地数据中移除
                const newAllCustomers = this.data.allCustomers.filter(c => c.id !== customerId);
                this.setData({
                  allCustomers: newAllCustomers
                });
                
                // 重新应用筛选
                this.applySearchAndFilter();
                
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
              } else {
                this.logger.error('删除客户失败', res);
                wx.showToast({
                  title: '删除失败',
                  icon: 'none'
                });
              }
            },
            fail: (err) => {
              this.logger.error('请求删除客户失败', err);
              wx.showToast({
                title: '网络错误',
                icon: 'none'
              });
            }
          });
        }
      }
    });
  },

  /**
   * 返回首页
   */
  goToHome() {
    wx.navigateBack();
  },

  /**
   * 新增客户
   */
  addNewCustomer() {
    wx.navigateTo({
      url: '/pages/customer/add',
      fail: (err) => {
        this.logger.error('跳转新增页面失败', err);
        wx.showToast({
          title: '页面跳转失败',
          icon: 'none'
        });
      }
    });
  }
});