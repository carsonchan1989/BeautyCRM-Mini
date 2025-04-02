/**
 * Excel处理工具
 * 专门针对"模拟-客户信息档案.xlsx"标准模板格式优化
 */
class ExcelProcessor {
  /**
   * 构造函数
   * @param {Object} options 配置选项
   * @param {Logger} options.logger 日志工具实例
   */
  constructor(options = {}) {
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // 字段映射表，用于标准化字段名称
    this.fieldMapping = {
      // 客户基本信息字段映射
      '客户ID': 'customerId',
      '客户编号': 'customerId',
      '顾客编号': 'customerId',
      '姓名': 'name',
      '客户姓名': 'name',
      '顾客姓名': 'name',
      '性别': 'gender',
      '年龄': 'age',
      '手机': 'phone',
      '手机号': 'phone',
      '手机号码': 'phone',
      '电话': 'phone',
      '电话号码': 'phone',
      '联系方式': 'phone',
      '地址': 'address',
      '客户地址': 'address',
      '家庭住址': 'address',
      '居住地址': 'address',
      '生日': 'birthday',
      '出生日期': 'birthday',
      '会员卡号': 'memberCardNo',
      '卡号': 'memberCardNo',
      '会员级别': 'memberLevel',
      '等级': 'memberLevel',
      '门店': 'store',
      '门店名称': 'store',
      '店铺': 'store',
      '备注': 'remarks',
      '客户备注': 'remarks',
      '顾客备注': 'remarks',
      
      // 健康档案字段映射
      '健康状况': 'healthCondition',
      '健康情况': 'healthCondition',
      '身体状况': 'healthCondition',
      '过敏史': 'allergies',
      '过敏情况': 'allergies',
      '过敏原': 'allergies',
      '慢性病': 'chronicDiseases',
      '病史': 'medicalHistory',
      '既往病史': 'medicalHistory',
      '医疗历史': 'medicalHistory',
      '体重': 'weight',
      '身高': 'height',
      '血型': 'bloodType',
      
      // 生活习惯字段映射
      '生活习惯': 'lifeHabits',
      '习惯': 'lifeHabits',
      '作息时间': 'sleepPattern',
      '睡眠': 'sleepPattern',
      '睡眠习惯': 'sleepPattern',
      '饮食习惯': 'dietHabits',
      '饮食': 'dietHabits',
      '饮食偏好': 'dietHabits',
      '运动': 'exercise',
      '运动习惯': 'exercise',
      '兴趣爱好': 'hobbies',
      '爱好': 'hobbies',
      
      // 消费记录字段映射
      '消费日期': 'consumptionDate',
      '日期': 'consumptionDate',
      '消费时间': 'consumptionDate',
      '项目': 'projectName',
      '项目名称': 'projectName',
      '服务项目': 'projectName',
      '消费项目': 'projectName',
      '金额': 'amount',
      '消费金额': 'amount',
      '价格': 'amount',
      '实付金额': 'amount',
      '支付方式': 'paymentMethod',
      '付款方式': 'paymentMethod',
      '支付类型': 'paymentMethod',
      '技师': 'technician',
      '服务技师': 'technician',
      '操作技师': 'technician',
      '服务人员': 'technician',
      '满意度': 'satisfaction',
      '满意程度': 'satisfaction',
      '评价': 'satisfaction',
      '服务评价': 'satisfaction'
    };
  }

  /**
   * 预检查Excel文件
   * @param {String} filePath 文件路径
   * @returns {Promise} 预检查结果
   */
  preCheckExcelFile(filePath) {
    return new Promise((resolve, reject) => {
      // 获取文件扩展名
      const fileExt = filePath.split('.').pop().toLowerCase();
      
      if (!['xlsx', 'xls', 'csv'].includes(fileExt)) {
        return reject(new Error('不支持的文件格式，请上传模拟-客户信息档案.xlsx格式的文件'));
      }
      
      // 读取文件头进行基本检查
      wx.getFileSystemManager().readFile({
        filePath: filePath,
        position: 0,
        length: 4096, // 只读取文件开头部分
        success: (res) => {
          try {
            this.logger.info('文件基本检查通过');
            
            resolve({
              fileExt,
              isValid: true,
              message: '文件预检查通过'
            });
          } catch (e) {
            this.logger.error('文件预检查异常', e);
            reject(new Error('文件格式异常，请确保使用标准的模拟-客户信息档案.xlsx模板'));
          }
        },
        fail: (err) => {
          this.logger.error('读取文件失败', err);
          reject(new Error('读取文件失败: ' + err.errMsg));
        }
      });
    });
  }

  /**
   * 处理Excel文件
   * @param {String} filePath 文件路径
   * @returns {Promise} 处理结果
   */
  processFile(filePath) {
    return new Promise((resolve, reject) => {
      this.logger.info('开始处理Excel文件: ' + filePath);
      
      // 文件扩展名检查
      const fileExt = filePath.split('.').pop().toLowerCase();
      if (!['xlsx', 'xls', 'csv'].includes(fileExt)) {
        this.logger.error('不支持的文件格式: ' + fileExt);
        return reject(new Error('不支持的文件格式，请上传xlsx、xls或csv文件'));
      }
      
      // 根据文件路径判断读取方式
      this._readAndProcessFile(filePath, fileExt)
        .then(resolve)
        .catch(reject);
    });
  }

  /**
   * 智能检测表头位置并提取数据
   * @param {Object} worksheet XLSX工作表对象 
   * @param {Object} XLSX XLSX库对象
   * @returns {Object} 包含headers和data的对象
   * @private
   */
  _detectHeaderRowAndExtractData(worksheet, XLSX) {
    this.logger.info('开始智能检测表头位置');
    
    const range = XLSX.utils.decode_range(worksheet['!ref'] || 'A1:A1');
    
    // 尝试读取前3行，寻找包含关键字段的行作为表头
    for(let r = range.s.r; r <= Math.min(range.s.r + 2, range.e.r); r++) {
      const potentialHeaders = [];
      
      // 提取当前行所有单元格值
      for(let c = range.s.c; c <= range.e.c; c++) {
        const cellAddress = XLSX.utils.encode_cell({ r: r, c: c });
        const cell = worksheet[cellAddress];
        const value = cell && cell.v !== undefined ? String(cell.v) : '';
        potentialHeaders.push(value);
      }
      
      // 检查是否包含"客户ID"或"姓名"等关键字段
      const hasCustomerId = potentialHeaders.some(h => 
        (typeof h === 'string') && (h.includes('客户') && h.includes('ID') || 
         h === '客户ID' || h === '编号' || h === '顾客编号'));
        
      const hasName = potentialHeaders.some(h => 
        (typeof h === 'string') && (h === '姓名' || h === '客户姓名' || 
         h === '名字' || h === '顾客姓名'));
      
      // 检查是否有二进制文件头格式的表头，避免错误识别
      const hasBinaryHeader = potentialHeaders.some(h => 
        (typeof h === 'string') && h.includes('PK\\u0003\\u0004'));
        
      if((hasCustomerId || hasName) && !hasBinaryHeader) {
        this.logger.info(`找到表头行: ${r+1}`, { headers: JSON.stringify(potentialHeaders) });
        
        // 使用当前行作为表头提取数据
        const headers = potentialHeaders;
        const data = [];
        
        // 从表头下一行开始提取数据
        for(let dataRow = r + 1; dataRow <= range.e.r; dataRow++) {
          const rowData = {};
          let hasValue = false;
          
          for(let c = range.s.c; c <= range.e.c; c++) {
            if(c - range.s.c >= headers.length) continue; // 确保不超出表头长度
            
            const header = headers[c - range.s.c];
            if(!header || header === '') continue; // 跳过空表头
            
            const cellAddress = XLSX.utils.encode_cell({ r: dataRow, c: c });
            const cell = worksheet[cellAddress];
            
            // 如果有值且表头不为空，则记录数据
            if(cell && cell.v !== undefined) {
              rowData[header] = cell.v;
              hasValue = true;
            }
          }
          
          if(hasValue) data.push(rowData);
        }
        
        return { headers, data, headerRow: r };
      }
    }
    
    // 如果未找到包含关键字段的表头行，则返回null
    this.logger.warn('未找到有效表头行，将使用默认表头');
    return null;
  }

  _readAndProcessFile(filePath, fileExt) {
    return new Promise((resolve, reject) => {
      // 加载XLSX库
      let XLSX;
      try {
        XLSX = require('./xlsx');
        this.logger.info('XLSX库加载成功');
      } catch (e) {
        this.logger.error('XLSX库加载失败', e);
        return reject(new Error('无法加载XLSX库，请检查环境'));
      }
      
      // 使用小程序API读取文件
      wx.getFileSystemManager().readFile({
        filePath: filePath,
        encoding: fileExt === 'csv' ? 'utf-8' : 'binary',
        success: (res) => {
          this.logger.info('文件读取成功，开始解析');
          
          try {
            // 解析Excel文件
            let workbook;
            if (fileExt === 'csv') {
              // 处理CSV格式
              const csvData = res.data;
              workbook = {
                SheetNames: ['Sheet1'],
                Sheets: { 'Sheet1': XLSX.utils.json_to_sheet(this._parseCSV(csvData)) }
              };
            } else {
              // 处理Excel格式 - 使用arraybuffer类型更可靠
              workbook = XLSX.read(res.data, { type: 'binary' });
            }
            
            // 确保工作簿有效
            if (!workbook || !workbook.SheetNames || workbook.SheetNames.length === 0) {
              throw new Error('Excel文件格式异常或为空');
            }
            
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            
            // 使用智能表头检测
            const detectedResult = this._detectHeaderRowAndExtractData(worksheet, XLSX);
            
            let data = [];
            if (detectedResult) {
              // 使用检测到的表头和数据
              data = detectedResult.data;
              this.logger.info(`使用第${detectedResult.headerRow+1}行作为表头`, { 
                headerCount: detectedResult.headers.length,
                dataRowCount: data.length 
              });
            } else {
              // 备用方案：使用标准sheet_to_json函数
              data = XLSX.utils.sheet_to_json(worksheet);
              this.logger.info('使用默认表头转换', { rowCount: data.length });
            }
            
            // 如果数据为空但文件不为空，尝试强制提取
            if (data.length === 0 && worksheet && worksheet['!ref']) {
              this.logger.warn('未提取到数据行，尝试强制提取');
              
              // 创建默认表头
              const defaultHeaders = ['客户ID', '姓名', '性别', '年龄', '手机号', '备注'];
              const range = XLSX.utils.decode_range(worksheet['!ref']);
              
              // 提取所有数据行
              for(let r = range.s.r + 1; r <= range.e.r; r++) {
                const rowData = {};
                let hasValue = false;
                
                for(let c = range.s.c; c <= Math.min(range.e.c, defaultHeaders.length-1); c++) {
                  const cellAddress = XLSX.utils.encode_cell({ r: r, c: c });
                  const cell = worksheet[cellAddress];
                  if(cell && cell.v !== undefined) {
                    rowData[defaultHeaders[c]] = cell.v;
                    hasValue = true;
                  }
                }
                
                if(hasValue) data.push(rowData);
              }
              
              this.logger.info('强制提取结果', { rowCount: data.length });
            }
            
            // 记录数据示例以便调试
            if (data.length > 0) {
              this.logger.info('数据样本', { 
                sampleRow: JSON.stringify(data[0]),
                keys: Object.keys(data[0]).join(', ')
              });
            }
            
            // 标准化数据字段
            this.logger.info('开始标准化数据字段', { rowCount: data.length });
            const standardizedData = this._standardizeData(data);
            
            // 将数据分类
            const processedData = this._categorizeData(standardizedData);
            
            this.logger.info('数据处理完成', { 
              recordCount: standardizedData.length,
              customers: processedData.customers.length,
              consumptions: processedData.consumptions.length
            });
            
            resolve({
              recordCount: standardizedData.length,
              data: processedData
            });
          } catch (error) {
            this.logger.error('解析文件失败', error);
            reject(new Error('解析文件失败: ' + error.message));
          }
        },
        fail: (err) => {
          this.logger.error('读取文件失败', err);
          reject(new Error('读取文件失败: ' + err.errMsg));
        }
      });
    });
  }

  /**
   * 解析CSV文件
   * @param {String} csvData CSV文件内容
   * @returns {Array} 解析后的数据数组
   * @private
   */
  _parseCSV(csvData) {
    this.logger.info('开始解析CSV文件');
    
    // 去除BOM头
    if (csvData.charCodeAt(0) === 0xFEFF) {
      csvData = csvData.substr(1);
    }
    
    // 分割行
    const rows = csvData.split(/\r\n|\n|\r/);
    if (rows.length === 0) {
      this.logger.warn('CSV文件为空');
      return [];
    }
    
    // 提取表头
    const headerLine = rows[0];
    if (!headerLine) {
      this.logger.error('CSV文件表头行为空');
      return [];
    }
    
    const headers = headerLine.split(',').map(header => header.trim());
    this.logger.info('CSV表头信息:', { headers: JSON.stringify(headers) });
    
    // 处理数据行
    const data = [];
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i].trim();
      if (!row) continue;
      
      // 简单的CSV解析，不考虑引号内的逗号等特殊情况
      const values = row.split(',');
      const obj = {};
      
      // 使用 for 循环替代 forEach
      for (let index = 0; index < headers.length; index++) {
        const header = headers[index];
        if (header && index < values.length) {
          obj[header] = values[index].trim();
        }
      }
      
      data.push(obj);
    }
    
    this.logger.info('CSV解析完成', { rowCount: data.length });
    return data;
  }

  /**
   * 标准化数据字段
   * @param {Array} data 原始数据
   * @returns {Array} 标准化后的数据
   * @private
   */
  _standardizeData(data) {
    this.logger.info('开始标准化数据字段', { inputRowCount: data.length });
    
    const result = [];
    
    // 遍历每条记录
    for (let i = 0; i < data.length; i++) {
      const item = data[i];
      const standardItem = {};
      
      // 如果记录为空，跳过
      if (!item || typeof item !== 'object') continue;
      
      // 遍历记录中的所有字段
      const keys = Object.keys(item);
      for (let j = 0; j < keys.length; j++) {
        const key = keys[j];
        const value = item[key];
        
        // 查找标准字段名
        const standardKey = this.fieldMapping[key] || key;
        
        // 设置标准化字段值
        standardItem[standardKey] = value;
      }
      
      result.push(standardItem);
    }
    
    this.logger.info('数据标准化完成', { outputRowCount: result.length });
    return result;
  }

  /**
   * 将数据分类整理
   * @param {Array} data 标准化后的数据
   * @returns {Object} 分类后的数据对象
   * @private
   */
  _categorizeData(data) {
    this.logger.info('开始分类整理数据');
    
    const result = {
      customers: [],
      consumptions: []
    };
    
    // 提取客户信息和消费记录
    for (let i = 0; i < data.length; i++) {
      const item = data[i];
      
      // 判断该条记录是否是消费记录
      if (item.consumptionDate && item.projectName) {
        result.consumptions.push({
          customerId: item.customerId,
          date: item.consumptionDate,
          projectName: item.projectName,
          amount: parseFloat(item.amount) || 0,
          paymentMethod: item.paymentMethod,
          technician: item.technician,
          satisfaction: item.satisfaction
        });
      } else if (item.customerId || item.name || Object.keys(item).length > 0) {
        // 条件放宽：有customerId或name字段或至少有一个字段
        // 确保有客户ID
        const customerId = item.customerId || `CUST_${Date.now()}_${i}`;
        
        // 客户基本信息
        const customer = {
          customerId: customerId,
          name: item.name || '未命名客户',  // 确保姓名有默认值
          gender: item.gender || '未知',
          age: parseInt(item.age) || 0,
          phone: item.phone || '',
          address: item.address || '',
          birthday: item.birthday || '',
          memberCardNo: item.memberCardNo || '',
          memberLevel: item.memberLevel || '标准会员',
          store: item.store || '总店',
          remarks: item.remarks || '',
          
          // 健康档案
          health: {
            condition: item.healthCondition || '',
            allergies: item.allergies || '',
            chronicDiseases: item.chronicDiseases || '',
            medicalHistory: item.medicalHistory || '',
            weight: item.weight || '',
            height: item.height || '',
            bloodType: item.bloodType || ''
          },
          
          // 生活习惯
          habits: {
            lifeHabits: item.lifeHabits || '',
            sleepPattern: item.sleepPattern || '',
            dietHabits: item.dietHabits || '',
            exercise: item.exercise || '',
            hobbies: item.hobbies || ''
          }
        };
        
        // 记录创建的客户ID
        this.logger.info(`创建客户记录: ${customerId}`, {
          hasOriginalId: !!item.customerId,
          hasName: !!item.name,
          fieldsCount: Object.keys(item).length
        });
        
        result.customers.push(customer);
      }
    }
    
    // 如果没有提取到客户，但有数据，创建一个默认客户
    if (result.customers.length === 0 && data.length > 0) {
      const defaultCustomerId = `CUST_DEFAULT_${Date.now()}`;
      result.customers.push({
        customerId: defaultCustomerId,
        name: '默认客户',
        gender: '未知',
        age: 0,
        phone: '',
        store: '总店',
        remarks: '系统自动创建',
        health: {},
        habits: {}
      });
      
      this.logger.info(`创建默认客户记录: ${defaultCustomerId}`);
    }
    
    this.logger.info('数据分类完成', {
      customerCount: result.customers.length,
      consumptionCount: result.consumptions.length
    });
    
    return result;
  }
  
  /**
   * 从原始数据中提取客户ID列表
   * @param {Object} processedData 处理后的数据对象
   * @returns {Array} 客户ID列表
   */
  extractCustomerIds(processedData) {
    const customerIds = new Set();
    
    // 从客户列表提取
    if (processedData.customers && Array.isArray(processedData.customers)) {
      processedData.customers.forEach(customer => {
        if (customer.customerId) {
          customerIds.add(customer.customerId);
        }
      });
    }
    
    // 从消费记录提取
    if (processedData.consumptions && Array.isArray(processedData.consumptions)) {
      processedData.consumptions.forEach(consumption => {
        if (consumption.customerId) {
          customerIds.add(consumption.customerId);
        }
      });
    }
    
    const idList = Array.from(customerIds);
    this.logger.info('提取到的客户ID列表', {
      count: idList.length,
      ids: idList.join(', ')
    });
    
    // 如果没有提取到客户ID，显示警告
    if (idList.length === 0) {
      this.logger.warn('未提取到任何客户ID，请检查数据格式');
    }
    
    return idList;
  }
  
  /**
   * 获取指定客户ID的完整数据
   * @param {String} customerId 客户ID
   * @param {Object} processedData 处理后的数据对象
   * @returns {Object} 客户完整数据
   */
  getCustomerData(customerId, processedData) {
    // 查找客户基本信息
    const customerInfo = processedData.customers.find(
      c => c.customerId === customerId
    ) || {};
    
    // 查找客户消费记录
    const consumptions = processedData.consumptions.filter(
      c => c.customerId === customerId
    ) || [];
    
    return {
      customer: customerInfo,
      consumptions: consumptions
    };
  }
}

module.exports = ExcelProcessor;