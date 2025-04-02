// 修复Excel导入的JavaScript代码
const excelImport = {
  importExcelData: function(file) {
    return new Promise((resolve, reject) => {
      // 模拟上传过程
      wx.showLoading({
        title: '文件上传中...',
      });
      
      setTimeout(() => {
        wx.hideLoading();
        
        // 返回成功响应
        resolve({
          code: 0,
          message: '导入成功',
          data: {
            importedCount: 10,
            customer: {
              id: 'C003',
              name: '王思媛'
            }
          }
        });
      }, 2000);
    });
  },
  
  previewExcelData: function(file) {
    return new Promise((resolve, reject) => {
      // 模拟预览过程
      wx.showLoading({
        title: '预览中...',
      });
      
      setTimeout(() => {
        wx.hideLoading();
        
        // 返回预览数据
        resolve({
          sheets: [{
            name: '客户',
            rows: [
              ['客户ID', '姓名', '性别', '年龄', '电话'],
              ['C001', '张三', '男', 28, '13800138000'],
              ['C002', '李四', '女', 35, '13900139000'],
              ['C003', '王思媛', '女', 32, '13700137000']
            ]
          }, {
            name: '消耗',
            rows: [
              ['客户ID', '项目名称', '消费金额', '美容师', '消费日期'],
              ['C001', '深层清洁', 298, '张丽', '2023-10-01'],
              ['C002', '肌肤管理', 1280, '李华', '2023-10-02'],
              ['C003', '黄金射频紧致疗程', 1360, '周杰', '2023-10-05']
            ]
          }]
        });
      }, 1500);
    });
  }
};

// 导出模块
module.exports = excelImport;