-- 007：Python / Java / C++ 概念体系种子（节点 + 前置依赖边）
-- psql -d programming_tutor -f 007_seed_python_java_cpp_knowledge.sql

-- ===================== Python =====================
INSERT INTO knowledge_nodes (language, name, description, category) VALUES
    ('python', '变量与赋值', '变量绑定、动态类型、赋值语句', '基础'),
    ('python', '数据类型', 'int/float/str/bool/None 及类型转换', '基础'),
    ('python', '输入输出', 'input()/print()/格式化输出', '基础'),
    ('python', '运算符', '算术/比较/逻辑/成员运算符', '基础'),
    ('python', '字符串', '切片、常用方法、f-string', '数据结构'),
    ('python', '列表', 'list 增删改查、切片、推导式', '数据结构'),
    ('python', '元组', 'tuple 不可变序列', '数据结构'),
    ('python', '字典', 'dict 键值映射、遍历与常用方法', '数据结构'),
    ('python', '集合', 'set 去重与集合运算', '数据结构'),
    ('python', '条件语句', 'if/elif/else 与缩进块', '流程控制'),
    ('python', '循环', 'for/while、range、enumerate', '流程控制'),
    ('python', '循环控制', 'break/continue/else 子句', '流程控制'),
    ('python', '函数', 'def 定义、参数、默认值、返回值', '函数'),
    ('python', '函数参数', '位置参数、关键字参数、可变参数', '函数'),
    ('python', '作用域', '局部/全局/闭包与 global', '函数'),
    ('python', '异常处理', 'try/except/finally、自定义异常', '进阶'),
    ('python', '类与对象', 'class、__init__、实例属性', '面向对象'),
    ('python', '继承与多态', '继承、super()、方法重写', '面向对象'),
    ('python', '模块与导入', 'import、from...import、__main__', '基础'),
    ('python', '文件读写', 'open()、with 语句、打开模式', '进阶'),
    ('python', '列表推导式', 'comprehension 与条件过滤', '进阶'),
    ('python', '排序与查找', 'sorted/key、bisect、常见算法', '算法'),
    ('python', '递归', '递归函数与终止条件', '函数')
ON CONFLICT (language, name) DO NOTHING;

INSERT INTO knowledge_edges (language, from_node, to_node) VALUES
    ('python', '变量与赋值', '数据类型'),
    ('python', '变量与赋值', '输入输出'),
    ('python', '数据类型', '运算符'),
    ('python', '运算符', '条件语句'),
    ('python', '条件语句', '循环'),
    ('python', '循环', '循环控制'),
    ('python', '循环', '列表'),
    ('python', '数据类型', '字符串'),
    ('python', '列表', '元组'),
    ('python', '列表', '字典'),
    ('python', '列表', '集合'),
    ('python', '循环', '函数'),
    ('python', '函数', '函数参数'),
    ('python', '函数', '作用域'),
    ('python', '函数', '递归'),
    ('python', '函数', '异常处理'),
    ('python', '函数', '类与对象'),
    ('python', '类与对象', '继承与多态'),
    ('python', '变量与赋值', '模块与导入'),
    ('python', '异常处理', '文件读写'),
    ('python', '列表', '列表推导式'),
    ('python', '列表', '排序与查找')
ON CONFLICT (language, from_node, to_node) DO NOTHING;

-- ===================== Java =====================
INSERT INTO knowledge_nodes (language, name, description, category) VALUES
    ('java', '变量与基本类型', '八大基本类型、变量声明与类型转换', '基础'),
    ('java', '运算符与表达式', '算术/比较/逻辑运算符、类型提升', '基础'),
    ('java', '输入输出', 'Scanner 读入、System.out 输出与格式化', '基础'),
    ('java', '条件与分支', 'if/else、switch 语句', '流程控制'),
    ('java', '循环', 'for/while/do-while、增强 for', '流程控制'),
    ('java', '数组', '定长数组、多维数组、遍历', '数据结构'),
    ('java', '字符串', 'String 不可变、StringBuilder、常用方法', '数据结构'),
    ('java', '集合框架', 'List/Set/Map 与 ArrayList/HashMap', '数据结构'),
    ('java', '方法与重载', '方法定义、参数传递、方法重载', '函数'),
    ('java', '递归', '递归与递归终止条件', '函数'),
    ('java', '类与对象', 'class、构造器、this、封装', '面向对象'),
    ('java', '继承与多态', 'extends、super、方法重写、向上转型', '面向对象'),
    ('java', '接口与抽象类', 'interface、abstract class、implements', '面向对象'),
    ('java', '异常处理', 'try/catch/finally、受检异常、throws', '进阶'),
    ('java', '泛型', '泛型类/方法、类型参数', '进阶'),
    ('java', '包与访问控制', 'package/import、public/private/protected', '基础'),
    ('java', '静态成员', 'static 字段/方法与类初始化', '进阶'),
    ('java', '排序与查找', 'Arrays.sort、Collections.sort、二分查找', '算法'),
    ('java', '时间复杂度', '算法效率分析基础', '算法')
ON CONFLICT (language, name) DO NOTHING;

INSERT INTO knowledge_edges (language, from_node, to_node) VALUES
    ('java', '变量与基本类型', '运算符与表达式'),
    ('java', '变量与基本类型', '输入输出'),
    ('java', '运算符与表达式', '条件与分支'),
    ('java', '条件与分支', '循环'),
    ('java', '循环', '数组'),
    ('java', '变量与基本类型', '字符串'),
    ('java', '数组', '集合框架'),
    ('java', '循环', '方法与重载'),
    ('java', '方法与重载', '递归'),
    ('java', '方法与重载', '类与对象'),
    ('java', '类与对象', '继承与多态'),
    ('java', '继承与多态', '接口与抽象类'),
    ('java', '方法与重载', '异常处理'),
    ('java', '集合框架', '泛型'),
    ('java', '变量与基本类型', '包与访问控制'),
    ('java', '类与对象', '静态成员'),
    ('java', '数组', '排序与查找'),
    ('java', '排序与查找', '时间复杂度')
ON CONFLICT (language, from_node, to_node) DO NOTHING;

-- ===================== C++ =====================
INSERT INTO knowledge_nodes (language, name, description, category) VALUES
    ('cpp', '变量与基本类型', 'int/double/char/bool 与声明', '基础'),
    ('cpp', '运算符与表达式', '算术/比较/逻辑/位运算符', '基础'),
    ('cpp', '输入输出流', 'cin/cout 与流格式化', '基础'),
    ('cpp', '条件分支', 'if/else、switch 语句', '流程控制'),
    ('cpp', '循环', 'for/while/do-while、范围 for', '流程控制'),
    ('cpp', '数组与 vector', '定长数组、std::vector 动态数组', '数据结构'),
    ('cpp', 'string 字符串', 'std::string 与常用成员函数', '数据结构'),
    ('cpp', '指针与引用', '指针运算、引用、空指针', '进阶'),
    ('cpp', '函数与重载', '函数定义、默认参数、重载', '函数'),
    ('cpp', '递归', '递归与终止条件', '函数'),
    ('cpp', '结构体与类', 'struct/class、成员与访问控制', '面向对象'),
    ('cpp', '构造与析构', '构造函数、析构函数、RAII', '面向对象'),
    ('cpp', '继承与多态', '继承、虚函数、纯虚与多态', '面向对象'),
    ('cpp', '动态内存', 'new/delete、内存泄漏', '进阶'),
    ('cpp', 'STL 容器', 'map/set/queue/stack 与迭代器', '数据结构'),
    ('cpp', 'STL 算法', 'sort/find/accumulate 与 lambda', '算法'),
    ('cpp', '异常处理', 'try/catch/throw', '进阶'),
    ('cpp', '模板', '函数模板与类模板', '进阶'),
    ('cpp', '时间复杂度', '算法效率分析基础', '算法')
ON CONFLICT (language, name) DO NOTHING;

INSERT INTO knowledge_edges (language, from_node, to_node) VALUES
    ('cpp', '变量与基本类型', '运算符与表达式'),
    ('cpp', '变量与基本类型', '输入输出流'),
    ('cpp', '运算符与表达式', '条件分支'),
    ('cpp', '条件分支', '循环'),
    ('cpp', '循环', '数组与 vector'),
    ('cpp', '变量与基本类型', 'string 字符串'),
    ('cpp', '变量与基本类型', '指针与引用'),
    ('cpp', '循环', '函数与重载'),
    ('cpp', '函数与重载', '递归'),
    ('cpp', '指针与引用', '结构体与类'),
    ('cpp', '结构体与类', '构造与析构'),
    ('cpp', '结构体与类', '继承与多态'),
    ('cpp', '指针与引用', '动态内存'),
    ('cpp', '数组与 vector', 'STL 容器'),
    ('cpp', 'STL 容器', 'STL 算法'),
    ('cpp', '函数与重载', '异常处理'),
    ('cpp', '函数与重载', '模板'),
    ('cpp', 'STL 算法', '时间复杂度')
ON CONFLICT (language, from_node, to_node) DO NOTHING;
