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
      // 先同步所有HTML报告到传统缓存
      this._syncAllHtmlReportsToCache();
      
      // 获取所有传统格式的报告
      const traditionalReports = this.reportGenerator.getAllReports();
      
      // 获取HTML格式的报告
      const htmlReports = this._getHtmlReports();
      
      // 合并两种类型的报告
      const allReports = [...traditionalReports, ...htmlReports];
      
      // 按日期从新到旧排序
      allReports.sort((a, b) => {
        const dateA = a.date ? new Date(a.date) : new Date(0);
        const dateB = b.date ? new Date(b.date) : new Date(0);
        return dateB - dateA;
      });
      
      this.logger.info(`加载了${allReports.length}份报告 (传统:${traditionalReports.length}, HTML:${htmlReports.length})`);
      
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
            customerLevel: customer ? customer.memberLevel : '',
            isHtmlFormat: report.isHtmlFormat || false
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
   * 获取存储中的HTML报告
   * @private
   */
  _getHtmlReports() {
    try {
      const reports = [];
      const keys = wx.getStorageInfoSync().keys;
      
      // 查找所有HTML报告
      for (const key of keys) {
        // HTML报告的键格式：html_report_[customerId]_[date]
        // 或者：html_report_[customerId]_latest
        if (key.startsWith('html_report_')) {
          const parts = key.split('_');
          // 忽略 "latest" 报告，避免重复
          if (parts.length >= 4 && parts[parts.length - 1] !== 'latest') {
            const customerId = parts[2];
            const dateStr = parts.slice(3).join('_');
            
            // 获取HTML内容
            const htmlContent = wx.getStorageSync(key);
            
            if (!htmlContent) continue;
            
            // 提取报告摘要（不含HTML标签）
            let reportSummary = '';
            try {
              reportSummary = htmlContent
                .replace(/\\"/g, '"')
                .replace(/\\n/g, ' ')
                .replace(/\\t/g, ' ')
                .replace(/<[^>]*>/g, ' ')  // 移除HTML标签
                .replace(/\s+/g, ' ')      // 合并多个空格
                .trim();
            } catch (err) {
              reportSummary = '客户分析报告 (HTML格式)';
              this.logger.warn('提取HTML报告摘要失败', { key, error: err });
            }
            
            reports.push({
              key: key,
              customerId: customerId,
              date: dateStr,
              report: reportSummary.substring(0, 300) || '客户分析报告', // 提取摘要用于显示
              html: htmlContent,                       // 保存完整HTML内容
              isHtmlFormat: true
            });
          }
        }
      }
      
      return reports;
    } catch (error) {
      this.logger.error('获取HTML报告失败', error);
      return [];
    }
  },
  
  /**
   * 同步所有HTML报告到传统缓存系统
   * @private
   */
  _syncAllHtmlReportsToCache() {
    try {
      const keys = wx.getStorageInfoSync().keys;
      let syncCount = 0;
      
      // 查找所有HTML报告键
      for (const key of keys) {
        // HTML报告的键格式：html_report_[customerId]_[date]
        // 或者：html_report_[customerId]_latest
        if (key.startsWith('html_report_') && !key.endsWith('_latest')) {
          const parts = key.split('_');
          if (parts.length >= 4) {
            const customerId = parts[2];
            const dateStr = parts.slice(3).join('_');
            
            // 获取HTML内容
            const htmlContent = wx.getStorageSync(key);
            if (htmlContent) {
              // 创建对应的传统报告缓存键
              const reportCacheKey = `customer_${customerId}_${dateStr}`;
              
              // 检查传统缓存中是否已存在该报告
              const existingReport = this.reportGenerator.reportsCache[reportCacheKey];
              if (!existingReport) {
                // 提取报告摘要
                let reportSummary = htmlContent
                  .replace(/<[^>]*>/g, ' ')  // 移除HTML标签
                  .replace(/\s+/g, ' ')      // 合并多个空格
                  .trim()
                  .substring(0, 1000);       // 限制长度
                
                // 添加到传统缓存
                this.reportGenerator.reportsCache[reportCacheKey] = reportSummary;
                syncCount++;
              }
            }
          }
        }
      }
      
      // 如果有同步的报告，保存缓存
      if (syncCount > 0) {
        this.reportGenerator._saveReportsToCache(this.reportGenerator.reportsCache);
        this.logger.info(`已同步 ${syncCount} 份HTML报告到传统缓存`);
      }
    } catch (error) {
      this.logger.error('同步HTML报告到传统缓存失败', error);
    }
  },
  
  /**
   * 查看报告详情
   */
  viewReportDetail(e) {
    const customerId = e.currentTarget.dataset.id;
    const date = e.currentTarget.dataset.date;
    const isHtml = e.currentTarget.dataset.isHtml;
    
    if (!customerId) return;
    
    // 区分HTML和传统报告的跳转参数
    let url = `/pages/report/detail?id=${customerId}`;
    
    if (date) {
      url += `&date=${date}`;
    }
    
    if (isHtml) {
      url += `&format=html`;
    }
    
    wx.navigateTo({ url });
  },
  
  /**
   * 删除报告
   */
  deleteReport(e) {
    const customerId = e.currentTarget.dataset.id;
    const reportKey = e.currentTarget.dataset.key;
    const isHtml = e.currentTarget.dataset.isHtml;
    
    if (!customerId) return;
    
    wx.showModal({
      title: '删除确认',
      content: '确定要删除这份报告吗？',
      success: (res) => {
        if (res.confirm) {
          if (isHtml && reportKey) {
            // 删除HTML报告
            this._deleteHtmlReport(reportKey, customerId);
          } else {
            // 清除该客户的传统报告缓存
            this.reportGenerator.clearCustomerReportCache(customerId);
          }
          
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
   * 删除HTML报告
   * @param {String} reportKey 报告键名
   * @param {String} customerId 客户ID
   * @private
   */
  _deleteHtmlReport(reportKey, customerId) {
    try {
      // 删除指定的报告
      wx.removeStorageSync(reportKey);
      
      // 检查是否需要删除latest报告
      const latestKey = `html_report_${customerId}_latest`;
      const latestReport = wx.getStorageSync(latestKey);
      
      // 如果latest报告内容与被删除的报告相同，也删除latest
      if (latestReport && this._isLatestReport(reportKey, customerId)) {
        wx.removeStorageSync(latestKey);
      }
      
      this.logger.info('已删除HTML报告', { reportKey });
      
      return true;
    } catch (error) {
      this.logger.error('删除HTML报告失败', error);
      return false;
    }
  },
  
  /**
   * 检查是否是latest报告
   * @param {String} reportKey 报告键名
   * @param {String} customerId 客户ID
   * @returns {Boolean} 是否是latest报告
   * @private
   */
  _isLatestReport(reportKey, customerId) {
    // 获取所有带日期的报告键
    const keys = wx.getStorageInfoSync().keys;
    const dateReportKeys = keys.filter(key => 
      key.startsWith(`html_report_${customerId}_`) && 
      !key.endsWith('_latest')
    );
    
    // 按日期排序
    dateReportKeys.sort((a, b) => {
      const dateA = a.split('_').slice(3).join('_');
      const dateB = b.split('_').slice(3).join('_');
      return new Date(dateB) - new Date(dateA);
    });
    
    // 如果reportKey是最新的报告，返回true
    return dateReportKeys.length > 0 && dateReportKeys[0] === reportKey;
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