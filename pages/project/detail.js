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
    isLoading: true,
    errorMessage: ''
  },

  onLoad: function(options) {
    // 初始化日志
    this.debug = true;
    this.log('项目详情页面已加载');
    
    if (options.id) {
      this.setData({ projectId: options.id });
      this.log(`项目ID: ${options.id}`);
      this.loadProjectData(options.id);
    } else {
      this.log('项目ID不存在');
      wx.showToast({
        title: '项目ID不存在',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  // 日志函数
  log: function(message, data) {
    if (this.debug) {
      console.log(`[项目详情] ${message}`, data || '');
    }
  },

  // 加载项目数据
  loadProjectData: function(id) {
    const self = this;
    
    this.setData({
      isLoading: true,
      errorMessage: ''
    });
    
    wx.showLoading({
      title: '加载中...'
    });

    self.log(`请求项目数据: ${apiConfig.getUrl(apiConfig.paths.project.detail(id))}`);
    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.project.detail(id)),
      method: 'GET',
      success: function(res) {
        self.log('项目详情响应:', res.statusCode);
        
        // 处理状态码308的情况
        if (res.statusCode === 308) {
          self.log('收到308重定向响应');
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            self.log(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method: 'GET',
              success: (redirectRes) => {
                self.log(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode === 200 && redirectRes.data && redirectRes.data.success) {
                  // 处理重定向后的成功响应
                  self.log('加载项目数据成功:', redirectRes.data.data);
                  self.setData({
                    projectData: redirectRes.data.data,
                    isLoading: false
                  });
                } else {
                  self.log('重定向后请求失败:', redirectRes.data);
                  self.setData({
                    isLoading: false,
                    errorMessage: (redirectRes.data && redirectRes.data.message) || '重定向后请求失败'
                  });
                  wx.showToast({
                    title: (redirectRes.data && redirectRes.data.message) || '重定向后请求失败',
                    icon: 'none'
                  });
                }
              },
              fail: (redirectErr) => {
                self.log('重定向请求错误:', redirectErr);
                self.setData({
                  isLoading: false,
                  errorMessage: '重定向请求失败'
                });
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
            self.log('加载项目数据成功:', res.data.data);
            self.setData({
              projectData: res.data.data,
              isLoading: false
            });
          } else {
            self.log('加载项目失败:', res.data);
            self.setData({
              isLoading: false,
              errorMessage: res.data.message || '加载失败'
            });
            wx.showToast({
              title: res.data.message || '加载失败',
              icon: 'none'
            });
          }
        } else {
          self.log('请求状态码异常:', res.statusCode);
          self.setData({
            isLoading: false,
            errorMessage: `加载失败 (${res.statusCode})`
          });
          wx.showToast({
            title: `加载失败 (${res.statusCode})`,
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        self.log('加载项目详情失败:', err);
        self.setData({
          isLoading: false,
          errorMessage: '网络错误'
        });
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

  // 编辑项目
  onEditProject: function() {
    this.log(`跳转编辑页面，项目ID: ${this.data.projectId}`);
    wx.navigateTo({
      url: `/pages/project/edit?id=${this.data.projectId}`
    });
  },

  // 返回列表页面
  goBack: function() {
    this.log('返回项目列表页面');
    wx.navigateBack();
  },

  // 删除项目
  onDeleteProject: function() {
    const self = this;
    this.log(`准备删除项目，ID: ${this.data.projectId}`);
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个项目吗？',
      success: function(res) {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...'
          });

          self.log(`发送删除请求: ${apiConfig.getUrl(apiConfig.paths.project.delete(self.data.projectId))}`);
          wx.request({
            url: apiConfig.getUrl(apiConfig.paths.project.delete(self.data.projectId)),
            method: 'DELETE',
            success: function(res) {
              self.log('删除项目响应:', res.statusCode);
              
              // 处理状态码308的情况
              if (res.statusCode === 308) {
                self.log('收到308重定向响应');
                // 获取重定向URL
                const redirectUrl = res.header['Location'] || res.header['location'];
                if (redirectUrl) {
                  self.log(`跟随重定向到: ${redirectUrl}`);
                  // 重新请求重定向URL
                  wx.request({
                    url: redirectUrl,
                    method: 'DELETE',
                    success: (redirectRes) => {
                      self.log(`重定向请求响应:`, redirectRes.statusCode);
                      if (redirectRes.statusCode === 200 && redirectRes.data && redirectRes.data.success) {
                        // 处理重定向后的成功响应
                        self.log('删除项目成功');
                        wx.showToast({
                          title: '删除成功',
                          icon: 'success'
                        });
                        // 返回上一页并刷新列表
                        setTimeout(() => {
                          wx.navigateBack();
                        }, 1500);
                      } else {
                        self.log('重定向后删除失败:', redirectRes.data);
                        wx.showToast({
                          title: (redirectRes.data && redirectRes.data.message) || '重定向后请求失败',
                          icon: 'none'
                        });
                      }
                    },
                    fail: (redirectErr) => {
                      self.log('重定向请求错误:', redirectErr);
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
                  self.log('删除项目成功');
                  wx.showToast({
                    title: '删除成功',
                    icon: 'success'
                  });
                  // 返回上一页并刷新列表
                  setTimeout(() => {
                    wx.navigateBack();
                  }, 1500);
                } else {
                  self.log('删除项目失败:', res.data);
                  wx.showToast({
                    title: res.data.message || '删除失败',
                    icon: 'none'
                  });
                }
              } else {
                self.log('删除请求状态码异常:', res.statusCode);
                wx.showToast({
                  title: `删除失败 (${res.statusCode})`,
                  icon: 'none'
                });
              }
            },
            fail: function(err) {
              self.log('删除项目网络请求失败:', err);
              wx.showToast({
                title: '网络错误',
                icon: 'none'
              });
            },
            complete: function() {
              wx.hideLoading();
            }
          });
        }
      }
    });
  }
}); 