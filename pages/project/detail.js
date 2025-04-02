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
    }
  },

  onLoad: function(options) {
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
          self.setData({
            projectData: res.data.data
          });
        } else {
          wx.showToast({
            title: res.data.message || '加载失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('加载项目详情失败:', err);
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
    wx.navigateTo({
      url: `/pages/project/edit?id=${this.data.projectId}`
    });
  },

  // 删除项目
  onDeleteProject: function() {
    const self = this;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个项目吗？',
      success: function(res) {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...'
          });

          wx.request({
            url: `http://localhost:5000/api/projects/${self.data.projectId}`,
            method: 'DELETE',
            success: function(res) {
              if (res.data && res.data.success) {
                wx.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
                // 返回上一页并刷新列表
                setTimeout(() => {
                  wx.navigateBack();
                }, 1500);
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
  }
}); 