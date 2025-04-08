import requests
import json

def test_project_api():
    """测试项目API配置"""
    print("开始测试项目API...")
    
    # 使用新路径测试项目列表API
    api_url = 'http://localhost:5000/projects'
    print(f"请求项目API: {api_url}")
    
    try:
        response = requests.get(api_url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据类型: {type(data).__name__}")
                
                if isinstance(data, dict):
                    print(f"响应对象键: {', '.join(data.keys())}")
                    
                    # 尝试提取项目数据
                    projects = []
                    if 'data' in data and isinstance(data['data'], list):
                        projects = data['data']
                        print(f"从'data'字段提取项目数据")
                    else:
                        # 查找数组类型的字段
                        for key, value in data.items():
                            if isinstance(value, list):
                                projects = value
                                print(f"从'{key}'字段提取项目数据")
                                break
                elif isinstance(data, list):
                    projects = data
                    print("响应直接是项目数组")
                else:
                    print(f"未知响应格式: {type(data).__name__}")
                    projects = []
                
                # 显示项目数据
                print(f"获取到项目总数: {len(projects)}")
                if projects:
                    print("示例项目数据:")
                    for i, project in enumerate(projects[:3]):
                        if isinstance(project, dict):
                            name = project.get('name', project.get('project_name', '未命名'))
                            category = project.get('category', project.get('type', '未分类'))
                            price = project.get('price', project.get('cost', 0))
                            print(f"  {i+1}. {name} - {category} - ¥{price}")
                        else:
                            print(f"  {i+1}. 未知格式: {type(project).__name__}")
                else:
                    print("未获取到项目数据")
                    # 打印完整响应以便调试
                    print(f"完整响应: {json.dumps(data)[:1000]}...")
            except json.JSONDecodeError:
                print("响应不是有效的JSON格式")
                print(f"原始响应内容: {response.text[:1000]}...")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:1000]}...")
    except requests.RequestException as e:
        print(f"请求异常: {str(e)}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_project_api() 