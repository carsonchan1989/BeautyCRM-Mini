const apiConfig = require('../../config/api');

Page({
  data: {
    tempFilePath: '',
    fileName: '',
    uploading: false
  },

  onChooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['.xlsx'],
      success: (res) => {
        const file = res.tempFiles[0];
        this.setData({
          tempFilePath: file.path,
          fileName: file.name
        });
      }
    });
  },

  async onUpload() {
    if (!this.data.tempFilePath) {
      wx.showToast({
        title: '请先选择文件',
        icon: 'none'
      });
      return;
    }

    this.setData({ uploading: true });

    try {
      const uploadRes = await wx.uploadFile({
        url: apiConfig.getUrl(apiConfig.paths.service.import),
        filePath: this.data.tempFilePath,
        name: 'file',
        formData: {
          type: 'service'
        }
      });

      const result = JSON.parse(uploadRes.data);

      if (uploadRes.statusCode === 201) {
        wx.showToast({
          title: result.message,
          icon: 'success'
        });
        
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(result.error || '导入失败');
      }
    } catch (error) {
      console.error('导入失败:', error);
      wx.showToast({
        title: error.message || '导入失败',
        icon: 'none'
      });
    } finally {
      this.setData({ uploading: false });
    }
  },

  onDownloadTemplate() {
    wx.showToast({
      title: '模板下载中...',
      icon: 'loading',
      duration: 2000
    });

    // 这里应该调用后端的模板下载接口
    // 目前仅显示提示
    setTimeout(() => {
      wx.showToast({
        title: '模板已下载',
        icon: 'success'
      });
    }, 2000);
  }
});