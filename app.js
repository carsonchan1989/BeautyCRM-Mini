// app.js
const Logger = require('./utils/logger')
const apiConfig = require('./config/api')

App({
  globalData: {
    userInfo: null,
    logger: null,
    apiBaseUrl: apiConfig.getBaseUrl() // 使用apiConfig中的baseUrl
  },
  
  onLaunch() {
    // 初始化Logger
    this.globalData.logger = new Logger({
      debug: true,
      prefix: 'BtyCRM'
    });
    
    this.globalData.logger.info('小程序启动');
    this.globalData.logger.info('API地址:', this.globalData.apiBaseUrl);
    
    // 判断运行环境
    try {
      const systemInfo = wx.getSystemInfoSync();
      this.globalData.systemInfo = systemInfo;
      this.globalData.logger.info('运行环境:', systemInfo.platform);
      this.globalData.logger.info('系统信息:', systemInfo.system);
      this.globalData.logger.info('微信版本:', systemInfo.version);
      
      // 记录特定的网络信息
      wx.getNetworkType({
        success: (res) => {
          this.globalData.logger.info('网络类型:', res.networkType);
        }
      });
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