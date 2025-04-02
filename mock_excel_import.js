/**
 * 模拟Excel导入功能
 * 用于解决小程序无法连接本地服务器的问题
 */

// 模拟数据
const mockExcelData = {
  "客户": {
    "columns": ["ID", "姓名", "性别", "年龄", "电话", "门店归属", "籍贯", "备注"],
    "data": [
      {"ID": "CUS001", "姓名": "张三", "性别": "女", "年龄": 32, "电话": "13812345678", "门店归属": "总店", "籍贯": "北京", "备注": ""},
      {"ID": "CUS002", "姓名": "李四", "性别": "女", "年龄": 28, "电话": "13987654321", "门店归属": "分店一", "籍贯": "上海", "备注": "敏感肌"},
      {"ID": "CUS003", "姓名": "王五", "性别": "女", "年龄": 45, "电话": "13765432198", "门店归属": "总店", "籍贯": "广州", "备注": ""}
    ]
  },
  "消耗": {
    "columns": ["客户ID", "进店时间", "离店时间", "总耗卡金额", "总消耗项目数", "服务满意度", "项目1", "美容师1", "金额1", "是否指定1", "项目2", "美容师2", "金额2", "是否指定2"],
    "data": [
      {"客户ID": "CUS001", "进店时间": "2025/03/15 14:30:00", "离店时间": "2025/03/15 16:30:00", "总耗卡金额": 680, "总消耗项目数": 2, "服务满意度": "满意", "项目1": "面部护理", "美容师1": "小张", "金额1": 380, "是否指定1": "✓", "项目2": "肩颈按摩", "美容师2": "小李", "金额2": 300, "是否指定2": ""},
      {"客户ID": "CUS002", "进店时间": "2025/03/16 10:00:00", "离店时间": "2025/03/16 12:00:00", "总耗卡金额": 560, "总消耗项目数": 1, "服务满意度": "非常满意", "项目1": "敏感肌护理", "美容师1": "小王", "金额1": 560, "是否指定1": "✓", "项目2": "", "美容师2": "", "金额2": "", "是否指定2": ""},
      {"客户ID": "CUS003", "进店时间": "2025/03/17 15:00:00", "离店时间": "2025/03/17 17:30:00", "总耗卡金额": 1200, "总消耗项目数": 2, "服务满意度": "满意", "项目1": "全身排毒", "美容师1": "小赵", "金额1": 800, "是否指定1": "", "项目2": "头部按摩", "美容师2": "小钱", "金额2": 400, "是否指定2": "✓"}
    ]
  }
};

/**
 * Excel导入模拟对象
 */
const excelImport = {
  /**
   * 导入Excel数据
   * @param {String} filePath - 文件路径
   * @param {Object} options - 配置项
   * @returns {Promise} 导入结果
   */
  importExcelData: function(filePath, options = {}) {
    console.log('模拟导入Excel数据:', filePath);
    
    return new Promise((resolve, reject) => {
      // 显示导入中提示
      wx.showLoading({
        title: '正在导入...',
      });
      
      // 模拟网络延迟
      setTimeout(() => {
        wx.hideLoading();
        
        // 返回成功结果
        resolve({
          code: 0,
          message: '导入成功',
          data: {
            importedCount: 3,
            customers: [
              { id: 'CUS001', name: '张三', gender: '女' },
              { id: 'CUS002', name: '李四', gender: '女' },
              { id: 'CUS003', name: '王五', gender: '女' }
            ]
          }
        });
      }, 2000);
    });
  },
  
  /**
   * 预览Excel数据
   * @param {String} filePath - 文件路径
   * @param {Object} options - 配置项
   * @returns {Promise} 预览数据
   */
  previewExcelData: function(filePath, options = {}) {
    console.log('模拟预览Excel数据:', filePath);
    
    return new Promise((resolve, reject) => {
      // 显示加载中提示
      wx.showLoading({
        title: '正在分析...',
      });
      
      // 模拟网络延迟
      setTimeout(() => {
        wx.hideLoading();
        
        // 返回预览数据
        resolve({
          code: 0,
          message: '预览成功',
          data: mockExcelData
        });
      }, 1500);
    });
  }
};

// 导出模块
module.exports = excelImport;