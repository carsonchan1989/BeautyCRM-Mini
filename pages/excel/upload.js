// pages/excel/upload.js
// 用于Excel文件上传和处理的页面逻辑

const excelImport = require('../../utils/excel_import_fixed');

Page({
  data: {
    selectedFile: null,
    fileInfo: null,
    importStatus: '',
    importResult: null,
    errorMessage: '',
    isPreviewMode: false,
    previewData: null
  },

  onLoad: function () {
    this.setData({
      importStatus: '准备导入',
      errorMessage: ''
    });
  },

  // 选择Excel文件
  selectExcelFile: function () {
    const that = this;
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'xls'],
      success: function (res) {
        const file = res.tempFiles[0];
        
        // 检查文件大小 (限制为10MB)
        if (file.size > 10 * 1024 * 1024) {
          that.setData({
            errorMessage: '文件过大，请选择10MB以内的文件'
          });
          return;
        }
        
        // 更新文件信息
        that.setData({
          selectedFile: file,
          fileInfo: {
            name: file.name,
            size: (file.size / 1024).toFixed(2) + 'KB',
            time: new Date().toLocaleString()
          },
          importStatus: '已选择文件',
          errorMessage: '',
          isPreviewMode: false,
          previewData: null
        });
      },
      fail: function (err) {
        console.error('选择文件失败:', err);
      }
    });
  },

  // 预览Excel文件内容
  previewExcel: function () {
    if (!this.data.selectedFile) {
      this.setData({
        errorMessage: '请先选择Excel文件'
      });
      return;
    }

    const that = this;
    this.setData({
      importStatus: '预览中...',
      errorMessage: ''
    });

    // 调用修复版的预览方法
    excelImport.previewExcelData(this.data.selectedFile)
      .then(previewData => {
        that.setData({
          importStatus: '预览完成',
          isPreviewMode: true,
          previewData: previewData
        });
      })
      .catch(error => {
        that.setData({
          importStatus: '预览失败',
          errorMessage: error.message || '预览文件时出错'
        });
      });
  },

  // 开始导入Excel数据
  startImport: function () {
    if (!this.data.selectedFile) {
      this.setData({
        errorMessage: '请先选择Excel文件'
      });
      return;
    }

    const that = this;
    this.setData({
      importStatus: '导入中...',
      errorMessage: ''
    });

    // 显示加载提示
    wx.showLoading({
      title: '导入中...',
      mask: true
    });

    // 调用修复版的导入方法
    excelImport.importExcelData(this.data.selectedFile)
      .then(result => {
        wx.hideLoading();
        that.setData({
          importStatus: '导入完成',
          importResult: result,
          errorMessage: ''
        });
        
        // 显示成功提示
        wx.showToast({
          title: '导入成功',
          icon: 'success',
          duration: 2000
        });
        
        // 2秒后跳转到客户列表页
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/customer/list'
          });
        }, 2000);
      })
      .catch(error => {
        wx.hideLoading();
        that.setData({
          importStatus: '导入失败',
          errorMessage: error.message || 'Excel处理失败'
        });
        
        console.error('导入失败详情:', error);
        
        // 显示失败提示
        wx.showModal({
          title: '导入失败',
          content: error.message || 'Excel处理失败，请检查文件格式或联系技术支持',
          showCancel: false
        });
      });
  },

  // 返回上一页
  goBack: function () {
    wx.navigateBack();
  }
});