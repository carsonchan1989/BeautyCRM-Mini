// service/detail.js - 服务记录详情页

const app = getApp()
const apiConfig = require('../../config/api');

Page({
  data: {
    serviceId: null,
    service: null,
    loading: true
  },

  onLoad: function (options) {
    if (options.id) {
      this.setData({
        serviceId: options.id
      })
      this.loadServiceDetail(options.id)
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  // 加载服务记录详情
  loadServiceDetail: function (serviceId) {
    this.setData({ loading: true })
    
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.service.detail(serviceId)),
      method: 'GET',
      success: (res) => {
        if (res.data && res.data.success) {
          this.setData({
            service: res.data.data
          })
        } else {
          wx.showToast({
            title: '获取服务记录详情失败',
            icon: 'none'
          })
          setTimeout(() => {
            wx.navigateBack()
          }, 1500)
        }
      },
      fail: (err) => {
        console.error('请求服务记录详情失败:', err)
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'none'
        })
      },
      complete: () => {
        this.setData({ loading: false })
      }
    })
  },

  // 编辑服务记录
  editService: function () {
    wx.navigateTo({
      url: `/pages/service/edit?id=${this.data.serviceId}`
    })
  },

  // 删除服务记录
  deleteService: function () {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条服务记录吗？删除后将无法恢复。',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: apiConfig.getUrl(apiConfig.paths.service.delete(this.data.serviceId)),
            method: 'DELETE',
            success: (res) => {
              if (res.data && res.data.success) {
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                })
                setTimeout(() => {
                  wx.navigateBack()
                }, 1500)
              } else {
                wx.showToast({
                  title: res.data.message || '删除失败',
                  icon: 'none'
                })
              }
            },
            fail: (err) => {
              console.error('删除服务记录失败:', err)
              wx.showToast({
                title: '网络错误，请重试',
                icon: 'none'
              })
            }
          })
        }
      }
    })
  },

  // 查看客户详情
  viewCustomer: function () {
    if (this.data.service && this.data.service.customer_id) {
      wx.navigateTo({
        url: `/pages/customer/detail?id=${this.data.service.customer_id}`
      })
    }
  },

  // 返回上一页
  navigateBack: function () {
    wx.navigateBack()
  },
  
  // 复制文本
  copyText: function (e) {
    const text = e.currentTarget.dataset.text
    if (text) {
      wx.setClipboardData({
        data: text,
        success: () => {
          wx.showToast({
            title: '已复制',
            icon: 'success'
          })
        }
      })
    }
  }
})