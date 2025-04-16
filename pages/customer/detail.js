const app = getApp();
const apiConfig = require('../../config/api');

Page({
  data: {
    customerId: '',
    customer: null,
    activeTab: 'basic',
    healthData: null,
    consumptionData: [],
    serviceData: [],
    communicationData: [],
    loading: true,
    tabList: [
      { id: 'basic', name: '基本信息' },
      { id: 'health', name: '健康档案' },
      { id: 'consumption', name: '消费记录' },
      { id: 'service', name: '服务记录' },
      { id: 'communication', name: '沟通记录' }
    ]
  },

  onLoad: function(options) {
    if (options.id) {
      this.setData({
        customerId: options.id,
        loading: true
      });
      this.loadCustomerData();
    } else {
      wx.showToast({
        title: '客户ID缺失',
        icon: 'error'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  // 加载客户所有数据
  loadCustomerData: function() {
    wx.showLoading({
      title: '加载中...',
    });

    // 获取客户基本信息
    this.getCustomerDetail();
  },

  // 获取客户基本信息
  getCustomerDetail: function() {
    const that = this;
    console.log("请求客户详情URL:", apiConfig.getUrl(apiConfig.paths.customer.detail(this.data.customerId)));
    
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.detail(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        console.log("客户详情API返回:", res.data);
        
        if (res.statusCode === 200) {
          // 添加处理以适应不同的API响应格式
          let customerData = res.data;
          
          // 如果API返回的是带有code/data的封装格式
          if (res.data.code === 0 && res.data.data) {
            customerData = res.data.data;
          }
          
          that.setData({
            customer: customerData,
            loading: false
          });
          
          // 继续加载其他数据
          that.getHealthData();
          that.getConsumptionData();
          that.getServiceData();
          that.getCommunicationData();
        } else {
          wx.showToast({
            title: '客户数据加载失败',
            icon: 'none'
          });
          that.setData({
            loading: false
          });
        }
      },
      fail: function(err) {
        console.error('获取客户详情失败:', err);
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        });
        that.setData({
          loading: false
        });
      },
      complete: function() {
        wx.hideLoading();
      }
    });
  },

  // 获取健康档案数据
  getHealthData: function() {
    const that = this;
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.health(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        console.log("健康档案API返回:", res.data);
        
        if (res.statusCode === 200) {
          let healthData = res.data;
          
          // 确保健康数据正确处理 - 取第一条数据
          if (Array.isArray(healthData) && healthData.length > 0) {
            that.setData({
              healthData: healthData[0]
            });
          } else if (healthData && healthData.items && Array.isArray(healthData.items) && healthData.items.length > 0) {
            that.setData({
              healthData: healthData.items[0]
            });
          } else {
            that.setData({
              healthData: null
            });
          }
        } else {
          console.error('获取健康档案失败:', res.data);
        }
      },
      fail: function(err) {
        console.error('获取健康档案失败:', err);
      }
    });
  },

  // 获取消费记录
  getConsumptionData: function() {
    const that = this;
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.consumption(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        console.log("消费记录API返回:", res.data);
        
        if (res.statusCode === 200) {
          let consumptionData = res.data;
          
          // 处理不同格式的响应
          if (Array.isArray(consumptionData)) {
            that.setData({
              consumptionData: consumptionData
            });
          } else if (consumptionData && consumptionData.items && Array.isArray(consumptionData.items)) {
            that.setData({
              consumptionData: consumptionData.items
            });
          } else {
            that.setData({
              consumptionData: []
            });
          }
        } else {
          console.error('获取消费记录失败:', res.data);
        }
      },
      fail: function(err) {
        console.error('获取消费记录失败:', err);
      }
    });
  },

  // 获取服务记录
  getServiceData: function() {
    const that = this;
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.service(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        console.log("服务记录API返回:", res.data);
        
        if (res.statusCode === 200) {
          let serviceData = res.data;
          
          // 处理不同格式的响应
          if (Array.isArray(serviceData)) {
            that.setData({
              serviceData: serviceData
            });
          } else if (serviceData && serviceData.items && Array.isArray(serviceData.items)) {
            that.setData({
              serviceData: serviceData.items
            });
          } else {
            that.setData({
              serviceData: []
            });
          }
        } else {
          console.error('获取服务记录失败:', res.data);
        }
      },
      fail: function(err) {
        console.error('获取服务记录失败:', err);
      }
    });
  },

  // 获取沟通记录
  getCommunicationData: function() {
    const that = this;
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.communication(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        console.log("沟通记录API返回:", res.data);
        
        if (res.statusCode === 200) {
          let communicationData = res.data;
          
          // 处理不同格式的响应
          if (Array.isArray(communicationData)) {
            that.setData({
              communicationData: communicationData
            });
          } else if (communicationData && communicationData.items && Array.isArray(communicationData.items)) {
            that.setData({
              communicationData: communicationData.items
            });
          } else {
            that.setData({
              communicationData: []
            });
          }
        } else {
          console.error('获取沟通记录失败:', res.data);
        }
      },
      fail: function(err) {
        console.error('获取沟通记录失败:', err);
      }
    });
  },

  // 切换标签页
  switchTab: function(e) {
    const tabId = e.currentTarget.dataset.id;
    this.setData({
      activeTab: tabId
    });
  },

  // 返回上一页
  goBack: function() {
    wx.navigateBack();
  },

  // 跳转到报告生成页面
  goToReport: function() {
    wx.navigateTo({
      url: `/pages/report/create?customerId=${this.data.customerId}`
    });
  },

  // 编辑客户信息
  editCustomer: function() {
    wx.navigateTo({
      url: `/pages/customer/add?id=${this.data.customerId}&edit=true`
    });
  },

  // 查看服务记录详情
  viewServiceDetail: function(e) {
    const serviceId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/service/detail?id=${serviceId}`
    });
  },

  // 查看沟通记录详情
  viewCommunicationDetail: function(e) {
    const commId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/communication/detail?id=${commId}`
    });
  }
});
