Page({
  data: {
    activeTab: 'list', // 默认显示项目列表
    projects: [],
    searchKeyword: '',
    loading: false
  },

  onLoad: function() {
    this.loadProjects();
  },

  onShow: function() {
    // 每次显示页面时重新加载数据
    this.loadProjects();
  },

  // 切换选项卡
  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      activeTab: tab
    });

    if (tab === 'list') {
      this.loadProjects();
    }
  },

  // 加载项目数据
  loadProjects: function() {
    if (this.data.loading) return;

    const self = this;
    this.setData({ loading: true });

    wx.showLoading({
      title: '加载中...'
    });

    wx.request({
      url: 'http://localhost:5000/api/projects',
      method: 'GET',
      success: function(res) {
        if (res.data && res.data.success) {
          console.log('加载到项目数据:', res.data.data.length, '条');
          self.setData({
            projects: res.data.data
          });
          // 如果没有项目，显示提示信息
          if (res.data.data.length === 0) {
            wx.showToast({
              title: '暂无项目数据',
              icon: 'none',
              duration: 2000
            });
          }
        } else {
          console.error('加载项目失败:', res.data);
          wx.showToast({
            title: '加载失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('请求项目数据失败:', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
      },
      complete: function() {
        wx.hideLoading();
        self.setData({ loading: false });
      }
    });
  },

  // 搜索项目
  onSearchInput: function(e) {
    const keyword = e.detail.value;
    this.setData({ searchKeyword: keyword });

    if (keyword) {
      // 筛选本地列表
      const filteredProjects = this.data.projects.filter(project => 
        (project.name && project.name.toLowerCase().includes(keyword.toLowerCase())) ||
        (project.description && project.description.toLowerCase().includes(keyword.toLowerCase()))
      );
      this.setData({
        projects: filteredProjects
      });
    } else {
      // 重新加载全部
      this.loadProjects();
    }
  },

  // 添加新项目
  addProject: function() {
    wx.navigateTo({
      url: '/pages/project/add'
    });
  },

  // 编辑项目
  editProject: function(e) {
    const projectId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/project/edit?id=${projectId}`
    });
  },

  // 删除项目
  deleteProject: function(e) {
    const self = this;
    const projectId = e.currentTarget.dataset.id;

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个项目吗？',
      success: function(res) {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...'
          });

          wx.request({
            url: `http://localhost:5000/api/projects/${projectId}`,
            method: 'DELETE',
            success: function(res) {
              if (res.data && res.data.success) {
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
                self.loadProjects(); // 重新加载项目列表
              } else {
                wx.showToast({
                  title: res.data.message || '删除失败',
                  icon: 'none'
                });
              }
            },
            fail: function(err) {
              console.error('删除项目失败:', err);
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
  },

  // 手动录入
  showManualInput: function() {
    wx.navigateTo({
      url: '/pages/project/add'
    });
  },

  // 导入Excel
  importExcel: function() {
    wx.navigateTo({
      url: '/pages/project/add?mode=excel'
    });
  },

  // 下载模板
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
  }
}); 