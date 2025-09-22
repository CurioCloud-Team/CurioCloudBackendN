# 直接复制teaching_service.py中的逻辑进行测试
def _extract_subject_from_collected_data(collected_data):
    """
    从收集的数据中智能提取学科信息

    Args:
        collected_data: 收集的用户数据

    Returns:
        学科名称
    """
    # 首先检查直接的subject字段
    if collected_data.get("subject"):
        return collected_data["subject"]

    # 从动态问题答案中提取学科信息
    for key, value in collected_data.items():
        if key.startswith("question_") and key.endswith("_answer") and value:
            # 检查答案中是否包含常见学科关键词
            subject_keywords = {
                "数学": ["数学", "算术", "代数", "几何", "微积分", "统计", "计算", "方程"],
                "语文": ["语文", "中文", "文学", "作文", "阅读", "古诗", "诗歌", "散文"],
                "英语": ["英语", "English", "英文", "单词", "语法", "听力", "口语", "写作"],
                "物理": ["物理", "力学", "电学", "光学", "热学", "声学", "运动", "能量"],
                "化学": ["化学", "元素", "分子", "化合物", "反应", "实验", "原子", "离子"],
                "生物": ["生物", "细胞", "遗传", "进化", "生态", "植物", "动物", "基因"],
                "历史": ["历史", "古代", "近代", "现代", "朝代", "战争", "文明", "文化"],
                "地理": ["地理", "地图", "气候", "地形", "国家", "城市", "河流", "山脉"],
                "政治": ["政治", "法律", "宪法", "政府", "公民", "权利", "民主", "法制"],
                "音乐": ["音乐", "歌曲", "乐器", "节拍", "音符", "合唱", "旋律", "节奏"],
                "美术": ["美术", "绘画", "素描", "色彩", "艺术", "创作", "设计", "雕塑"],
                "体育": ["体育", "运动", "健身", "球类", "跑步", "游泳", "锻炼", "比赛"],
                "信息技术": ["计算机", "编程", "软件", "网络", "信息技术", "IT", "代码", "程序"]
            }

            value_lower = value.lower()
            for subject, keywords in subject_keywords.items():
                if any(keyword in value_lower for keyword in keywords):
                    return subject

    return ""

# 测试数据 - 直接使用从数据库中看到的实际数据
test_data = [
    {'question_1_answer': 'Java', 'question_2_answer': 'Java 基础语法与数据类型'},
    {'question_1_answer': '数据结构与算法', 'question_2_answer': '计算机专业本科生（初学或入门）'},
    {'question_1_answer': '化学', 'question_2_answer': '成人'},
]

print("=== Subject提取测试 ===")
for i, data in enumerate(test_data):
    subject = _extract_subject_from_collected_data(data)
    print(f'测试数据 {i+1}: {data}')
    print(f'提取的subject: "{subject}"')

    # 详细分析每个答案
    for key, value in data.items():
        if key.startswith("question_") and key.endswith("_answer") and value:
            print(f'  分析 {key}: "{value}"')
            value_lower = value.lower()
            found_match = False
            subject_keywords = {
                "数学": ["数学", "算术", "代数", "几何", "微积分", "统计", "计算", "方程"],
                "语文": ["语文", "中文", "文学", "作文", "阅读", "古诗", "诗歌", "散文"],
                "英语": ["英语", "English", "英文", "单词", "语法", "听力", "口语", "写作"],
                "物理": ["物理", "力学", "电学", "光学", "热学", "声学", "运动", "能量"],
                "化学": ["化学", "元素", "分子", "化合物", "反应", "实验", "原子", "离子"],
                "生物": ["生物", "细胞", "遗传", "进化", "生态", "植物", "动物", "基因"],
                "历史": ["历史", "古代", "近代", "现代", "朝代", "战争", "文明", "文化"],
                "地理": ["地理", "地图", "气候", "地形", "国家", "城市", "河流", "山脉"],
                "政治": ["政治", "法律", "宪法", "政府", "公民", "权利", "民主", "法制"],
                "音乐": ["音乐", "歌曲", "乐器", "节拍", "音符", "合唱", "旋律", "节奏"],
                "美术": ["美术", "绘画", "素描", "色彩", "艺术", "创作", "设计", "雕塑"],
                "体育": ["体育", "运动", "健身", "球类", "跑步", "游泳", "锻炼", "比赛"],
                "信息技术": ["计算机", "编程", "软件", "网络", "信息技术", "IT", "代码", "程序"]
            }
            for subject_name, keywords in subject_keywords.items():
                if any(keyword in value_lower for keyword in keywords):
                    print(f'    匹配到学科: {subject_name} (关键词: {[k for k in keywords if k in value_lower]})')
                    found_match = True
                    break
            if not found_match:
                print(f'    未匹配到任何学科')
    print('---')