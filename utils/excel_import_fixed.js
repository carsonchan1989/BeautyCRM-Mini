// 修复版Excel导入模块
const app = getApp();
const apiConfig = require('../config/api');

/**
 * 导入Excel文件并处理消耗数据
 * @param {File} file - 用户选择的Excel文件
 * @returns {Promise} - 返回处理结果的Promise
 */
function importExcelData(file) {
  return new Promise((resolve, reject) => {
    // 显示加载中
    wx.showLoading({
      title: '文件上传中...',
      mask: true
    });
    
    // 首先上传Excel文件
    uploadExcelFile(file)
      .then(fileUrl => {
        console.log('文件上传成功，开始处理数据');
        
        // 调用后端API处理Excel数据
        return processExcelData(fileUrl);
      })
      .then(result => {
        wx.hideLoading();
        resolve(result);
      })
      .catch(error => {
        wx.hideLoading();
        console.error('Excel导入失败:', error);
        reject(error);
      });
  });
}

/**
 * 上传Excel文件到服务器
 * @param {File} file - 用户选择的Excel文件
 * @returns {Promise<string>} - 返回上传后的文件URL
 */
function uploadExcelFile(file) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: apiConfig.getUrl('/api/excel/import'),
      filePath: file.path,
      name: 'file',
      success: function(res) {
        try {
          const data = JSON.parse(res.data);
          if (data.code === 0) {
            resolve(data.data.fileUrl);
          } else {
            reject(new Error(data.message || '文件上传失败'));
          }
        } catch (e) {
          reject(new Error('解析上传响应失败'));
        }
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

/**
 * 处理Excel数据
 * @param {string} fileUrl - 上传后的文件URL
 * @returns {Promise<Object>} - 返回处理结果
 */
function processExcelData(fileUrl) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: apiConfig.getUrl('/api/excel/process'),
      method: 'POST',
      data: {
        fileUrl: fileUrl,
        // 修复: 移除total_project_count字段，使用正确的字段名
        mappingOptions: {
          customerMapping: {
            id: '客户ID',
            name: '姓名',
            gender: '性别',
            age: '年龄',
            // 其他字段...
          },
          serviceMapping: {
            customer_id: '客户ID',
            service_date: '进店时间',
            departure_time: '离店时间',
            total_amount: '总耗卡金额',
            total_sessions: '总消耗项目数', // 使用正确的字段名
            satisfaction: '服务满意度',
            payment_method: '支付方式'
          },
          serviceItemMapping: {
            project_name: '项目名称',
            beautician_name: '美容师',
            unit_price: '金额',
            is_specified: '是否指定'
          }
        }
      },
      success: function(res) {
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(new Error(res.data.message || '数据处理失败'));
        }
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

/**
 * 预览Excel数据
 * @param {File} file - 用户选择的Excel文件
 * @returns {Promise<Object>} - 返回预览数据
 */
function previewExcelData(file) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: apiConfig.getUrl('/api/excel/preview'),
      filePath: file.path,
      name: 'file',
      success: function(res) {
        try {
          const data = JSON.parse(res.data);
          if (data.code === 0) {
            resolve(data.data);
          } else {
            reject(new Error(data.message || '文件预览失败'));
          }
        } catch (e) {
          reject(new Error('解析预览响应失败'));
        }
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

// 导出模块
module.exports = {
  importExcelData,
  previewExcelData
};