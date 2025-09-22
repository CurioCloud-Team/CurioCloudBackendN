# 测试修复后的subject和grade提取逻辑
def _extract_subject_from_collected_data(collected_data):
    # 首先检查直接的subject字段
    if collected_data.get("subject"):
        return collected_data["subject"]

    # 优先检查第一个问题的答案（通常直接询问学科）
    first_answer = collected_data.get("question_1_answer", "")
    if first_answer:
        # 直接匹配学科名称
        direct_subjects = {
            "语文": ["语文", "国语", "汉语", "文学"],
            "数学": ["数学", "算术", "代数", "几何"],
            "英语": ["英语", "英文", "English"],
            "物理": ["物理", "物理学"],
            "化学": ["化学", "化学科"],
            "生物": ["生物", "生物学"],
            "历史": ["历史", "历史课"],
            "地理": ["地理", "地理学"],
            "政治": ["政治", "思想政治", "政治课"],
            "音乐": ["音乐", "音乐课"],
            "美术": ["美术", "美术课", "绘画"],
            "体育": ["体育", "体育课", "体操"],
            "信息技术": ["信息技术", "计算机", "编程", "信息科技"],
            "科学": ["科学", "自然科学"],
            "道德与法治": ["道德与法治", "品德", "法治"],
            "劳动": ["劳动", "劳动技术"],
            "综合实践": ["综合实践", "实践活动"],
            # 编程语言单独处理
            "Java": ["Java", "JAVA", "java"],
            "Python": ["Python", "PYTHON", "python"],
            "C++": ["C++", "CPP", "cpp", "c++"],
            "C语言": ["C语言", "C语言编程"],
            "JavaScript": ["JavaScript", "JS", "javascript", "js"],
            "数据结构与算法": ["数据结构", "算法", "数据结构与算法"]
        }

        first_answer_lower = first_answer.lower()
        for subject, keywords in direct_subjects.items():
            if any(keyword.lower() in first_answer_lower for keyword in keywords):
                return subject

        # 如果第一个答案没有直接匹配，则尝试关键词匹配
        subject_keywords = {
            "数学": ["数学", "算术", "代数", "几何", "微积分", "统计", "计算", "方程", "数据结构", "算法"],
            "语文": ["语文", "中文", "文学", "作文", "阅读", "古诗", "诗歌", "散文", "写作"],
            "英语": ["英语", "English", "英文", "单词", "语法", "听力", "口语", "写作", "外语"],
            "物理": ["物理", "力学", "电学", "光学", "热学", "声学", "运动", "能量", "电磁"],
            "化学": ["化学", "元素", "分子", "化合物", "反应", "实验", "原子", "离子", "有机"],
            "生物": ["生物", "细胞", "遗传", "进化", "生态", "植物", "动物", "基因", "微生物"],
            "历史": ["历史", "古代", "近代", "现代", "朝代", "战争", "文明", "文化", "考古"],
            "地理": ["地理", "地图", "气候", "地形", "国家", "城市", "河流", "山脉", "环境"],
            "政治": ["政治", "法律", "宪法", "政府", "公民", "权利", "民主", "法制", "社会"],
            "音乐": ["音乐", "歌曲", "乐器", "节拍", "音符", "合唱", "旋律", "节奏", "乐理"],
            "美术": ["美术", "绘画", "素描", "色彩", "艺术", "创作", "设计", "雕塑", "美学"],
            "体育": ["体育", "运动", "健身", "球类", "跑步", "游泳", "锻炼", "比赛", "体能"],
            "信息技术": ["计算机", "编程", "软件", "网络", "信息技术", "IT", "代码", "程序", "数据库"]
        }

        for subject, keywords in subject_keywords.items():
            if any(keyword in first_answer_lower for keyword in keywords):
                return subject

    # 如果第一个问题没有匹配，检查其他问题的答案
    for key, value in collected_data.items():
        if key.startswith("question_") and key.endswith("_answer") and value and key != "question_1_answer":
            value_lower = value.lower()
            # 同样使用直接匹配和关键词匹配的逻辑
            for subject, keywords in direct_subjects.items():
                if any(keyword.lower() in value_lower for keyword in keywords):
                    return subject

            for subject, keywords in subject_keywords.items():
                if any(keyword in value_lower for keyword in keywords):
                    return subject

    return ""

def _extract_grade_from_collected_data(collected_data):
    # 首先检查直接的grade字段
    if collected_data.get("grade"):
        return collected_data["grade"]

    # 从动态问题答案中提取年级信息
    for key, value in collected_data.items():
        if key.startswith("question_") and key.endswith("_answer") and value:
            # 年级匹配模式 - 按照优先级排序，更具体的匹配在前
            grade_patterns = [
                # 初中 - 具体年级
                ("初中一年级", "初中一年级"), ("初中二年级", "初中二年级"), ("初中三年级", "初中三年级"),
                ("初一", "初中一年级"), ("初二", "初中二年级"), ("初三", "初中三年级"),
                ("七年级", "初中一年级"), ("八年级", "初中二年级"), ("九年级", "初中三年级"),
                # 高中 - 具体年级
                ("高中一年级", "高中一年级"), ("高中二年级", "高中二年级"), ("高中三年级", "高中三年级"),
                ("高一", "高中一年级"), ("高二", "高中二年级"), ("高三", "高中三年级"),
                # 小学 - 具体年级
                ("小学一年级", "小学一年级"), ("小学二年级", "小学二年级"), ("小学三年级", "小学三年级"),
                ("小学四年级", "小学四年级"), ("小学五年级", "小学五年级"), ("小学六年级", "小学六年级"),
                # 大学 - 具体年级
                ("大学一年级", "大学一年级"), ("大学二年级", "大学二年级"), ("大学三年级", "大学三年级"), ("大学四年级", "大学四年级"),
                ("大一", "大学一年级"), ("大二", "大学二年级"), ("大三", "大学三年级"), ("大四", "大学四年级"),
                # 研究生
                ("研究生一年级", "研究生一年级"), ("研究生二年级", "研究生二年级"), ("研究生三年级", "研究生三年级"),
                ("硕士一年级", "研究生一年级"), ("硕士二年级", "研究生二年级"), ("硕士三年级", "研究生三年级"),
                ("博士一年级", "博士一年级"), ("博士二年级", "博士二年级"), ("博士三年级", "博士三年级"),
                # 通用年级（只有在没有学段前缀时才匹配）
                ("一年级", "小学一年级"), ("二年级", "小学二年级"), ("三年级", "小学三年级"),
                ("四年级", "小学四年级"), ("五年级", "小学五年级"), ("六年级", "小学六年级"),
                # 学段（最后匹配）
                ("初中", "初中"), ("高中", "高中"), ("小学", "小学"), ("大学", "大学"), ("研究生", "研究生"),
                # 成人教育和职业培训
                ("成人", "成人"), ("成人教育", "成人"), ("职业培训", "成人"),
                # 学历层次
                ("本科生", "大学"), ("本科", "大学"), ("专科生", "大学"), ("专科", "大学"),
                ("硕士研究生", "研究生"), ("博士研究生", "博士"),
                # 学习阶段描述
                ("初学", "入门"), ("入门", "入门"), ("基础", "入门"), ("初级", "入门"),
                ("中级", "中级"), ("高级", "高级"), ("专业", "高级"),
                # 幼儿园
                ("幼儿园", "幼儿园"), ("学前班", "学前班"), ("托儿所", "幼儿园")
            ]

            value_lower = value.lower()
            for pattern, grade in grade_patterns:
                if pattern in value_lower:
                    return grade

    return ""

# 测试数据 - 使用实际的数据库数据
test_data = [
    {'question_1_answer': 'Java', 'question_2_answer': 'Java 基础语法与数据类型'},
    {'question_1_answer': '数据结构与算法', 'question_2_answer': '计算机专业本科生（初学或入门）'},
    {'question_1_answer': '化学', 'question_2_answer': '成人'},
    {'question_1_answer': '英语', 'question_2_answer': '小学三年级'},
    {'question_1_answer': '物理', 'question_2_answer': '大学'},
]

print("=== 修复后的提取逻辑测试 ===")
for i, data in enumerate(test_data):
    subject = _extract_subject_from_collected_data(data)
    grade = _extract_grade_from_collected_data(data)
    print(f'测试数据 {i+1}: {data}')
    print(f'提取的subject: "{subject}", grade: "{grade}"')
    print('---')