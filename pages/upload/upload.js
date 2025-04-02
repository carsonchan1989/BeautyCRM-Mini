// pages/upload/upload.js
Page({
  data: {
    
  },
  
  onLoad() {
    // 直接跳转到Excel导入页面
    wx.navigateTo({
      url: '/pages/excel/import'
    });
  }
});