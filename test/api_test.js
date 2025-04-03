// API测试脚本 - 检查大模型API是否可用及模型是否存在
const https = require('https');

// API配置
const apiConfig = {
  url: 'https://api.siliconflow.cn/v1',
  apiKey: 'sk-zenjhfgpeauztirirbzjshbvzuvqhqidkfkqwtmmenennmaa',
  model: 'Pro/deepseek-ai/DeepSeek-R1'
};

// 测试1: 检查API服务是否可用 (/models 接口)
function checkApiAvailability() {
  console.log('====================================');
  console.log('测试1: 检查API服务可用性和获取模型列表');
  console.log('====================================');
  
  const options = {
    hostname: 'api.siliconflow.cn',
    port: 443,
    path: '/v1/models',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${apiConfig.apiKey}`
    }
  };

  const req = https.request(options, (res) => {
    console.log(`API状态码: ${res.statusCode}`);

    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      if (res.statusCode === 200) {
        try {
          const result = JSON.parse(data);
          console.log('API服务可用');
          console.log('可用模型列表:');
          
          if (result.data && Array.isArray(result.data)) {
            result.data.forEach(model => {
              console.log(`- ${model.id || model.name}`);
            });

            // 检查我们的模型是否在列表中
            const targetModel = apiConfig.model;
            const modelExists = result.data.some(model => 
              model.id === targetModel || model.name === targetModel
            );
            
            console.log(`\n我们需要的模型 "${targetModel}" ${modelExists ? '存在于列表中' : '不在列表中'}`);
            
            // 检查完模型列表后，进行简单调用测试
            testApiCall();
          } else {
            console.log('无法获取模型列表');
          }
        } catch (e) {
          console.error('解析API响应失败:', e.message);
          console.log('原始响应:', data);
        }
      } else {
        console.error('API服务请求失败，状态码:', res.statusCode);
        console.log('响应内容:', data);
      }
    });
  });

  req.on('error', (e) => {
    console.error('API请求错误:', e.message);
  });

  req.end();
}

// 测试2: 尝试调用API生成内容
function testApiCall() {
  console.log('\n====================================');
  console.log('测试2: 尝试调用模型生成内容');
  console.log('====================================');
  
  const postData = JSON.stringify({
    model: apiConfig.model,
    messages: [
      { role: "system", content: "你是一位专业的美容顾问助手" },
      { role: "user", content: "请简单介绍一下皮肤护理的基本步骤" }
    ],
    temperature: 0.7,
    max_tokens: 500,
    response_format: { type: "text" }
  });

  const options = {
    hostname: 'api.siliconflow.cn',
    port: 443,
    path: '/v1/chat/completions',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData),
      'Authorization': `Bearer ${apiConfig.apiKey}`
    }
  };

  const req = https.request(options, (res) => {
    console.log(`API调用状态码: ${res.statusCode}`);

    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      try {
        if (res.statusCode === 200) {
          const result = JSON.parse(data);
          console.log('API调用成功！示例回复:');
          if (result.choices && result.choices.length > 0) {
            const content = result.choices[0].message.content;
            console.log(content.substring(0, 200) + '...(内容已截断)');
          }
        } else {
          console.error('API调用失败:');
          console.log(data);
          
          // 如果是模型不存在错误，测试不同的模型名称格式
          if (data.includes('Model does not exist')) {
            console.log('\n尝试其他常见模型名称格式...');
            testAlternativeModelNames();
          }
        }
      } catch (e) {
        console.error('解析API响应失败:', e.message);
        console.log('原始响应:', data);
      }
    });
  });

  req.on('error', (e) => {
    console.error('API请求错误:', e.message);
  });

  req.write(postData);
  req.end();
}

// 测试3: 尝试不同格式的模型名称
function testAlternativeModelNames() {
  console.log('\n====================================');
  console.log('测试3: 尝试不同格式的模型名称');
  console.log('====================================');

  // 可能的模型名称格式组合
  const modelNameVariations = [
    'deepseek-ai/deepseek-r1',          // 全小写
    'deepseek-ai/DeepSeek-R1',          // 保留大写
    'DeepSeek-ai/DeepSeek-R1',          // 厂商名称首字母大写
    'deepseek-r1',                      // 仅模型名称小写
    'DeepSeek-R1',                      // 仅模型名称
    'Pro-deepseek-ai/DeepSeek-R1',      // Pro前缀带连字符
    'Pro_deepseek-ai/DeepSeek-R1',      // Pro前缀带下划线
    // 原始格式
    'Pro/deepseek-ai/DeepSeek-R1'       // 原始格式
  ];

  console.log('测试以下模型名称格式:');
  modelNameVariations.forEach((modelName, index) => {
    console.log(`${index + 1}. ${modelName}`);
  });

  // 逐个测试不同的模型名称
  testModelNameVariation(modelNameVariations, 0);
}

// 测试特定格式的模型名称
function testModelNameVariation(modelNames, index) {
  if (index >= modelNames.length) {
    console.log('\n所有模型格式测试完成');
    return;
  }

  const modelName = modelNames[index];
  console.log(`\n测试模型名称: "${modelName}"`);

  const postData = JSON.stringify({
    model: modelName,
    messages: [
      { role: "system", content: "你是助手" },
      { role: "user", content: "hello" }
    ],
    temperature: 0.7,
    max_tokens: 10,
    response_format: { type: "text" }
  });

  const options = {
    hostname: 'api.siliconflow.cn',
    port: 443,
    path: '/v1/chat/completions',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData),
      'Authorization': `Bearer ${apiConfig.apiKey}`
    }
  };

  const req = https.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      if (res.statusCode === 200) {
        console.log(`✓ 模型名称 "${modelName}" 可用! (状态码: 200)`);
      } else {
        try {
          const error = JSON.parse(data);
          console.log(`✗ 模型名称 "${modelName}" 不可用 (状态码: ${res.statusCode})`);
          console.log(`  错误: ${error.message || '未知错误'}`);
        } catch (e) {
          console.log(`✗ 模型名称 "${modelName}" 不可用 (状态码: ${res.statusCode})`);
          console.log(`  响应: ${data}`);
        }
      }

      // 测试下一个模型名称
      setTimeout(() => {
        testModelNameVariation(modelNames, index + 1);
      }, 1000);
    });
  });

  req.on('error', (e) => {
    console.error(`测试模型 "${modelName}" 时出错:`, e.message);
    // 继续测试下一个模型名称
    setTimeout(() => {
      testModelNameVariation(modelNames, index + 1);
    }, 1000);
  });

  req.write(postData);
  req.end();
}

// 开始测试
checkApiAvailability();