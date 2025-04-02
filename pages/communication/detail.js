// communication/detail.js - 沟通记录详情页

const app = getApp();
const apiConfig = require('../../config/api');

Page({
  data: {
    commId: null,
    customerId: null,
    communication: null,
    customer: null,
    loading: true
  },

  onLoad: function (options) {
    console.log('Communication detail options:', options);
    if (options.id) {
      this.setData({
        commId: options.id,
        customerId: options.customerId || null
      });
      this.loadCommunicationDetail(options.id);
      
      if (options.customerId) {
        this.loadCustomerInfo(options.customerId);
      }
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  // 加载沟通记录详情
  loadCommunicationDetail: function (commId) {
    this.setData({ loading: true });
    console.log('Loading communication detail for ID:', commId);
    
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.communication.detail(commId)),
      method: 'GET',
      success: (res) => {
        console.log('Communication detail response:', res);
        if (res.statusCode === 200 && res.data) {
          this.setData({
            communication: res.data,
            loading: false
          });
          
          // 如果没有客户ID但有客户记录，加载客户信息
          if (!this.data.customerId && res.data.customer_id) {
            this.loadCustomerInfo(res.data.customer_id);
          }
        } else {
          wx.showToast({
            title: '获取沟通记录详情失败',
            icon: 'none'
          });
          this.setData({ loading: false });
        }
      },
      fail: (err) => {
        console.error('请求沟通记录详情失败:', err);
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'none'
        });
        this.setData({ loading: false });
      }
    });
  },
  
  // 加载客户信息
  loadCustomerInfo: function(customerId) {
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.detail(customerId)),
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({
            customer: res.data
          });
        }
      },
      fail: (err) => {
        console.error('获取客户信息失败:', err);
      }
    });
  },

  // 编辑沟通记录
  editCommunication: function () {
    wx.navigateTo({
      url: `/pages/communication/edit?id=${this.data.commId}`
    });
  },

  // 删除沟通记录
  deleteCommunication: function () {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条沟通记录吗？删除后将无法恢复。',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: apiConfig.getUrl(apiConfig.paths.communication.delete(this.data.commId)),
            method: 'DELETE',
            success: (res) => {
              if (res.statusCode === 200) {
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
                setTimeout(() => {
                  wx.navigateBack();
                }, 1500);
              } else {
                wx.showToast({
                  title: res.data.message || '删除失败',
                  icon: 'none'
                });
              }
            },
            fail: (err) => {
              console.error('删除沟通记录失败:', err);
              wx.showToast({
                title: '网络错误，请重试',
                icon: 'none'
              });
            }
          });
        }
      }
    });
  },

  // 查看客户详情
  viewCustomer: function () {
    const customerId = this.data.customerId || (this.data.communication && this.data.communication.customer_id);
    if (customerId) {
      wx.navigateTo({
        url: `/pages/customer/detail?id=${customerId}`
      });
    }
  },

  // 返回上一页
  navigateBack: function () {
    wx.navigateBack();
  },
  
  // 复制文本
  copyText: function (e) {
    const text = e.currentTarget.dataset.text;
    if (text) {
      wx.setClipboardData({
        data: text,
        success: () => {
          wx.showToast({
            title: '已复制',
            icon: 'success'
          });
        }
      });
    }
  },
  
  // 拨打电话
  makeCall: function (e) {
    const phoneNumber = e.currentTarget.dataset.phone;
    if (phoneNumber) {
      wx.makePhoneCall({
        phoneNumber: phoneNumber
      });
    }
  },
  
  // 新增沟通记录
  addCommunication: function() {
    wx.navigateTo({
      url: `/pages/communication/add?customerId=${this.data.communication.customer_id}`
    });
  }
});