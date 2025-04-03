// pages/report/prompt.js
const Logger = require('../../utils/logger');

Page({
  data: {
    files: [],
    isLoading: true,
    errorMessage: '',
    selectedFile: null,
    fileContent: ''
  },
  
  onLoad() {
    // 初始化Logger
    this.logger = new Logger({ debug: true });
    this.logger.info('导出提示词查看页面已加载');
    
    // 加载导出的文件列表
    this.loadExportedFiles();
  },
  
  /**
   * 加载导出的文件列表
   */
  loadExportedFiles() {
    try {
      this.setData({ isLoading: true });
      
      // 导入PromptExporter
      const PromptExporter = require('../../utils/exportPrompt');
      this.promptExporter = new PromptExporter({ logger: this.logger });
      
      // 获取导出的文件列表
      this.promptExporter.getExportedFiles()
        .then(result => {
          if (result.success && result.files.length > 0) {
            this.setData({
              files: result.files,
              isLoading: false
            });
          } else {
            this.setData({
              files: [],
              isLoading: false,
              errorMessage: '没有找到导出的提示词文件'
            });
          }
        })
        .catch(error => {
          this.logger.error('加载导出文件列表失败', error);
          this.setData({
            isLoading: false,
            errorMessage: '加载文件列表失败: ' + error.message
          });
        });
    } catch (error) {
      this.logger.error('初始化导出工具失败', error);
      this.setData({
        isLoading: false,
        errorMessage: '初始化失败: ' + error.message
      });
    }
  },
  
  /**
   * 查看文件内容
   */
  viewFile(e) {
    const { filename, path } = e.currentTarget.dataset;
    
    try {
      // 读取文件内容
      const fs = wx.getFileSystemManager();
      const content = fs.readFileSync(path, 'utf8');
      
      this.setData({
        selectedFile: filename,
        fileContent: content
      });
      
      this.logger.info('查看文件内容', { filename });
    } catch (error) {
      this.logger.error('读取文件内容失败', error);
      wx.showToast({
        title: '读取文件失败',
        icon: 'none'
      });
    }
  },
  
  /**
   * 删除文件
   */
  deleteFile(e) {
    const { filename } = e.currentTarget.dataset;
    
    wx.showModal({
      title: '确认删除',
      content: `确定要删除文件 ${filename} 吗？`,
      success: (res) => {
        if (res.confirm) {
          this.promptExporter.deleteExportedFile(filename)
            .then(() => {
              // 重新加载文件列表
              this.loadExportedFiles();
              
              // 如果删除的是当前查看的文件，清空内容
              if (this.data.selectedFile === filename) {
                this.setData({
                  selectedFile: null,
                  fileContent: ''
                });
              }
              
              wx.showToast({
                title: '删除成功',
                icon: 'success'
              });
            })
            .catch(error => {
              this.logger.error('删除文件失败', error);
              wx.showToast({
                title: '删除失败',
                icon: 'none'
              });
            });
        }
      }
    });
  },
  
  /**
   * 复制文件内容
   */
  copyContent() {
    if (!this.data.fileContent) return;
    
    wx.setClipboardData({
      data: this.data.fileContent,
      success: () => {
        wx.showToast({
          title: '内容已复制',
          icon: 'success'
        });
      }
    });
  },
  
  /**
   * 返回上一页
   */
  goBack() {
    wx.navigateBack();
  }
});