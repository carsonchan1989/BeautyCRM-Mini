// pages/history/history.js
const Logger = require('../../utils/logger')
const ReportGenerator = require('../../utils/reportGenerator')
const DataStore = require('../../utils/dataStore')

Page({
  data: {
    // 报告列表
    reports: [],
    
    // 加载状态
    isLoading: true,
    
    // 错误信息
    errorMessage: ''
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ logger: this.logger });
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 加载报告列表
    this.loadReports();
  },
  
  /**
   * 加载报告列表
   */
  loadReports() {
    this.setData({ isLoading: true });
    
    try {
      // 获取所有报告
      const allReports = this.reportGenerator.getAllReports();
      
      // 如果有报告，为每个报告添加客户信息
      if (allReports.length > 0) {
        // 为每个报告添加客户信息
        const reportsWithCustomer = allReports.map(report => {
          // 获取客户信息
          const customer = this.dataStore.getCustomerById(report.customerId);
          
          return {
            ...report,
            customerName: customer ? customer.name : '未知客户',
            customerGender: customer ? customer.gender : '未知',
            customerAge: customer ? customer.age : '',
            customerLevel: customer ? customer.memberLevel : ''
          };
        });
        
        this.setData({
          reports: reportsWithCustomer,
          isLoading: false
        });
      } else {
        this.setData({
          reports: [],
          isLoading: false
        });
      }
    } catch (error) {
      this.logger.error('加载报告列表失败', error);
      
      this.setData({
        isLoading: false,
        errorMessage: '加载报告列表失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 查看报告详情
   */
  viewReportDetail(e) {
    const customerId = e.currentTarget.dataset.id;
    const date = e.currentTarget.dataset.date;
    
    if (!customerId) return;
    
    wx.navigateTo({
      url: `/pages/report/detail?id=${customerId}&date=${date}`
    });
  },
  
  /**
   * 删除报告
   */
  deleteReport(e) {
    const customerId = e.currentTarget.dataset.id;
    if (!customerId) return;
    
    wx.showModal({
      title: '删除确认',
      content: '确定要删除这份报告吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除该客户的报告缓存
          this.reportGenerator.clearCustomerReportCache(customerId);
          
          // 刷新报告列表
          this.loadReports();
          
          wx.showToast({
            title: '删除成功',
            icon: 'success'
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
   * 生成新报告
   */
  createNewReport() {
    wx.navigateTo({
      url: '/pages/report/report'
    });
  }
});