// app.js
const Logger = require('./utils/logger')

App({
  globalData: {
    userInfo: null,
    logger: null,
    apiBaseUrl: 'http://localhost:5000/api' // API服务器地址，加上/api前缀
  },
  
  onLaunch() {
    // 初始化Logger
    this.globalData.logger = new Logger({
      debug: true,
      prefix: 'BtyCRM'
    });
    
    this.globalData.logger.info('小程序启动');
    
    // 获取系统信息
    try {
      const systemInfo = wx.getSystemInfoSync();
      this.globalData.systemInfo = systemInfo;
      this.globalData.logger.info('获取系统信息成功', systemInfo);
    } catch (e) {
      this.globalData.logger.error('获取系统信息失败', e);
    }
    
    // 检查更新
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager();
      
      updateManager.onCheckForUpdate((res) => {
        if (res.hasUpdate) {
          this.globalData.logger.info('发现新版本');
          
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好，是否重启应用？',
              success: (res) => {
                if (res.confirm) {
                  updateManager.applyUpdate();
                }
              }
            });
          });
          
          updateManager.onUpdateFailed(() => {
            this.globalData.logger.error('新版本下载失败');
            
            wx.showModal({
              title: '更新提示',
              content: '新版本下载失败，请检查网络设置并重试'
            });
          });
        }
      });
    }
  }
});