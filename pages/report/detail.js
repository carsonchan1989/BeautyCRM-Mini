// pages/report/detail.js
const Logger = require('../../utils/logger')
const ReportGenerator = require('../../utils/reportGenerator')
const DataStore = require('../../utils/dataStore')
const apiConfig = require('../../config/api');

Page({
  data: {
    // 报告数据
    customerId: '',
    customer: null,
    report: null,
    reportDate: '',
    htmlContent: '',  // HTML格式的报告内容
    
    // 页面状态
    isLoading: true,
    errorMessage: '',
    isHtmlFormat: false
  },
  
  onLoad(options) {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('报告详情页参数', options); // 增加日志记录
    
    // 初始化ReportGenerator
    this.reportGenerator = new ReportGenerator({ logger: this.logger });
    
    // 初始化DataStore
    this.dataStore = new DataStore({ logger: this.logger });
    
    // 获取参数
    const customerId = options.customerId || options.id; // 同时支持两种参数名
    const reportDate = options.reportDate || options.date || null; // 如果提供日期，则查看指定日期的报告
    const forceRefresh = options.forceRefresh === 'true'; // 是否强制刷新
    const isHtmlFormat = options.format === 'html'; // 是否为HTML格式
    
    this.logger.info('处理后的参数', { 
      customerId, 
      reportDate, 
      forceRefresh, 
      isHtmlFormat 
    });
    
    if (!customerId) {
      this.setData({
        isLoading: false,
        errorMessage: '缺少客户ID参数'
      });
      return;
    }
    
    this.setData({ 
      customerId: customerId,
      reportDate: reportDate || this.formatDate(new Date()),
      isHtmlFormat: isHtmlFormat
    });
    
    // 加载报告数据
    this.loadReportData(customerId, reportDate, forceRefresh, isHtmlFormat);
  },
  
  /**
   * 格式化日期为YYYY-MM-DD格式
   */
  formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },
  
  /**
   * 加载报告数据
   */
  loadReportData(customerId, reportDate, forceRefresh = false, isHtmlFormat = false) {
    try {
      this.setData({ isLoading: true });
      
      // 如果不是强制刷新，尝试加载现有报告
      if (!forceRefresh) {
        if (isHtmlFormat) {
          // 尝试加载HTML格式报告
          this.loadHtmlReport(customerId, reportDate);
        } else {
          // 尝试加载传统格式报告
          const reportData = this.reportGenerator.getCustomerReport(customerId, reportDate);
          if (reportData) {
            this.loadCustomerInfo(customerId, null, reportData);
            return;
          }
        }
      }
      
      // 如果强制刷新或没有找到报告，则从API获取报告
      if (!isHtmlFormat) {
        this.loadCustomerInfo(customerId, null);
      }
      
    } catch (error) {
      this.logger.error('加载报告数据失败', error);
      
      this.setData({
        isLoading: false,
        errorMessage: '加载报告数据失败: ' + (error.message || '未知错误')
      });
    }
  },
  
  /**
   * 加载HTML报告
   */
  loadHtmlReport(customerId, reportDate) {
    try {
      // 构建存储键名
      const htmlKey = reportDate 
        ? `html_report_${customerId}_${reportDate}` 
        : `html_report_${customerId}_latest`;
        
      const htmlContent = wx.getStorageSync(htmlKey);
      
      if (htmlContent) {
        this.logger.info('从本地存储加载HTML报告成功', { customerId, reportDate });
        
        // 处理HTML内容，确保可以正确渲染
        const processedHtml = this._processHtmlContent(htmlContent);
        
        // 加载客户基本信息，并设置HTML内容
        this.loadCustomerInfo(customerId, processedHtml);
        return true;
      }
      
      return false;
    } catch (error) {
      this.logger.error('加载HTML报告失败', error);
      return false;
    }
  },
  
  /**
   * 处理HTML内容，使其正确渲染
   * @param {String} html 原始HTML内容
   * @returns {String} 处理后的HTML内容
   * @private
   */
  _processHtmlContent(html) {
    if (!html) return '';
    
    // 处理可能的HTML字符串，移除多余的转义字符
    let processedHtml = html
      .replace(/\\"/g, '"')
      .replace(/\\n/g, '')
      .replace(/\\t/g, '');
      
    // 如果HTML内容是纯文本，添加基本HTML结构
    if (!processedHtml.includes('<')) {
      processedHtml = `<div style="font-size:28rpx;line-height:1.6;">${processedHtml}</div>`;
    }
    
    // 添加基本样式以确保正确显示
    if (!processedHtml.includes('<style>')) {
      processedHtml = `
        <style>
          body { font-size: 28rpx; line-height: 1.6; color: #333; }
          h1, h2, h3, h4 { margin: 20rpx 0; }
          p { margin: 10rpx 0; }
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ddd; padding: 8rpx; }
          th { background-color: #f2f2f2; }
        </style>
        ${processedHtml}
      `;
    }
    
    return processedHtml;
  },
  
  /**
   * 加载客户基本信息
   */
  loadCustomerInfo(customerId, htmlContent, reportData = null) {
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.customer.detail(customerId)),
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200) {
          const customer = res.data;
          
          if (htmlContent) {
            // 如果已有HTML内容，直接设置
            this.setData({
              customer: customer,
              htmlContent: htmlContent,
              isLoading: false
            });
          } else if (reportData) {
            // 如果已有报告数据，直接设置
            this.setData({
              customer: customer,
              report: reportData,
              isLoading: false
            });
          } else {
            // 获取消费记录，准备生成新报告
            this.loadCustomerConsumptions(customer);
          }
        } else {
          this.setData({
            isLoading: false,
            errorMessage: '获取客户信息失败'
          });
        }
      },
      fail: (err) => {
        this.logger.error('获取客户信息失败', err);
        this.setData({
          isLoading: false,
          errorMessage: '网络请求失败'
        });
      }
    });
  },
  
  /**
   * 加载客户消费记录
   */
  loadCustomerConsumptions(customer) {
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.service.list) + `?customer_id=${customer.id}`,
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          const consumptions = res.data.data.rows || [];
          
          // 尝试从报告生成器获取报告
          const reportData = this.reportGenerator.getCustomerReport(customer.id);
          
          if (reportData) {
            this.setData({
              customer: customer,
              report: reportData,
              isLoading: false
            });
          } else {
            // 如果没有现成的报告，自动生成新报告
            this.generateNewReport(customer, consumptions);
          }
        } else {
          this.setData({
            customer: customer,
            isLoading: false,
            errorMessage: '获取消费记录失败'
          });
        }
      },
      fail: (err) => {
        this.logger.error('获取消费记录失败', err);
        this.setData({
          customer: customer,
          isLoading: false,
          errorMessage: '网络请求失败'
        });
      }
    });
  },
  
  /**
   * 生成新的报告
   */
  generateNewReport(customer, consumptions) {
    this.setData({
      isLoading: true,
      errorMessage: ''
    });
    
    this.logger.info('开始生成新报告', { customerId: customer.id });
    
    this.reportGenerator.generateReport(customer, consumptions)
      .then(result => {
        // 保存最新的报告到本地存储
        const currentDate = this.formatDate(new Date());
        
        // 根据返回的结果类型处理
        if (typeof result === 'object' && result.html) {
          // 返回了HTML内容
          const htmlContent = result.html;
          
          // 存储HTML报告
          const dateKey = `html_report_${customer.id}_${currentDate}`;
          const latestKey = `html_report_${customer.id}_latest`;
          
          wx.setStorageSync(dateKey, htmlContent);
          wx.setStorageSync(latestKey, htmlContent);
          
          this.setData({
            customer: customer,
            htmlContent: htmlContent,
            reportDate: currentDate,
            isLoading: false
          });
        } else {
          // 传统报告格式
          this.setData({
            customer: customer,
            report: result,
            reportDate: currentDate,
            isLoading: false
          });
        }
      })
      .catch(error => {
        this.logger.error('生成报告失败', error);
        
        this.setData({
          customer: customer,
          isLoading: false,
          errorMessage: '生成报告失败: ' + (error.message || '未知错误')
        });
      });
  },
  
  /**
   * 分享报告
   */
  shareReport() {
    if (!this.data.report && !this.data.htmlContent) return;
    
    wx.showActionSheet({
      itemList: ['复制到剪贴板', '保存为图片'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 复制到剪贴板
          const content = this.data.htmlContent || 
            (this.data.report ? this.data.report.report : '');
            
          wx.setClipboardData({
            data: content,
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
            url: `/pages/report/create?id=${this.data.customerId}&forceRefresh=true`
          });
        }
      }
    });
  }
});