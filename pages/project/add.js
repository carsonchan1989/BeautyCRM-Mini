Page({
  data: {
    projectData: {
      name: '',
      description: '',
      price: '',
      category: '',
      duration: '',
      notes: ''
    },
    categories: ['面部护理', '身体护理', '美容服务', '特色项目'],
    categoryIndex: null,
    // Excel导入相关
    excelFile: null,
    excelFileSize: '',
    previewData: [],
    importMode: 'add_only', // add_only 仅添加新项目, update_existing 更新已有项目, replace_all 替换所有
    importFilePath: '',
    processing: false
  },

  onLoad: function(options) {
    // 如果是Excel导入模式，显示Excel上传区域
    if (options.mode && options.mode === 'excel') {
      wx.pageScrollTo({
        selector: '.excel-upload',
        duration: 300
      });
    }
    
    // 如果是编辑模式，加载项目数据
    if (options.id) {
      this.loadProjectData(options.id);
    }
    
    // 加载项目分类
    this.loadProjectCategories();
  },

  // 加载项目分类
  loadProjectCategories: function() {
    const self = this;
    wx.request({
      url: 'http://localhost:5000/api/projects/categories',
      method: 'GET',
      success: function(res) {
        if (res.data && res.data.success && res.data.data.length > 0) {
          self.setData({
            categories: res.data.data
          });
        }
      }
    });
  },

  // 加载项目数据
  loadProjectData: function(id) {
    const self = this;
    wx.request({
      url: `http://localhost:5000/api/projects/${id}`,
      method: 'GET',
      success: function(res) {
        if (res.data && res.data.success) {
          const projectData = res.data.data;
          const categoryIndex = self.data.categories.indexOf(projectData.category);
          self.setData({
            projectData: projectData,
            categoryIndex: categoryIndex
          });
        }
      }
    });
  },

  // 输入项目名称
  onInputName: function(e) {
    this.setData({
      'projectData.name': e.detail.value
    });
  },

  // 输入项目描述
  onInputDescription: function(e) {
    this.setData({
      'projectData.description': e.detail.value
    });
  },

  // 输入项目价格
  onInputPrice: function(e) {
    this.setData({
      'projectData.price': e.detail.value
    });
  },

  // 选择项目分类
  onCategoryChange: function(e) {
    this.setData({
      categoryIndex: e.detail.value,
      'projectData.category': this.data.categories[e.detail.value]
    });
  },

  // 输入项目时长
  onInputDuration: function(e) {
    this.setData({
      'projectData.duration': e.detail.value
    });
  },

  // 输入注意事项
  onInputNotes: function(e) {
    this.setData({
      'projectData.notes': e.detail.value
    });
  },

  // 保存项目
  saveProject: function() {
    const self = this;
    const projectData = this.data.projectData;

    // 表单验证
    if (!projectData.name) {
      wx.showToast({
        title: '请输入项目名称',
        icon: 'none'
      });
      return;
    }

    if (!projectData.price) {
      wx.showToast({
        title: '请输入项目价格',
        icon: 'none'
      });
      return;
    }

    if (!projectData.category) {
      wx.showToast({
        title: '请选择项目分类',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '保存中...'
    });

    // 发送请求保存项目
    wx.request({
      url: 'http://localhost:5000/api/projects',
      method: 'POST',
      data: projectData,
      success: function(res) {
        if (res.data && res.data.success) {
          wx.showToast({
            title: '保存成功',
            icon: 'success'
          });
          // 返回上一页
          setTimeout(() => {
            wx.navigateBack();
          }, 1500);
        } else {
          wx.showToast({
            title: res.data.message || '保存失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
        console.error('保存项目失败:', err);
      },
      complete: function() {
        wx.hideLoading();
      }
    });
  },

  // 取消编辑
  cancelEdit: function() {
    wx.navigateBack();
  },

  // ========== Excel导入相关功能 ==========
  
  // 选择Excel文件
  chooseExcelFile: function() {
    const self = this;
    
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['.xlsx', '.xls'],
      success: function(res) {
        const file = res.tempFiles[0];
        // 检查是否是Excel文件
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
          wx.showToast({
            title: '请选择Excel文件',
            icon: 'none'
          });
          return;
        }
        
        // 计算文件大小
        let fileSize = '';
        if (file.size < 1024) {
          fileSize = file.size + 'B';
        } else if (file.size < 1024 * 1024) {
          fileSize = (file.size / 1024).toFixed(2) + 'KB';
        } else {
          fileSize = (file.size / (1024 * 1024)).toFixed(2) + 'MB';
        }
        
        self.setData({
          excelFile: file,
          excelFileSize: fileSize,
          previewData: [] // 清空预览数据
        });
      }
    });
  },
  
  // 下载Excel模板
  downloadTemplate: function() {
    wx.showToast({
      title: '获取模板中...',
      icon: 'loading'
    });
    
    // 可以调用后端API获取模板URL，或者直接打开一个预设的网页
    setTimeout(() => {
      wx.showModal({
        title: '模板下载',
        content: '请通过浏览器访问系统网站下载项目导入模板',
        confirmText: '知道了',
        showCancel: false
      });
    }, 1000);
  },
  
  // 预览Excel数据
  previewExcelData: function() {
    if (!this.data.excelFile) {
      wx.showToast({
        title: '请先选择Excel文件',
        icon: 'none'
      });
      return;
    }
    
    const self = this;
    self.setData({
      processing: true
    });
    
    wx.showLoading({
      title: '解析Excel...'
    });
    
    // 上传Excel文件到后端解析
    wx.uploadFile({
      url: 'http://localhost:5000/api/projects/import/excel',
      filePath: self.data.excelFile.path,
      name: 'file',
      success: function(res) {
        try {
          const data = JSON.parse(res.data);
          if (data.success) {
            self.setData({
              previewData: data.data.preview || [],
              importFilePath: data.file_path || ''
            });
            
            if (self.data.previewData.length === 0) {
              wx.showToast({
                title: '没有解析到有效数据',
                icon: 'none'
              });
            }
          } else {
            wx.showModal({
              title: '解析失败',
              content: data.message || '无法解析Excel文件',
              showCancel: false
            });
          }
        } catch (e) {
          console.error('解析响应失败:', e);
          wx.showToast({
            title: '服务器响应格式错误',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('上传Excel失败:', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
      },
      complete: function() {
        wx.hideLoading();
        self.setData({
          processing: false
        });
      }
    });
  },
  
  // 确认导入Excel数据
  importExcelData: function() {
    if (this.data.previewData.length === 0) {
      wx.showToast({
        title: '没有数据可导入',
        icon: 'none'
      });
      return;
    }
    
    if (this.data.processing) {
      return;
    }
    
    const self = this;
    self.setData({
      processing: true
    });
    
    wx.showLoading({
      title: '导入中...'
    });
    
    // 弹窗确认导入模式
    wx.showActionSheet({
      itemList: ['仅添加新项目', '更新已有项目', '替换所有项目'],
      success: function(res) {
        // 根据选择设置导入模式
        let importMode = 'add_only';
        if (res.tapIndex === 1) {
          importMode = 'update_existing';
        } else if (res.tapIndex === 2) {
          importMode = 'replace_all';
        }
        
        // 确认导入
        wx.request({
          url: 'http://localhost:5000/api/projects/import/confirm',
          method: 'POST',
          data: {
            file_path: self.data.importFilePath,
            mode: importMode
          },
          success: function(res) {
            if (res.data && res.data.success) {
              wx.showModal({
                title: '导入成功',
                content: res.data.message || '数据导入完成',
                showCancel: false,
                success: function() {
                  // 返回上一页
                  wx.navigateBack();
                }
              });
            } else {
              wx.showModal({
                title: '导入失败',
                content: res.data.message || '导入数据失败',
                showCancel: false
              });
            }
          },
          fail: function(err) {
            console.error('导入数据请求失败:', err);
            wx.showToast({
              title: '网络错误',
              icon: 'none'
            });
          },
          complete: function() {
            wx.hideLoading();
            self.setData({
              processing: false
            });
          }
        });
      },
      fail: function() {
        wx.hideLoading();
        self.setData({
          processing: false
        });
      }
    });
  }
}); 