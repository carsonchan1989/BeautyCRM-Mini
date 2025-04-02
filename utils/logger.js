/**
 * 日志工具类
 * 提供统一的日志记录接口
 */
class Logger {
  /**
   * 构造函数
   * @param {Object} options 配置选项
   * @param {String} options.module 模块名称
   * @param {Boolean} options.debug 是否启用调试日志
   */
  constructor(options = {}) {
    this.module = options.module || 'App';
    this.debug = options.debug || false;
    this.listeners = {};
    
    // 日志级别定义
    this.levels = {
      DEBUG: 0,
      INFO: 1,
      WARN: 2,
      ERROR: 3
    };
    
    this.currentLevel = this.debug ? this.levels.DEBUG : this.levels.INFO;
  }
  
  /**
   * 获取格式化的当前时间
   * @returns {String} 格式化的时间
   * @private
   */
  _getTime() {
    const now = new Date();
    return now.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).replace(/\//g, '-');
  }
  
  /**
   * 记录日志
   * @param {String} level 日志级别
   * @param {String} message 日志消息
   * @param {*} data 额外数据
   * @private
   */
  _log(level, message, data) {
    if (this.levels[level] < this.currentLevel) return;
    
    const time = this._getTime();
    const logMessage = `[${time}] [${level}] [${this.module}] ${message}`;
    
    // 控制台输出
    switch (level) {
      case 'DEBUG':
        console.debug(logMessage, data || '');
        break;
      case 'INFO':
        console.info(logMessage, data || '');
        break;
      case 'WARN':
        console.warn(logMessage, data || '');
        break;
      case 'ERROR':
        console.error(logMessage, data || '');
        break;
      default:
        console.log(logMessage, data || '');
    }
    
    // 触发日志事件
    this._emit('log', {
      time,
      level,
      module: this.module,
      message,
      data
    });
    
    return {
      time,
      level,
      text: message,
      data
    };
  }
  
  /**
   * 添加事件监听器
   * @param {String} event 事件名称
   * @param {Function} listener 监听函数
   */
  on(event, listener) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);
    
    return this;
  }
  
  /**
   * 触发事件
   * @param {String} event 事件名称
   * @param {*} data 事件数据
   * @private
   */
  _emit(event, data) {
    const listeners = this.listeners[event];
    if (listeners && Array.isArray(listeners)) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (e) {
          console.error(`事件监听器错误:`, e);
        }
      });
    }
  }
  
  /**
   * 记录调试日志
   * @param {String} message 日志消息
   * @param {*} data 额外数据
   */
  debug(message, data) {
    return this._log('DEBUG', message, data);
  }
  
  /**
   * 记录信息日志
   * @param {String} message 日志消息
   * @param {*} data 额外数据
   */
  info(message, data) {
    return this._log('INFO', message, data);
  }
  
  /**
   * 记录警告日志
   * @param {String} message 日志消息
   * @param {*} data 额外数据
   */
  warn(message, data) {
    return this._log('WARN', message, data);
  }
  
  /**
   * 记录错误日志
   * @param {String} message 日志消息
   * @param {*} data 额外数据
   */
  error(message, data) {
    return this._log('ERROR', message, data);
  }
  
  /**
   * 设置日志级别
   * @param {String} level 日志级别
   */
  setLevel(level) {
    if (this.levels[level] !== undefined) {
      this.currentLevel = this.levels[level];
    }
    
    return this;
  }
  
  /**
   * 启用调试模式
   */
  enableDebug() {
    this.debug = true;
    this.currentLevel = this.levels.DEBUG;
    
    return this;
  }
  
  /**
   * 禁用调试模式
   */
  disableDebug() {
    this.debug = false;
    this.currentLevel = this.levels.INFO;
    
    return this;
  }
}

module.exports = Logger;