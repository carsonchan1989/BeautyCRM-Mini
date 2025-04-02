// pages/excel/import.js
const app = getApp();
const Logger = require('../../utils/logger');
const logger = new Logger('ExcelImport');
const apiConfig = require('../../config/api');
const request = require('../../utils/request');

Page({
  data: {
    uploading: false,
    uploadProgress: 0,
    fileList: [],
    analyzing: false,
    analyzeProgress: 0,
    importResult: null,
    errorMessage: '',
    debugMode: false, // 调试模式
    debugInfo: {}, // 调试信息
    showSettings: false, // 是否显示设置面板
    validSheetNames: [ // 用于匹配的Sheet名称列表
      { label: '客户信息', matches: ['客户', '客户基础信息', '基础信息'] },
      { label: '健康记录', matches: ['健康', '健康档案', '健康与皮肤数据'] },
      { label: '消费记录', matches: ['消费', '消费行为记录', '消费记录'] },
      { label: '服务记录', matches: ['消耗', '消耗行为记录', '服务记录'] },
      { label: '沟通记录', matches: ['沟通', '客户沟通记录', '沟通记录'] }
    ]
  },

  onLoad: function (options) {
    logger.info('Excel导入页面加载');
    
    // 检查是否有调试参数
    if (options.debug === 'true' || options.debug === '1') {
      this.setData({ debugMode: true });
      logger.info('已开启调试模式');
    }
  },

  // 切换调试模式
  toggleDebugMode: function() {
    this.setData({
      debugMode: !this.data.debugMode
    });
    logger.info(this.data.debugMode ? '已开启调试模式' : '已关闭调试模式');
  },

  // 切换设置面板
  toggleSettings: function() {
    this.setData({
      showSettings: !this.data.showSettings
    });
  },

  // 选择Excel文件上传
  chooseExcel: function () {
    logger.info('开始选择Excel文件');

    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'xls'],
      success: (res) => {
        if (res.tempFiles && res.tempFiles.length > 0) {
          const file = res.tempFiles[0];

          // 验证文件类型
          const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
          const isValidType = validTypes.includes(file.type) || file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

          if (!isValidType) {
            this.setData({
              errorMessage: '请选择有效的Excel文件（.xlsx或.xls格式）'
            });
            return;
          }

          // 更新文件列表
          this.setData({
            fileList: [{
              name: file.name,
              size: this._formatFileSize(file.size),
              path: file.path,
              time: new Date().toLocaleString()
            }],
            errorMessage: '',
            debugInfo: { fileName: file.name, fileSize: file.size, filePath: file.path }
          });

          logger.info('已选择文件:', file.name);
        }
      },
      fail: (err) => {
        logger.error('选择文件失败:', err);
        this.setData({
          errorMessage: '选择文件失败：' + (err.errMsg || JSON.stringify(err))
        });
      }
    });
  },

  // 预检查Excel
  preCheckExcel: function() {
    if (this.data.fileList.length === 0) {
      this.setData({
        errorMessage: '请先选择Excel文件'
      });
      return;
    }

    const file = this.data.fileList[0];
    logger.info('开始预检查文件:', file.name);

    this.setData({
      analyzing: true,
      analyzeProgress: 0,
      errorMessage: ''
    });

    // 模拟预检查进度
    const preCheckTimer = setInterval(() => {
      if (this.data.analyzeProgress < 90) {
        this.setData({
          analyzeProgress: this.data.analyzeProgress + 10
        });
      } else {
        clearInterval(preCheckTimer);
      }
    }, 300);

    // 发送预检查请求
    const preCheckUrl = `${app.globalData.apiBaseUrl}/excel/import`;
    
    wx.uploadFile({
      url: preCheckUrl,
      filePath: file.path,
      name: 'file',
      formData: {
        action: 'precheck'
      },
      success: (res) => {
        clearInterval(preCheckTimer);
        this.setData({
          analyzeProgress: 100
        });

        logger.info('文件预检查完成');

        // 处理响应
        try {
          const result = JSON.parse(res.data);
          
          if (this.data.debugMode) {
            this.setData({
              debugInfo: { ...this.data.debugInfo, preCheckResult: result }
            });
          }

          if (res.statusCode === 200) {
            logger.info('文件预检查成功:', result);
            
            setTimeout(() => {
              this.setData({
                analyzing: false,
                importResult: {
                  filename: file.name,
                  preCheckResult: true,
                  sheets: result.sheets || [],
                  stats: result.stats || { totalSheets: result.sheets ? result.sheets.length : 0 },
                  message: '文件格式检查通过，可以导入',
                  time: new Date().toLocaleString()
                }
              });
            }, 500);
          } else {
            logger.error('文件预检查失败:', result);
            this.setData({
              analyzing: false,
              errorMessage: result.error || '文件预检查失败，请检查Excel格式是否符合模板要求'
            });
          }
        } catch (e) {
          logger.error('解析预检查响应失败:', e);
          this.setData({
            analyzing: false,
            errorMessage: '服务器响应解析失败：' + e.message
          });
        }
      },
      fail: (err) => {
        clearInterval(preCheckTimer);
        logger.error('预检查过程失败:', err);
        this.setData({
          analyzing: false,
          errorMessage: '文件预检查失败：' + (err.errMsg || JSON.stringify(err))
        });
      }
    });
  },

  // 上传文件并分析
  uploadAndAnalyze: function () {
    if (this.data.fileList.length === 0) {
      this.setData({
        errorMessage: '请先选择Excel文件'
      });
      return;
    }

    const file = this.data.fileList[0];
    logger.info('开始上传文件:', file.name);

    this.setData({
      uploading: true,
      uploadProgress: 0,
      errorMessage: ''
    });

    // 模拟上传进度
    const uploadTimer = setInterval(() => {
      if (this.data.uploadProgress < 90) {
        this.setData({
          uploadProgress: this.data.uploadProgress + 10
        });
      } else {
        clearInterval(uploadTimer);
      }
    }, 300);

    // 上传文件到服务器
    const importUrl = `${app.globalData.apiBaseUrl}/excel/import`;
    logger.info('上传文件到:', importUrl);

    // 添加调试信息到表单
    const formData = {};
    if (this.data.debugMode) {
      formData.debug = 'true';
    }

    wx.uploadFile({
      url: importUrl,
      filePath: file.path,
      name: 'file',
      formData: formData,
      header: {
        'Content-Type': 'multipart/form-data'
      },
      success: (res) => {
        clearInterval(uploadTimer);
        this.setData({
          uploadProgress: 100
        });

        logger.info('文件上传完成, 状态码:', res.statusCode);
        
        if (this.data.debugMode) {
          this.setData({
            debugInfo: { 
              ...this.data.debugInfo, 
              statusCode: res.statusCode,
              responseHeaders: res.header,
              responseLength: res.data ? res.data.length : 0
            }
          });
        }

        // 处理响应
        try {
          const result = JSON.parse(res.data);
          
          if (this.data.debugMode) {
            this.setData({
              debugInfo: { ...this.data.debugInfo, importResult: result }
            });
          }

          if (res.statusCode === 200) {
            logger.info('文件分析成功:', result);

            // 开始模拟分析过程
            this.setData({
              analyzing: true,
              analyzeProgress: 0
            });

            // 模拟分析进度
            const analyzeTimer = setInterval(() => {
              if (this.data.analyzeProgress < 90) {
                this.setData({
                  analyzeProgress: this.data.analyzeProgress + 10
                });
              } else {
                clearInterval(analyzeTimer);
                this.setData({
                  analyzeProgress: 100,
                  analyzing: false,
                  uploading: false,
                  importResult: {
                    filename: result.filename,
                    stats: result.stats,
                    message: result.message,
                    time: new Date().toLocaleString()
                  }
                });
              }
            }, 200);

          } else {
            logger.error('文件上传失败:', result);
            this.setData({
              uploading: false,
              errorMessage: result.error || '文件上传失败'
            });
          }
        } catch (e) {
          logger.error('解析响应失败:', e, '原始响应:', res.data?.substring(0, 200));
          this.setData({
            uploading: false,
            errorMessage: '服务器响应解析失败：' + e.message
          });
        }
      },
      fail: (err) => {
        clearInterval(uploadTimer);
        logger.error('上传过程失败:', err);
        this.setData({
          uploading: false,
          errorMessage: '文件上传失败：' + (err.errMsg || JSON.stringify(err))
        });
      }
    });
  },

  // 查看数据预览
  viewPreview: function () {
    // 跳转到数据预览页面
    wx.navigateTo({
      url: '/pages/excel/preview',
    });
  },

  // 返回上一页
  goBack: function () {
    wx.navigateBack();
  },

  // 清空选择的文件
  clearFile: function () {
    this.setData({
      fileList: [],
      importResult: null,
      errorMessage: '',
      debugInfo: {}
    });
  },

  // 格式化文件大小
  _formatFileSize: function (size) {
    if (size < 1024) {
      return size + 'B';
    } else if (size < 1024 * 1024) {
      return (size / 1024).toFixed(2) + 'KB';
    } else {
      return (size / (1024 * 1024)).toFixed(2) + 'MB';
    }
  }
});