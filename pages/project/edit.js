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
      url: 'http://localhost:5000/api/projects/categories',
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
      url: `http://localhost:5000/api/projects/${id}`,
      method: 'GET',
      success: function(res) {
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
      url: `http://localhost:5000/api/projects/${this.data.projectId}`,
      method: 'PUT',
      data: projectData,
      success: function(res) {
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