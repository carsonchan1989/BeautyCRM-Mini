// service/list.js - 服务记录列表页

const app = getApp()

Page({
  data: {
    services: [],
    loading: false,
    totalCount: 0,
    currentPage: 1,
    pageSize: 10,
    searchDate: '',
    showDatePicker: false,
    searchCustomer: '',
    customers: []
  },

  onLoad: function (options) {
    this.loadServices()
    // 如果有customerID参数，则加载特定客户的服务记录
    if (options.customerId) {
      this.setData({
        searchCustomer: options.customerId
      })
      this.loadCustomerServices(options.customerId)
    }
  },

  onShow: function () {
    if (!this.data.searchCustomer) {
      this.loadServices()
    }
  },

  onPullDownRefresh: function () {
    this.loadServices()
    wx.stopPullDownRefresh()
  },

  // 加载服务记录列表
  loadServices: function () {
    const { currentPage, pageSize, searchDate, searchCustomer } = this.data
    
    this.setData({ loading: true })
    
    let url = `${app.globalData.baseUrl}/api/services/list?page=${currentPage}&limit=${pageSize}`
    
    if (searchDate) {
      url += `&start_date=${searchDate}`
    }
    
    if (searchCustomer) {
      url += `&customer_id=${searchCustomer}`
    }
    
    wx.request({
      url: url,
      method: 'GET',
      success: (res) => {
        if (res.data && res.data.success) {
          this.setData({
            services: res.data.data.items,
            totalCount: res.data.data.total
          })
        } else {
          wx.showToast({
            title: '获取服务记录失败',
            icon: 'none'
          })
        }
      },
      fail: (err) => {
        console.error('请求服务记录列表失败:', err)
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

  // 加载特定客户的服务记录
  loadCustomerServices: function (customerId) {
    this.setData({ loading: true })
    
    wx.request({
      url: `${app.globalData.baseUrl}/api/services/customer/${customerId}`,
      method: 'GET',
      success: (res) => {
        if (res.data && res.data.success) {
          this.setData({
            services: res.data.data,
            totalCount: res.data.data.length
          })
        } else {
          wx.showToast({
            title: '获取客户服务记录失败',
            icon: 'none'
          })
        }
      },
      fail: (err) => {
        console.error('请求客户服务记录失败:', err)
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

  // 搜索客户
  searchCustomerByName: function (e) {
    const searchText = e.detail.value
    if (searchText && searchText.length > 1) {
      wx.request({
        url: `${app.globalData.baseUrl}/api/customers/search?keyword=${searchText}`,
        method: 'GET',
        success: (res) => {
          if (res.data && res.data.success) {
            this.setData({
              customers: res.data.data
            })
          }
        }
      })
    } else {
      this.setData({ customers: [] })
    }
  },

  // 选择客户
  selectCustomer: function (e) {
    const customerId = e.currentTarget.dataset.id
    const customerName = e.currentTarget.dataset.name
    
    this.setData({
      searchCustomer: customerId,
      customers: [],
      'searchForm.customerName': customerName
    })
    
    this.loadCustomerServices(customerId)
  },

  // 清除客户筛选
  clearCustomerFilter: function () {
    this.setData({
      searchCustomer: '',
      'searchForm.customerName': '',
      currentPage: 1
    })
    this.loadServices()
  },

  // 显示日期选择器
  showDatePicker: function () {
    this.setData({
      showDatePicker: true
    })
  },

  // 选择日期
  bindDateChange: function (e) {
    this.setData({
      searchDate: e.detail.value,
      showDatePicker: false,
      currentPage: 1
    })
    this.loadServices()
  },

  // 清除日期筛选
  clearDateFilter: function () {
    this.setData({
      searchDate: '',
      currentPage: 1
    })
    this.loadServices()
  },

  // 查看服务详情
  viewServiceDetail: function (e) {
    const serviceId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/service/detail?id=${serviceId}`
    })
  },

  // 添加新服务记录
  addService: function () {
    wx.navigateTo({
      url: '/pages/service/add'
    })
  },

  // 编辑服务记录
  editService: function (e) {
    const serviceId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/service/edit?id=${serviceId}`
    })
    
    // 阻止事件冒泡，防止触发viewServiceDetail
    return false
  },

  // 删除服务记录
  deleteService: function (e) {
    const serviceId = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条服务记录吗？删除后将无法恢复。',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: `${app.globalData.baseUrl}/api/services/${serviceId}`,
            method: 'DELETE',
            success: (res) => {
              if (res.data && res.data.success) {
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                })
                this.loadServices()
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
    
    // 阻止事件冒泡，防止触发viewServiceDetail
    return false
  },

  // 分页处理 - 上一页
  prevPage: function () {
    if (this.data.currentPage > 1) {
      this.setData({
        currentPage: this.data.currentPage - 1
      })
      this.loadServices()
    }
  },

  // 分页处理 - 下一页
  nextPage: function () {
    if (this.data.currentPage * this.data.pageSize < this.data.totalCount) {
      this.setData({
        currentPage: this.data.currentPage + 1
      })
      this.loadServices()
    }
  },

  // 格式化日期时间显示
  formatDateTime: function (dateTimeStr) {
    if (!dateTimeStr) return ''
    const date = new Date(dateTimeStr)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
})