// service/detail.js - 服务记录详情页

const app = getApp()
const apiConfig = require('../../config/api');

Page({
  data: {
    serviceId: null,
    service: null,
    loading: true,
    errorMessage: null,
    showDebug: false,  // 用于控制调试信息显示
    hasConsumptionRecords: false  // 是否有消耗记录
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
    this.setData({ 
      loading: true,
      errorMessage: null 
    })
    
    console.log("请求服务详情，ID:", serviceId)
    console.log("API URL:", apiConfig.getUrl(apiConfig.paths.service.detail(serviceId)))
    
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.service.detail(serviceId)),
      method: 'GET',
      success: (res) => {
        console.log("服务记录详情API返回数据:", res.data)
        
        if (res.data && (res.data.success || res.statusCode === 200)) {
          // 确保service_items字段存在并且格式化显示数据
          let serviceData = res.data;
          
          // 如果数据在data字段中，获取正确的数据对象
          if (res.data.data) {
            serviceData = res.data.data;
          }
          
          if (!serviceData.service_items) {
            serviceData.service_items = []
            console.warn("服务项目数据不存在，创建空数组")
          } else if (typeof serviceData.service_items === 'string') {
            // 尝试解析可能是字符串的service_items
            try {
              serviceData.service_items = JSON.parse(serviceData.service_items);
            } catch (e) {
              console.error("解析service_items字符串失败:", e);
              serviceData.service_items = [];
            }
          }
          
          // 检查是否有消耗记录
          let hasConsumptionRecords = false;
          if (serviceData.service_items && serviceData.service_items.length > 0) {
            for (let item of serviceData.service_items) {
              if (item.consumed_sessions && item.consumed_sessions.length > 0) {
                hasConsumptionRecords = true;
                break;
              }
            }
          }
          
          // 确保日期时间格式统一，方便显示
          if (serviceData.service_date) {
            // 保持原始格式不变，如果需要可以进行格式化
            console.log("服务日期:", serviceData.service_date)
          }
          
          if (serviceData.departure_time) {
            // 保持原始格式不变，如果需要可以进行格式化
            console.log("离店时间:", serviceData.departure_time)
          }
          
          // 确保每个服务项目的字段名称与模板一致
          serviceData.service_items = serviceData.service_items.map((item, index) => {
            console.log(`处理服务项目 ${index+1}:`, item)
            
            // 预处理金额值，确保是数字
            let amount = item.amount || item.unit_price || 0;
            if (typeof amount === 'string') {
              amount = parseFloat(amount) || 0;
            }
            
            // 预处理卡扣金额
            let cardDeduction = item.card_deduction || 0;
            if (typeof cardDeduction === 'string') {
              cardDeduction = parseFloat(cardDeduction) || 0;
            }
            
            return {
              id: item.id,
              service_id: item.service_id,
              project_id: item.project_id || '',
              service_name: item.service_name || item.project_name, // 优先使用服务端提供的mapped字段
              project_name: item.project_name,
              amount: amount,
              unit_price: item.unit_price || amount,
              card_deduction: cardDeduction,
              quantity: item.quantity || 1,
              beautician: item.beautician || item.beautician_name,
              beautician_name: item.beautician_name || item.beautician,
              is_specified: typeof item.is_specified === 'boolean' ? item.is_specified : Boolean(item.is_specified),
              note: item.note || item.remark || '',
              remark: item.remark || item.note || '',
              is_satisfied: typeof item.is_satisfied === 'boolean' ? item.is_satisfied : true,
              consumed_sessions: item.consumed_sessions || []
            }
          })
          
          // 设置数据
          this.setData({
            service: serviceData,
            showDebug: false, // 默认不显示调试信息
            hasConsumptionRecords: hasConsumptionRecords
          })
          
          console.log("格式化后的服务数据:", this.data.service)
          
          // 临时变量，仅用于调试
          let debugServiceItems = ''
          if (serviceData.service_items && serviceData.service_items.length > 0) {
            debugServiceItems = JSON.stringify(serviceData.service_items[0], null, 2)
          }
          console.log("服务项目明细示例:", debugServiceItems)
        } else {
          // 设置错误信息
          const errorMsg = res.data.message || '获取服务记录详情失败'
          console.error("API返回错误:", errorMsg)
          
          this.setData({
            errorMessage: errorMsg
          })
          
          wx.showToast({
            title: errorMsg,
            icon: 'none'
          })
          
          // 如果服务不存在，延迟返回
          if (res.data.message && res.data.message.includes('不存在')) {
            setTimeout(() => {
              wx.navigateBack()
            }, 2500)
          }
        }
      },
      fail: (err) => {
        const errorMsg = '网络错误，请重试'
        console.error('请求服务记录详情失败:', err)
        
        this.setData({
          errorMessage: errorMsg
        })
        
        wx.showToast({
          title: errorMsg,
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
  },
  
  // 刷新页面数据
  refreshData: function() {
    if (this.data.serviceId) {
      this.loadServiceDetail(this.data.serviceId)
    }
  },
  
  // 切换调试信息显示
  toggleDebug: function() {
    this.setData({
      showDebug: !this.data.showDebug
    })
  },
  
  // 生命周期函数 - 页面重新显示
  onShow: function() {
    // 每次显示页面时刷新数据
    if (this.data.serviceId) {
      this.refreshData()
    }
  }
})