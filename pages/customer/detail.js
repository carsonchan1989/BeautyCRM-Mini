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
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.detail(this.data.customerId)),
      method: 'GET',
      success: function(res) {
        if (res.statusCode === 200) {
          that.setData({
            customer: res.data,
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
        if (res.statusCode === 200) {
          that.setData({
            healthData: Array.isArray(res.data) && res.data.length > 0 ? res.data[0] : null
          });
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
        if (res.statusCode === 200) {
          that.setData({
            consumptionData: Array.isArray(res.data) ? res.data : []
          });
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
        if (res.statusCode === 200) {
          that.setData({
            serviceData: Array.isArray(res.data) ? res.data : []
          });
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
        if (res.statusCode === 200) {
          that.setData({
            communicationData: Array.isArray(res.data) ? res.data : []
          });
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
