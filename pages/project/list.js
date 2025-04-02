Page({
  data: {
    projects: [],
    searchKeyword: '',
    categories: ['全部', '面部护理', '身体护理', '美容服务', '特色项目'],
    categoryIndex: 0,
    originalProjects: [] // 用于存储未经过滤的原始数据
  },

  onLoad: function() {
    // 加载项目分类
    this.loadCategories();
    // 加载项目列表
    this.loadProjects();
  },

  onShow: function() {
    // 每次显示页面时重新加载数据，以确保数据同步
    this.loadProjects();
  },

  // 加载项目分类
  loadCategories: function() {
    const self = this;
    wx.request({
      url: 'http://localhost:5000/api/projects/categories',
      method: 'GET',
      success: function(res) {
        if (res.data && res.data.success && res.data.data.length > 0) {
          // 添加"全部"选项到分类列表的第一个位置
          const categories = ['全部'].concat(res.data.data);
          self.setData({
            categories: categories
          });
        }
      }
    });
  },

  // 加载项目列表
  loadProjects: function() {
    const self = this;
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
            projects: res.data.data,
            originalProjects: res.data.data
          });
          self.filterProjects(); // 应用当前的筛选条件
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
      }
    });
  },

  // 搜索输入处理
  onSearchInput: function(e) {
    this.setData({
      searchKeyword: e.detail.value
    });
    this.filterProjects();
  },

  // 分类选择处理
  onCategoryChange: function(e) {
    this.setData({
      categoryIndex: parseInt(e.detail.value)
    });
    this.filterProjects();
  },

  // 根据搜索关键词和分类筛选项目
  filterProjects: function() {
    if (!this.data.originalProjects || this.data.originalProjects.length === 0) {
      return;
    }
    
    let filteredProjects = this.data.originalProjects;
    const keyword = this.data.searchKeyword.toLowerCase();
    const selectedCategory = this.data.categories[this.data.categoryIndex];

    // 应用搜索关键词过滤
    if (keyword) {
      filteredProjects = filteredProjects.filter(project => 
        (project.name && project.name.toLowerCase().includes(keyword)) ||
        (project.description && project.description.toLowerCase().includes(keyword))
      );
    }

    // 应用分类过滤
    if (selectedCategory !== '全部') {
      filteredProjects = filteredProjects.filter(project => 
        project.category === selectedCategory
      );
    }

    this.setData({
      projects: filteredProjects
    });
  },

  // 点击项目查看详情
  onProjectTap: function(e) {
    const projectId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/project/detail?id=${projectId}`
    });
  },

  // 编辑项目
  onEditProject: function(e) {
    // 阻止事件冒泡，防止触发项目点击事件
    e.stopPropagation();
    const projectId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/project/edit?id=${projectId}`
    });
  },

  // 删除项目
  onDeleteProject: function(e) {
    // 阻止事件冒泡，防止触发项目点击事件
    e.stopPropagation();
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

  // 添加新项目
  onAddProject: function() {
    wx.navigateTo({
      url: '/pages/project/add'
    });
  }
}); 