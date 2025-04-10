const apiConfig = require('../../config/api');

Page({
  data: {
    // 项目数据
    projects: [],
    allProjects: [],
    
    // 加载状态
    isLoading: true,
    errorMessage: '',
    
    // 搜索和筛选
    searchKeyword: '',
    filterOptions: {
      category: '',
      priceRange: ''
    },
    
    // 下拉刷新
    isRefreshing: false,
    
    // 分类选项
    categories: ['全部', '面部护理', '身体护理', '美容服务', '特色项目'],
    priceRanges: ['全部', '0-100元', '100-300元', '300-500元', '500元以上'],
    categoryIndex: 0,
    priceRangeIndex: 0,
    
    // 是否显示筛选面板
    showFilterPanel: false
  },

  onLoad: function() {
    // 初始化日志
    this.debug = true;
    this.log('项目列表页面已加载');
    
    // 加载项目分类
    this.loadCategories();
    // 加载项目列表
    this.loadProjects();
  },

  onShow: function() {
    // 每次显示页面时重新加载数据，以确保数据同步
    this.loadProjects();
  },
  
  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadProjects(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  // 日志函数
  log: function(message, data) {
    if (this.debug) {
      console.log(`[项目列表] ${message}`, data || '');
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
          // 添加"全部"选项到分类列表的第一个位置
          const categories = ['全部'].concat(res.data.data);
          self.setData({
            categories: categories
          });
          self.log('加载项目分类成功', categories);
        } else {
          self.log('加载项目分类失败或返回为空');
        }
      },
      fail: function(err) {
        self.log('请求项目分类失败', err);
      }
    });
  },

  // 加载项目列表
  loadProjects: function(callback) {
    const self = this;
    
    this.setData({ 
      isLoading: true,
      errorMessage: '' 
    });
    
    wx.showLoading({
      title: '加载中...'
    });

    wx.request({
      url: apiConfig.getUrl(apiConfig.paths.project.list),
      method: 'GET',
      timeout: 10000, // 设置10秒超时
      success: function(res) {
        self.log('收到服务器响应', { 
          statusCode: res.statusCode,
          dataType: res.data ? typeof res.data : '无数据'
        });
        
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
                  const projects = redirectRes.data.data.map(item => ({
                    ...item,
                    id: item.id || item.projectId // 确保id字段存在
                  }));
                  
                  self.log('从重定向API加载了项目数据:', projects.length + '条');
                  
                  self.setData({
                    projects: projects,
                    allProjects: projects,
                    isLoading: false
                  });
                  
                  self.applySearchAndFilter(); // 应用当前的筛选条件
                } else {
                  self.log('重定向请求失败:', redirectRes.data);
                  self.setData({ 
                    isLoading: false,
                    errorMessage: '加载失败：' + (redirectRes.data && redirectRes.data.error ? redirectRes.data.error : '重定向后请求失败')
                  });
                  
                  wx.showToast({
                    title: '加载失败',
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
                  title: '加载失败',
                  icon: 'none'
                });
              }
            });
            return; // 已处理重定向请求，提前返回
          }
        }
        
        if (res.statusCode === 200) {
          if (res.data && res.data.success) {
            self.log('加载到项目数据:', res.data.data.length + '条');
            
            // 确保项目ID存在
            const projects = res.data.data.map(item => ({
              ...item,
              id: item.id || item.projectId // 确保id字段存在
            }));
            
            self.setData({
              projects: projects,
              allProjects: projects,
              isLoading: false
            });
            
            self.applySearchAndFilter(); // 应用当前的筛选条件
          } else {
            self.log('加载项目失败:', res.data);
            self.setData({ 
              isLoading: false,
              errorMessage: '加载失败：' + (res.data && res.data.error ? res.data.error : '未知错误')
            });
            
            wx.showToast({
              title: '加载失败',
              icon: 'none'
            });
          }
        } else {
          self.log('请求状态码异常:', res.statusCode);
          self.setData({ 
            isLoading: false,
            errorMessage: '加载失败：状态码 ' + res.statusCode
          });
          
          wx.showToast({
            title: '加载失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        self.log('请求项目数据失败:', err);
        
        // 显示具体的错误信息
        let errorMsg = '网络请求失败';
        if (err.errMsg.includes('timeout')) {
          errorMsg = '请求超时，请检查网络连接';
        } else if (err.errMsg.includes('fail')) {
          errorMsg = '无法连接到服务器，请确认服务器地址是否正确';
        }
        
        self.setData({
          isLoading: false,
          errorMessage: errorMsg
        });
        
        wx.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 2000
        });
      },
      complete: function() {
        wx.hideLoading();
        
        if (callback && typeof callback === 'function') {
          callback();
        }
      }
    });
  },

  // 搜索输入处理
  onSearchInput: function(e) {
    this.setData({
      searchKeyword: e.detail.value
    });
    this.applySearchAndFilter();
  },

  // 切换筛选面板
  toggleFilterPanel: function() {
    this.setData({
      showFilterPanel: !this.data.showFilterPanel
    });
  },

  // 分类选择处理
  onCategoryChange: function(e) {
    const index = parseInt(e.detail.value);
    const category = this.data.categories[index] === '全部' ? '' : this.data.categories[index];
    
    this.setData({
      categoryIndex: index,
      'filterOptions.category': category
    });
    
    this.applySearchAndFilter();
  },
  
  // 价格范围选择处理
  onPriceRangeChange: function(e) {
    const index = parseInt(e.detail.value);
    const priceRange = this.data.priceRanges[index] === '全部' ? '' : this.data.priceRanges[index];
    
    this.setData({
      priceRangeIndex: index,
      'filterOptions.priceRange': priceRange
    });
    
    this.applySearchAndFilter();
  },
  
  // 重置筛选
  resetFilter: function() {
    this.setData({
      categoryIndex: 0,
      priceRangeIndex: 0,
      filterOptions: {
        category: '',
        priceRange: ''
      },
      searchKeyword: ''
    });
    
    this.applySearchAndFilter();
  },

  // 根据搜索关键词和分类筛选项目
  applySearchAndFilter: function() {
    if (!this.data.allProjects || this.data.allProjects.length === 0) {
      return;
    }
    
    this.log('应用搜索和筛选', {
      关键词: this.data.searchKeyword,
      分类: this.data.filterOptions.category,
      价格范围: this.data.filterOptions.priceRange
    });
    
    let filteredProjects = this.data.allProjects;
    const keyword = this.data.searchKeyword.toLowerCase();
    const selectedCategory = this.data.filterOptions.category;
    const selectedPriceRange = this.data.filterOptions.priceRange;

    // 应用搜索关键词过滤
    if (keyword) {
      filteredProjects = filteredProjects.filter(project => 
        (project.name && project.name.toLowerCase().includes(keyword)) ||
        (project.description && project.description.toLowerCase().includes(keyword))
      );
    }

    // 应用分类过滤
    if (selectedCategory) {
      filteredProjects = filteredProjects.filter(project => 
        project.category === selectedCategory
      );
    }
    
    // 应用价格范围过滤
    if (selectedPriceRange) {
      filteredProjects = filteredProjects.filter(project => {
        const price = parseFloat(project.price || 0);
        
        if (selectedPriceRange === '0-100元') {
          return price >= 0 && price <= 100;
        } else if (selectedPriceRange === '100-300元') {
          return price > 100 && price <= 300;
        } else if (selectedPriceRange === '300-500元') {
          return price > 300 && price <= 500;
        } else if (selectedPriceRange === '500元以上') {
          return price > 500;
        }
        
        return true;
      });
    }

    this.setData({
      projects: filteredProjects
    });
    
    this.log('筛选后项目数量', filteredProjects.length);
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
    if (e && e.stopPropagation) {
      e.stopPropagation();
    }
    const projectId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/project/edit?id=${projectId}`
    });
  },

  // 删除项目
  onDeleteProject: function(e) {
    // 阻止事件冒泡，防止触发项目点击事件
    if (e && e.stopPropagation) {
      e.stopPropagation();
    }
    const self = this;
    const projectId = e.currentTarget.dataset.id;
    const projectName = e.currentTarget.dataset.name || '此项目';

    wx.showModal({
      title: '确认删除',
      content: `确定要删除${projectName}吗？此操作不可撤销。`,
      success: function(res) {
        if (res.confirm) {
          wx.showLoading({
            title: '删除中...'
          });

          self.log(`发送删除请求: ${apiConfig.getUrl(apiConfig.paths.project.delete(projectId))}`);
          wx.request({
            url: apiConfig.getUrl(apiConfig.paths.project.delete(projectId)),
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
                        self.loadProjects(); // 重新加载项目列表
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
                  self.loadProjects(); // 重新加载项目列表
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
  },

  // 添加新项目
  onAddProject: function() {
    wx.navigateTo({
      url: '/pages/project/add'
    });
  },
  
  // 返回首页
  goToHome: function() {
    wx.switchTab({
      url: '/pages/index/index'
    });
  }
}); 