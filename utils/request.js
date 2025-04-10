/**
 * 网络请求工具
 * 封装微信小程序网络请求API，统一处理请求和响应
 */

const Logger = require('./logger');
const logger = new Logger('Request');
const apiConfig = require('../config/api');

/**
 * 发起网络请求
 * @param {Object} options 请求配置
 * @param {string} options.url 请求地址
 * @param {string} [options.method='GET'] 请求方法
 * @param {Object} [options.data] 请求数据
 * @param {Object} [options.header] 请求头
 * @param {number} [options.timeout=30000] 超时时间
 * @param {boolean} [options.showLoading=true] 是否显示加载提示
 * @param {string} [options.loadingText='加载中'] 加载提示文本
 * @returns {Promise<any>} 请求结果
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data,
    header = {},
    timeout = 30000,
    showLoading = true,
    loadingText = '加载中'
  } = options;

  // 显示加载提示
  if (showLoading) {
    wx.showLoading({
      title: loadingText,
      mask: true
    });
  }

  // 添加通用请求头
  const headers = {
    'Content-Type': 'application/json',
    ...header
  };

  return new Promise((resolve, reject) => {
    logger.info(`${method} ${url}`, data);

    wx.request({
      url,
      method,
      data,
      header: headers,
      timeout,
      success: (res) => {
        logger.info(`${method} ${url} 响应:`, res.statusCode);

        // 隐藏加载提示
        if (showLoading) {
          wx.hideLoading();
        }

        // 处理HTTP状态码
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } 
        // 处理重定向状态码
        else if (res.statusCode >= 300 && res.statusCode < 400) {
          logger.info(`${method} ${url} 重定向:`, res.statusCode);
          
          // 获取重定向URL
          const redirectUrl = res.header['Location'] || res.header['location'];
          if (redirectUrl) {
            logger.info(`跟随重定向到: ${redirectUrl}`);
            // 重新请求重定向URL
            wx.request({
              url: redirectUrl,
              method,
              data,
              header: headers,
              timeout,
              success: (redirectRes) => {
                logger.info(`重定向请求响应:`, redirectRes.statusCode);
                if (redirectRes.statusCode >= 200 && redirectRes.statusCode < 300) {
                  resolve(redirectRes.data);
                } else {
                  const error = {
                    code: redirectRes.statusCode,
                    message: (redirectRes.data && redirectRes.data.error) || '重定向请求失败',
                    data: redirectRes.data
                  };
                  
                  logger.error(`重定向请求失败:`, error);
                  reject(error);
                }
              },
              fail: (redirectErr) => {
                logger.error(`重定向请求错误:`, redirectErr);
                reject({
                  code: -1,
                  message: redirectErr.errMsg || '重定向请求失败',
                  err: redirectErr
                });
              }
            });
          } else {
            // 如果没有获取到重定向URL，尝试直接返回响应数据
            logger.info(`未找到重定向URL，尝试使用当前响应数据`);
            if (res.data) {
              resolve(res.data);
            } else {
              const error = {
                code: res.statusCode,
                message: '重定向但未找到目标URL',
                data: res.data
              };
              
              logger.error(`${method} ${url} 重定向处理失败:`, error);
              reject(error);
            }
          }
        }
        else {
          const error = {
            code: res.statusCode,
            message: (res.data && res.data.error) || '请求失败',
            data: res.data
          };
          
          logger.error(`${method} ${url} 失败:`, error);
          reject(error);
          
          // 显示错误提示
          wx.showToast({
            title: error.message,
            icon: 'none',
            duration: 2000
          });
        }
      },
      fail: (err) => {
        logger.error(`${method} ${url} 错误:`, err);
        
        // 隐藏加载提示
        if (showLoading) {
          wx.hideLoading();
        }
        
        const error = {
          code: -1,
          message: err.errMsg || '网络请求失败',
          err
        };
        
        reject(error);
        
        // 显示错误提示
        wx.showToast({
          title: error.message,
          icon: 'none',
          duration: 2000
        });
      }
    });
  });
}

/**
 * GET请求
 * @param {string} url 请求地址
 * @param {Object} [data] 请求参数
 * @param {Object} [options] 其他选项
 */
function get(url, data, options = {}) {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  });
}

/**
 * POST请求
 * @param {string} url 请求地址
 * @param {Object} [data] 请求数据
 * @param {Object} [options] 其他选项
 */
function post(url, data, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  });
}

/**
 * PUT请求
 * @param {string} url 请求地址
 * @param {Object} [data] 请求数据
 * @param {Object} [options] 其他选项
 */
function put(url, data, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  });
}

/**
 * DELETE请求
 * @param {string} url 请求地址
 * @param {Object} [data] 请求数据
 * @param {Object} [options] 其他选项
 */
function del(url, data, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  });
}

module.exports = {
  request,
  get,
  post,
  put,
  delete: del,
  // 导出API工具函数
  api: {
    // 调用API的便捷方法
    getUrl: apiConfig.getUrl,
    // 常用API路径快捷方式
    customerList: () => get(apiConfig.getUrl(apiConfig.paths.customer.list)),
    customerDetail: (id) => get(apiConfig.getUrl(apiConfig.paths.customer.detail(id)))
  }
};