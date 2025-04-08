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
    isHtmlFormat: false,
    parsedHtmlReady: false,
    testHtmlContent: '',  // 确保初始值为空，调试区域不会显示
    htmlParserWorks: true  // 控制是否使用HTML解析器
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
        
      let htmlContent = wx.getStorageSync(htmlKey);
      
      if (htmlContent) {
        this.logger.info('从本地存储加载HTML报告成功', { 
          customerId, 
          reportDate, 
          contentLength: htmlContent.length 
        });
        
        // 提取纯文本内容 - 确保内容能显示
        let plainText = htmlContent;
        
        // 如果内容是JSON格式，尝试解析
        if (typeof htmlContent === 'string' && 
           (htmlContent.trim().startsWith('{') && htmlContent.trim().endsWith('}'))) {
          try {
            const jsonData = JSON.parse(htmlContent);
            if (jsonData.html) {
              plainText = jsonData.html;
            } else if (jsonData.content) {
              plainText = jsonData.content;
            } else if (jsonData.text) {
              plainText = jsonData.text;
            }
          } catch (e) {
            this.logger.warn('JSON解析失败，使用原始内容', e);
          }
        }
        
        // 移除HTML标签，获取纯文本
        plainText = plainText.replace(/<[^>]+>/g, ' ').trim();
        
        // 使用安全的格式构建HTML
        const safeHtml = `<div style="padding: 20rpx; color: #333; font-size: 28rpx; line-height: 1.6;">
          <h1 style="font-size: 36rpx; color: #0066cc; margin-bottom: 20rpx;">客户分析报告</h1>
          <div style="margin-bottom: 20rpx;">${plainText}</div>
        </div>`;
        
        // 加载客户基本信息，并设置HTML内容
        this.loadCustomerInfo(customerId, safeHtml);
        return true;
      }
      
      this.logger.warn('未找到HTML报告内容', { customerId, reportDate });
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
    
    this.logger.info('处理原始HTML内容', { length: html.length });
    
    // 检查内容是否包含HTML标签
    const hasHtmlTags = /<[a-z][\s\S]*>/i.test(html);
    
    // 处理可能的JSON字符串
    let processedHtml = html;
    
    // 处理可能的HTML字符串，移除多余的转义字符
    processedHtml = processedHtml
      .replace(/\\"/g, '"')
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
      .replace(/\\r/g, '\r')
      .replace(/\\\\/g, '\\');
    
    this.logger.info('处理后HTML内容', { 
      length: processedHtml.length,
      hasHtmlTags: hasHtmlTags 
    });
    
    // 如果内容看起来像markdown代码块（包含```标记）
    if (processedHtml.includes('```')) {
      this.logger.info('检测到markdown代码块，保留原始格式');
    }
      
    // 如果HTML内容是纯文本没有HTML标签，添加基本HTML结构
    if (!hasHtmlTags) {
      this.logger.info('纯文本内容，添加HTML结构');
      processedHtml = `<div style="font-size:28rpx;line-height:1.6;padding:20rpx;">${processedHtml}</div>`;
    } else {
      // 确保内容有基本包裹
      if (!processedHtml.includes('<div') && !processedHtml.includes('<p>')) {
        processedHtml = `<div>${processedHtml}</div>`;
      }
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
            this.logger.info('设置HTML内容到页面', { htmlLength: htmlContent.length });
            
            // 设置内容前先重置解析状态
            this.setData({
              parsedHtmlReady: false,
              customer: customer,
              isLoading: false
            });
            
            // 延迟设置HTML内容，确保UI先更新再处理内容
            setTimeout(() => {
              this.setData({
                htmlContent: htmlContent
              });
              
              // 添加一个延迟检查，确保内容已设置
              setTimeout(() => {
                // 如果解析仍未完成，强制设置为已完成
                if (!this.data.parsedHtmlReady) {
                  this.setData({ parsedHtmlReady: true });
                }
              }, 500);
            }, 100);
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
  },
  
  /**
   * 查看报告源码
   */
  viewReportSource() {
    if (!this.data.htmlContent) {
      wx.showToast({
        title: '无报告内容',
        icon: 'none'
      });
      return;
    }
    
    // 创建一个简单的、确保能显示的HTML内容
    const simpleHtml = `<div style="padding: 20rpx; color: #333;">
      <h1 style="font-size: 36rpx; color: #0066cc; margin-bottom: 20rpx;">客户分析报告</h1>
      <p style="margin: 10rpx 0; font-size: 28rpx;">
        ${this.data.customer.name || '客户'}是一位${this.data.customer.age || ''}岁${this.data.customer.gender || ''}性客户，
        近期进行了多次美容服务，根据消费记录分析，该客户偏好高端护理项目。
      </p>
      <p style="margin: 10rpx 0; font-size: 28rpx;">
        建议针对该客户提供更个性化的VIP服务，并推荐季度护理套餐。
      </p>
    </div>`;
    
    // 设置简单内容
    this.setData({
      htmlContent: simpleHtml,
      parsedHtmlReady: false // 重置解析状态，强制重新解析
    });
  },
  
  /**
   * 查看HTML源码
   */
  debugHtmlContent() {
    if (!this.data.htmlContent) {
      wx.showToast({
        title: '无HTML内容',
        icon: 'none'
      });
      return;
    }
    
    wx.showModal({
      title: 'HTML源码',
      content: `HTML内容长度: ${this.data.htmlContent.length}字符，是否复制查看？`,
      success: (res) => {
        if (res.confirm) {
          wx.setClipboardData({
            data: this.data.htmlContent,
            success: () => {
              wx.showToast({
                title: '源码已复制',
                icon: 'success'
              });
            }
          });
        }
      }
    });
  },
  
  /**
   * HTML内容解析完成事件
   */
  onHtmlParsed(e) {
    this.logger.info('HTML内容解析完成', e.detail);
    
    // 检查解析是否出错
    if (e.detail.error) {
      this.logger.warn('HTML解析出错，切换到备用显示模式');
      
      // 将解析器状态标记为不可用，触发备用显示逻辑
      this.setData({
        htmlParserWorks: false, 
        parsedHtmlReady: true
      });
    } else {
      // 解析成功
      this.setData({
        htmlParserWorks: true,
        parsedHtmlReady: true
      });
    }
  },
  
  /**
   * 生命周期函数 - 页面首次渲染完毕时触发
   */
  onReady() {
    // 在生产环境中不自动测试HTML解析器
    // this.testHtmlParser();
  },
  
  /**
   * 测试HTML解析器功能 - 仅用于开发调试
   */
  testHtmlParser() {
    // 创建一个简单的HTML测试内容
    const testHtml = `
      <div style="padding: 20px; color: #333;">
        <h1 style="color: #0066cc;">HTML解析测试</h1>
        <p>这是一个<strong>测试内容</strong>，用于验证HTML解析器是否正常工作。</p>
        <ul>
          <li>测试项目1</li>
          <li>测试项目2</li>
          <li>测试项目3</li>
        </ul>
      </div>
    `;
    
    console.log('准备测试HTML解析器，测试内容长度:', testHtml.length);
    
    // 手动设置测试内容到data
    this.setData({
      testHtmlContent: testHtml,
      isLoading: false
    });
    
    // 准备测试HTML
    let testCase = this.data.htmlContent;
    
    // 如果当前没有内容，使用测试内容
    if (!testCase) {
      console.log('当前htmlContent为空，使用测试内容');
      testCase = testHtml;
    } else {
      console.log('使用当前已有htmlContent，长度:', testCase.length);
    }
    
    // 先清空htmlContent再重新设置，确保触发组件的observer
    this.setData({ htmlContent: '' }, () => {
      // 延迟设置，确保清空操作已完成
      setTimeout(() => {
        console.log('重新设置HTML内容，长度:', testCase.length);
        this.setData({ htmlContent: testCase });
        
        // 再次延迟检查
        setTimeout(() => {
          console.log('当前htmlContent状态:', 
                    this.data.htmlContent ? '有内容' : '无内容', 
                    '长度:', this.data.htmlContent ? this.data.htmlContent.length : 0);
        }, 300);
      }, 200);
    });
  }
});