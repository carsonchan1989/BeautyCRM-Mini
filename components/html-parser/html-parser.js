/**
 * 增强型HTML解析器组件
 * 用于解析大模型返回的HTML内容并在小程序中正确渲染
 */
Component({
  properties: {
    /**
     * HTML内容字符串
     */
    htmlContent: {
      type: String,
      value: '',
      observer: function(newVal, oldVal) {
        console.log('HTML解析器: htmlContent已更新', {
          newVal: newVal ? `长度:${newVal.length}` : '空值',
          oldVal: oldVal ? `长度:${oldVal.length}` : '空值'
        });
        
        if (newVal) {
          this._parseHtml(newVal);
        } else {
          console.warn('HTML解析器: 收到空的htmlContent');
          this.setData({ 
            nodes: [],
            parsedContent: ''
          });
        }
      }
    },
    
    /**
     * 是否处理HTML转义字符
     */
    unescape: {
      type: Boolean,
      value: true
    },
    
    /**
     * 是否自动处理样式
     */
    autoStyle: {
      type: Boolean,
      value: true
    },
    
    /**
     * 是否添加默认基础样式
     */
    addBaseStyle: {
      type: Boolean,
      value: true
    }
  },
  
  data: {
    nodes: [], // 解析后的节点数组
    parsedContent: '' // 处理后的HTML字符串
  },
  
  lifetimes: {
    attached: function() {
      console.log('HTML解析器: 组件已挂载');
      if (this.properties.htmlContent) {
        console.log('HTML解析器: 初始化时发现htmlContent，长度:', this.properties.htmlContent.length);
        this._parseHtml(this.properties.htmlContent);
      } else {
        console.log('HTML解析器: 初始化时htmlContent为空');
      }
    },
    
    ready: function() {
      console.log('HTML解析器: 组件已准备就绪', {
        hasContent: !!this.properties.htmlContent,
        contentLength: this.properties.htmlContent ? this.properties.htmlContent.length : 0
      });
      
      // 添加一个延迟检查，当组件挂载完成后再次检查htmlContent
      setTimeout(() => {
        if (this.properties.htmlContent && !this.data.parsedContent) {
          console.log('HTML解析器: 延迟检查发现content未处理，长度:', this.properties.htmlContent.length);
          this._parseHtml(this.properties.htmlContent);
        }
      }, 300);
    }
  },
  
  methods: {
    /**
     * 解析HTML内容
     * @param {String} html HTML内容字符串
     * @private
     */
    _parseHtml: function(html) {
      if (!html) {
        console.warn('HTML解析器: 传入_parseHtml的内容为空');
        this.setData({ 
          nodes: [],
          parsedContent: ''
        });
        return;
      }
      
      console.log('HTML解析器: 开始解析HTML内容', { 
        length: html.length,
        preview: html.substring(0, 50) + '...'
      });
      
      try {
        // 简单检查HTML格式
        if (!html.includes('<div') && !html.includes('<p') && !html.includes('<h')) {
          console.log('HTML解析器: 未检测到HTML标签，作为纯文本处理');
          html = `<div style="font-size:28rpx;line-height:1.6;padding:20rpx;">${html}</div>`;
        }
        
        // 设置解析后的内容
        this.setData({ 
          parsedContent: html  // 直接使用原始HTML内容
        }, () => {
          console.log('HTML解析器: parsedContent已更新到视图', {
            length: html.length
          });
        });
        
        // 触发解析完成事件
        this.triggerEvent('parsed', { 
          content: html,
          originalLength: html.length,
          processedLength: html.length
        });
      } catch (error) {
        console.error('HTML解析器: 解析过程中发生错误', error);
        
        // 发生错误时，通知父组件使用备用方案
        this.triggerEvent('parsed', { 
          content: html,
          originalLength: html.length,
          processedLength: html.length,
          error: true
        });
      }
    },
    
    /**
     * 处理Markdown代码块
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _processMarkdownCodeBlocks: function(html) {
      if (!html) return '';
      
      let processedHtml = html;
      
      // 处理 ```html ... ``` 类型的代码块
      processedHtml = processedHtml.replace(
        /```(\w*)\s*([\s\S]*?)```/g,
        (match, language, code) => {
          return `<pre class="code-block"><code class="language-${language || 'text'}">${code.trim()}</code></pre>`;
        }
      );
      
      // 处理 ~~~ 类型的代码块
      processedHtml = processedHtml.replace(
        /~~~(\w*)\s*([\s\S]*?)~~~/g,
        (match, language, code) => {
          return `<pre class="code-block"><code class="language-${language || 'text'}">${code.trim()}</code></pre>`;
        }
      );
      
      // 处理内联代码 `code`
      processedHtml = processedHtml.replace(
        /`([^`]+)`/g,
        '<code class="inline-code">$1</code>'
      );
      
      return processedHtml;
    },
    
    /**
     * 处理HTML转义字符
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _unescapeHtml: function(html) {
      if (!html) return '';
      
      return html
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&amp;/g, '&')
        .replace(/\\"/g, '"')
        .replace(/\\n/g, '\n')
        .replace(/\\t/g, '\t')
        .replace(/\\\\/g, '\\');
    },
    
    /**
     * 处理HTML样式
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _processStyles: function(html) {
      if (!html) return '';
      
      let processedHtml = html;
      
      // 如果需要添加基础样式
      if (this.properties.addBaseStyle && !processedHtml.includes('<style>')) {
        const baseStyle = `
          <style>
            body, view { font-size: 28rpx; line-height: 1.6; color: #333; }
            h1 { font-size: 40rpx; font-weight: bold; margin: 30rpx 0 20rpx 0; }
            h2 { font-size: 36rpx; font-weight: bold; margin: 25rpx 0 15rpx 0; }
            h3 { font-size: 32rpx; font-weight: bold; margin: 20rpx 0 10rpx 0; }
            h4 { font-size: 30rpx; font-weight: bold; margin: 15rpx 0 10rpx 0; }
            p { margin: 10rpx 0; }
            .strong, strong, b { font-weight: bold; }
            .em, em, i { font-style: italic; }
            ul, ol { margin: 10rpx 0; padding-left: 40rpx; }
            li { margin: 5rpx 0; }
            table { border-collapse: collapse; width: 100%; margin: 15rpx 0; }
            th, td { border: 1px solid #ddd; padding: 10rpx; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            pre, code { font-family: monospace; background-color: #f5f5f5; padding: 10rpx; border-radius: 5rpx; }
            pre { margin: 10rpx 0; white-space: pre-wrap; word-wrap: break-word; }
            blockquote { border-left: 5rpx solid #ddd; padding: 10rpx 20rpx; margin: 10rpx 0; background-color: #f9f9f9; }
            a { color: #10aeff; text-decoration: none; }
          </style>
        `;
        
        // 添加基础样式到HTML头部
        processedHtml = baseStyle + processedHtml;
      }
      
      return processedHtml;
    },
    
    /**
     * 处理表格，确保在小程序中正确显示
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _processTables: function(html) {
      if (!html) return '';
      
      let processedHtml = html;
      
      // 添加表格滚动容器并使用自定义类名
      processedHtml = processedHtml.replace(
        /<table([^>]*)>/g, 
        '<view class="table-container"><table$1 class="custom-table">'
      );
      
      processedHtml = processedHtml.replace(
        /<\/table>/g, 
        '</table></view>'
      );
      
      // 替换th和td为自定义类名
      processedHtml = processedHtml.replace(
        /<th([^>]*)>/g,
        '<th$1 class="custom-th">'
      );
      
      processedHtml = processedHtml.replace(
        /<td([^>]*)>/g,
        '<td$1 class="custom-td">'
      );
      
      return processedHtml;
    },
    
    /**
     * 处理列表，确保缩进正确
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _processLists: function(html) {
      if (!html) return '';
      
      let processedHtml = html;
      
      // 确保列表有正确的缩进和间距
      processedHtml = processedHtml.replace(
        /<(ul|ol)([^>]*)>/g, 
        '<$1$2 style="margin: 10rpx 0; padding-left: 40rpx;">'
      );
      
      return processedHtml;
    },
    
    /**
     * 处理特殊标签，如代码块
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _processSpecialTags: function(html) {
      if (!html) return '';
      
      let processedHtml = html;
      
      // 处理代码块
      processedHtml = processedHtml.replace(
        /<pre([^>]*)>([\s\S]*?)<\/pre>/g,
        (match, attrs, content) => {
          const styledContent = content.replace(
            /<code([^>]*)>([\s\S]*?)<\/code>/g,
            '<code$1 style="display: block; white-space: pre; word-wrap: break-word; overflow: auto; background-color: #f5f5f5; padding: 10rpx; border-radius: 5rpx;">$2</code>'
          );
          return `<pre${attrs} style="margin: 15rpx 0; background-color: #f5f5f5; padding: 15rpx; border-radius: 5rpx; overflow: auto;">${styledContent}</pre>`;
        }
      );
      
      // 处理块引用
      processedHtml = processedHtml.replace(
        /<blockquote([^>]*)>/g,
        '<blockquote$1 style="border-left: 5rpx solid #ddd; padding: 10rpx 20rpx; margin: 15rpx 0; background-color: #f9f9f9;">'
      );
      
      return processedHtml;
    },
    
    /**
     * 清理多余的空白字符
     * @param {String} html HTML字符串
     * @returns {String} 处理后的HTML
     * @private
     */
    _cleanWhitespace: function(html) {
      if (!html) return '';
      
      // 将连续的空白字符替换为单个空格，但保留pre标签中的空白
      let processedHtml = html;
      
      // 提取所有pre标签内容
      const preBlocks = [];
      processedHtml = processedHtml.replace(/<pre\b[^>]*>([\s\S]*?)<\/pre>/g, (match) => {
        preBlocks.push(match);
        return `__PRE_BLOCK_${preBlocks.length - 1}__`;
      });
      
      // 清理非pre标签区域的空白
      processedHtml = processedHtml.replace(/\s+/g, ' ');
      
      // 恢复pre标签内容
      preBlocks.forEach((block, i) => {
        processedHtml = processedHtml.replace(`__PRE_BLOCK_${i}__`, block);
      });
      
      return processedHtml;
    }
  }
}); 