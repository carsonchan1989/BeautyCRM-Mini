const apiConfig = require('../../config/api');

Page({
  data: {
    projectId: null,
    projectData: {
      name: '',
      description: '',
      price: '',
      category: '',
      duration: '',
      notes: ''
    },
    categories: ['面部护理', '身体护理', '美容服务', '特色项目'],
    categoryIndex: null
  },

  onLoad: function(options) {
    // 加载项目分类
    this.loadCategories();
    
    if (options.id) {
      this.setData({ projectId: options.id });
      this.loadProjectData(options.id);
    } else {
      wx.showToast({
        title: '项目ID不存在',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  // 加载项目分类
  loadCategories: function() {
    const self = this;
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.project.categories),
      method: 'GET',
      success: function(res) {
        if (res.data && res.data.success && res.data.data.length > 0) {
          self.setData({
            categories: res.data.data
          });
          
          // 如果已经加载了项目数据，重新计算categoryIndex
          if (self.data.projectData.category) {
            const categoryIndex = self.data.categories.indexOf(self.data.projectData.category);
            if (categoryIndex >= 0) {
              self.setData({
                categoryIndex: categoryIndex
              });
            }
          }
        }
      }
    });
  },

  // 加载项目数据
  loadProjectData: function(id) {
    const self = this;
    wx.showLoading({
      title: '加载中...'
    });

    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.project.detail(id)),
      method: 'GET',
      success: function(res) {
        console.log('项目编辑加载响应:', res.statusCode);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          console.log('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            console.log(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                console.log(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode === 200 && redirectRes.data && redirectRes.data.success) {
                  // 处理重定向后的成功响应
                  const projectData = redirectRes.data.data;
                  const categoryIndex = self.data.categories.indexOf(projectData.category);
                  self.setData({
                    projectData: projectData,
                    categoryIndex: categoryIndex >= 0 ? categoryIndex : null
                  });
                } else {
                  wx.showToast({
                    title: (redirectRes.data && redirectRes.data.message) || '重定向后请求失败',
                    icon: 'none'
                  });
                }
              },
              fail: (redirectErr) => {
                console.error('重定向请求错误:', redirectErr);
                wx.showToast({
                  title: '重定向请求失败',
                  icon: 'none'
                });
              },
              complete: function() {
                wx.hideLoading();
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        if (res.statusCode === 200) {
          if (res.data && res.data.success) {
            const projectData = res.data.data;
            const categoryIndex = self.data.categories.indexOf(projectData.category);
            self.setData({
              projectData: projectData,
              categoryIndex: categoryIndex >= 0 ? categoryIndex : null
            });
          } else {
            wx.showToast({
              title: res.data.message || '加载失败',
              icon: 'none'
            });
          }
        } else {
          wx.showToast({
            title: `加载失败 (${res.statusCode})`,
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('加载项目数据失败:', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
      },
      complete: function() {
        wx.hideLoading();
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

    // 发送请求更新项目
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.project.update(this.data.projectId)),
      method: 'PUT',
      data: projectData,
      success: function(res) {
        console.log('项目保存响应:', res.statusCode);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          console.log('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            console.log(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'PUT',
              data: projectData,
              success: (redirectRes) => {
                console.log(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode === 200 && redirectRes.data && redirectRes.data.success) {
                  // 处理重定向后的成功响应
                  wx.showToast({
                    title: '更新成功',
                    icon: 'success'
                  });
                  // 返回上一页
                  setTimeout(() => {
                    wx.navigateBack();
                  }, 1500);
                } else {
                  wx.showToast({
                    title: (redirectRes.data && redirectRes.data.message) || '重定向后请求失败',
                    icon: 'none'
                  });
                }
              },
              fail: (redirectErr) => {
                console.error('重定向请求错误:', redirectErr);
                wx.showToast({
                  title: '重定向请求失败',
                  icon: 'none'
                });
              },
              complete: function() {
                wx.hideLoading();
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        if (res.statusCode === 200) {
          if (res.data && res.data.success) {
            wx.showToast({
              title: '更新成功',
              icon: 'success'
            });
            // 返回上一页
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          } else {
            wx.showToast({
              title: res.data.message || '更新失败',
              icon: 'none'
            });
          }
        } else {
          wx.showToast({
            title: `更新失败 (${res.statusCode})`,
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('更新项目失败:', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
      },
      complete: function() {
        wx.hideLoading();
      }
    });
  },

  // 取消编辑
  cancelEdit: function() {
    wx.navigateBack();
  }
}); 