// pages/report/detail.js
const Logger = require('../../utils/logger')
const ReportGenerator = require('../../utils/reportGenerator')
const DataStore = require('../../utils/dataStore')

Page({
  data: {
    // 报告数据
    customerId: '',
    customer: null,
    report: null,
    reportDate: '',
    
    // 页面状态
    isLoading: true,
    errorMessage: ''
  },
  
  onLoad(options) {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ logger: this.logger });
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 获取参数
    const customerId = options.id;
    const reportDate = options.date || null; // 如果提供日期，则查看指定日期的报告
    
    if (!customerId) {
      this.setData({
        isLoading: false,
        errorMessage: '缺少客户ID参数'
      });
      return;
    }
    
    this.setData({ 
      customerId: customerId,
      reportDate: reportDate
    });
    
    // 加载报告数据
    this.loadReportData(customerId, reportDate);
  },
  
  /**
   * 加载报告数据
   */
  loadReportData(customerId, reportDate) {
    try {
      // 获取客户信息
      const customer = this.dataStore.getCustomerById(customerId);
      if (!customer) {
        this.setData({
          isLoading: false,
          errorMessage: '未找到该客户信息'
        });
        return;
      }
      
      // 获取报告
      const reportData = this.reportGenerator.getCustomerReport(customerId, reportDate);
      if (!reportData) {
        this.setData({
          isLoading: false,
          errorMessage: '未找到该客户的分析报告'
        });
        return;
      }
      
      this.logger.info('成功加载客户报告', {
        customerId: customerId,
        reportDate: reportData.date
      });
      
      // 处理报告内容，将文本分段
      const reportContent = reportData.report.split('\n\n').filter(paragraph => paragraph.trim() !== '');
      
      this.setData({
        customer: customer,
        report: {
          ...reportData,
          content: reportContent
        },
        reportDate: reportData.date,
        isLoading: false
      });
    } catch (error) {
      this.logger.error('加载报告数据失败', error);
      
      this.setData({
        isLoading: false,
        errorMessage: '加载报告数据失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 分享报告
   */
  shareReport() {
    if (!this.data.report) return;
    
    wx.showActionSheet({
      itemList: ['复制到剪贴板', '保存为图片'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 复制到剪贴板
          wx.setClipboardData({
            data: this.data.report.report,
            success: () => {
              wx.showToast({
                title: '报告已复制',
                icon: 'success'
              });
            }
          });
        } else if (res.tapIndex === 1) {
          // 保存为图片（这里仅做示例，实际需要canvas绘制）
          wx.showToast({
            title: '暂不支持',
            icon: 'none'
          });
        }
      }
    });
  },
  
  /**
   * 返回上一页
   */
  goBack() {
    wx.navigateBack();
  },
  
  /**
   * 重新生成报告
   */
  regenerateReport() {
    if (!this.data.customerId) return;
    
    wx.showModal({
      title: '确认重新生成',
      content: '确定要重新生成此客户的分析报告吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: `/pages/report/create?id=${this.data.customerId}`
          });
        }
      }
    });
  }
});