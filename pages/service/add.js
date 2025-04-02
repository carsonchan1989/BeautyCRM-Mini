const apiConfig = require('../../config/api');

Page({
  data: {
    id: '',
    name: '',
    category: '',
    effects: '',
    description: '',
    price: '',
    sessions: '',
    categories: ['面部护理', '身体护理', '特色护理', '套餐项目'],
    selectedCategory: 0,
    isEdit: false,
    loading: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ 
        id: options.id,
        isEdit: true 
      });
      this.loadServiceData(options.id);
    }
  },

  async loadServiceData(id) {
    this.setData({ loading: true });
    try {
      const response = await wx.request({
        url: apiConfig.getUrl(apiConfig.paths.service.detail(id)),
        method: 'GET'
      });

      if (response.statusCode === 200) {
        const data = response.data;
        const categoryIndex = this.data.categories.findIndex(c => c === data.category);
        
        this.setData({
          name: data.name,
          category: data.category,
          selectedCategory: categoryIndex >= 0 ? categoryIndex : 0,
          effects: data.effects,
          description: data.description,
          price: data.price.toString(),
          sessions: data.sessions.toString()
        });
      } else {
        wx.showToast({
          title: '加载失败',
          icon: 'error'
        });
      }
    } catch (error) {
      console.error('加载项目数据失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'error'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  onCategoryChange(e) {
    this.setData({
      selectedCategory: e.detail.value,
      category: this.data.categories[e.detail.value]
    });
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({
      [field]: e.detail.value
    });
  },

  async onSubmit() {
    if (!this.validateForm()) {
      return;
    }

    const data = {
      name: this.data.name,
      category: this.data.category,
      effects: this.data.effects,
      description: this.data.description,
      price: parseFloat(this.data.price),
      sessions: parseInt(this.data.sessions)
    };

    if (this.data.isEdit) {
      data.id = this.data.id;
    }

    this.setData({ loading: true });

    try {
      const response = await wx.request({
        url: apiConfig.getUrl(this.data.isEdit ? 
          apiConfig.paths.service.update(this.data.id) : 
          apiConfig.paths.service.create),
        method: this.data.isEdit ? 'PUT' : 'POST',
        data: data
      });

      if (response.statusCode === 200 || response.statusCode === 201) {
        wx.showToast({
          title: this.data.isEdit ? '更新成功' : '创建成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(response.data.error || '保存失败');
      }
    } catch (error) {
      console.error('保存项目失败:', error);
      wx.showToast({
        title: error.message || '保存失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  validateForm() {
    if (!this.data.name) {
      wx.showToast({
        title: '请输入项目名称',
        icon: 'none'
      });
      return false;
    }

    if (!this.data.category) {
      wx.showToast({
        title: '请选择项目类别',
        icon: 'none'
      });
      return false;
    }

    if (!this.data.effects) {
      wx.showToast({
        title: '请输入项目功效',
        icon: 'none'
      });
      return false;
    }

    if (!this.data.description) {
      wx.showToast({
        title: '请输入原理描述',
        icon: 'none'
      });
      return false;
    }

    if (!this.data.price || isNaN(parseFloat(this.data.price))) {
      wx.showToast({
        title: '请输入有效的价格',
        icon: 'none'
      });
      return false;
    }

    if (!this.data.sessions || isNaN(parseInt(this.data.sessions))) {
      wx.showToast({
        title: '请输入有效的次数',
        icon: 'none'
      });
      return false;
    }

    return true;
  }
});