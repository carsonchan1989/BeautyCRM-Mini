// pages/excel/preview.js
const app = getApp();
const Logger = require('../../utils/logger');
const logger = new Logger('ExcelPreview');
const apiConfig = require('../../config/api');

Page({
  data: {
    loading: true,
    dataType: 'customer', // 'customer', 'health', 'consumption', 'service', 'communication'
    dataList: [],
    totalCount: 0,
    currentPage: 1,
    pageSize: 20,
    hasMore: false,
    errorMessage: '',
    serverUrl: app.globalData.apiBaseUrl || 'http://localhost:5000'
  },

  onLoad: function (options) {
    logger.info('Excel预览页面加载');
    this.loadData();
  },

  // 加载数据
  loadData: function () {
    this.setData({
      loading: true,
      errorMessage: ''
    });
    
    // 根据当前选择的数据类型获取数据
    this.fetchData(this.data.dataType);
  },

  // 从服务器获取数据
  fetchData: function (dataType) {
    logger.info(`正在获取${dataType}数据，页码：${this.data.currentPage}`);
    
    wx.showLoading({
      title: '加载中...'
    });
    
    wx.request({
      url: apiConfig.getUrl(`/api/customers`),
      method: 'GET',
      data: {
        page: this.data.currentPage,
        per_page: this.data.pageSize,
        data_type: dataType
      },
      success: (res) => {
        logger.info(`获取数据响应: 状态码 ${res.statusCode}`);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              data: {
                page: this.data.currentPage,
                per_page: this.data.pageSize,
                data_type: dataType
              },
              success: (redirectRes) => {
                logger.info(`重定向请求响应: 状态码 ${redirectRes.statusCode}`);
                if (redirectRes.statusCode === 200) {
                  const items = redirectRes.data.items || [];
                  const total = redirectRes.data.total || 0;
                  
                  logger.info(`数据获取成功: ${items.length}条记录，总计: ${total}`);
                  
                  this.setData({
                    dataList: items,
                    totalCount: total,
                    hasMore: this.data.currentPage * this.data.pageSize < total,
                    loading: false
                  });
                } else {
                  logger.error('重定向后数据获取失败:', redirectRes);
                  this.setData({
                    loading: false,
                    errorMessage: (redirectRes.data && redirectRes.data.error) || '数据加载失败'
                  });
                }
              },
              fail: (redirectErr) => {
                logger.error('重定向请求失败:', redirectErr);
                this.setData({
                  loading: false,
                  errorMessage: '重定向网络请求失败：' + (redirectErr.errMsg || JSON.stringify(redirectErr))
                });
              },
              complete: () => {
                wx.hideLoading();
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        if (res.statusCode === 200) {
          const items = res.data.items || [];
          const total = res.data.total || 0;
          
          logger.info(`数据获取成功: ${items.length}条记录，总计: ${total}`);
          
          this.setData({
            dataList: items,
            totalCount: total,
            hasMore: this.data.currentPage * this.data.pageSize < total,
            loading: false
          });
        } else {
          logger.error('数据获取失败:', res);
          this.setData({
            loading: false,
            errorMessage: (res.data && res.data.error) || '数据加载失败'
          });
        }
      },
      fail: (err) => {
        logger.error('请求失败:', err);
        this.setData({
          loading: false,
          errorMessage: '网络请求失败：' + (err.errMsg || JSON.stringify(err))
        });
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },

  // 切换数据类型
  switchDataType: function (e) {
    const dataType = e.currentTarget.dataset.type;
    logger.info(`切换数据类型到: ${dataType}`);
    
    this.setData({
      dataType: dataType,
      currentPage: 1,
      dataList: []
    });
    
    this.loadData();
  },

  // 加载更多数据
  loadMore: function () {
    if (this.data.hasMore) {
      this.setData({
        currentPage: this.data.currentPage + 1
      });
      this.loadData();
    }
  },

  // 刷新数据
  refreshData: function () {
    this.setData({
      currentPage: 1
    });
    this.loadData();
  },
  
  // 导出Excel文件
  exportExcel: function () {
    logger.info('开始导出Excel数据');
    
    wx.showLoading({
      title: '准备导出...',
    });
    
    wx.request({
      url: apiConfig.getUrl(`/api/excel/export`),
      method: 'POST',
      data: {
        include_sections: [this.data.dataType]
      },
      success: (res) => {
        logger.info(`导出响应: 状态码 ${res.statusCode}`);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          logger.info('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'POST',
              data: {
                include_sections: [this.data.dataType]
              },
              success: (redirectRes) => {
                wx.hideLoading();
                logger.info(`重定向请求响应: 状态码 ${redirectRes.statusCode}`);
                if (redirectRes.statusCode === 200) {
                  logger.info('导出请求成功:', redirectRes.data);
                  
                  wx.showModal({
                    title: '导出成功',
                    content: `Excel文件已导出：${redirectRes.data.filename || '未知文件名'}`,
                    showCancel: false
                  });
                } else {
                  logger.error('重定向后导出失败:', redirectRes.data);
                  
                  wx.showModal({
                    title: '导出失败',
                    content: (redirectRes.data && redirectRes.data.error) || '导出过程中发生错误',
                    showCancel: false
                  });
                }
              },
              fail: (redirectErr) => {
                wx.hideLoading();
                logger.error('重定向请求失败:', redirectErr);
                
                wx.showModal({
                  title: '导出失败',
                  content: '重定向请求失败：' + (redirectErr.errMsg || JSON.stringify(redirectErr)),
                  showCancel: false
                });
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        wx.hideLoading();
        
        if (res.statusCode === 200) {
          logger.info('导出请求成功:', res.data);
          
          wx.showModal({
            title: '导出成功',
            content: `Excel文件已导出：${res.data.filename || '未知文件名'}`,
            showCancel: false
          });
        } else {
          logger.error('导出失败:', res.data);
          
          wx.showModal({
            title: '导出失败',
            content: (res.data && res.data.error) || '导出过程中发生错误',
            showCancel: false
          });
        }
      },
      fail: (err) => {
        wx.hideLoading();
        logger.error('导出请求失败:', err);
        
        wx.showModal({
          title: '导出失败',
          content: '网络请求失败：' + (err.errMsg || JSON.stringify(err)),
          showCancel: false
        });
      }
    });
  },
  
  // 返回上一页
  goBack: function () {
    wx.navigateBack();
  },

  // 查看详细信息
  viewDetail: function (e) {
    const id = e.currentTarget.dataset.id;
    logger.info(`查看详细信息, ID: ${id}`);
    
    // 根据数据类型跳转到不同页面
    if (this.data.dataType === 'customer') {
      wx.navigateTo({
        url: `/pages/customer/detail?id=${id}`
      });
    } else {
      wx.showToast({
        title: '功能开发中',
        icon: 'none'
      });
    }
  }
});