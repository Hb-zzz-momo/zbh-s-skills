# Web 实验专用检查项

以本次指导书为准，此清单来自已读实验1—5材料，不能代替重读新版本。每项关联报告位置、源文件、结果证据与状态。

## 实验1
HTML语义结构、链接、图片、音频、表格、GET/POST；另一设备访问必须是真实第二设备，回环或本机另一浏览器不能冒充。静态资源POST返回200不等于服务端解析参数。

## 实验2 CSS
新闻标题/来源/灰色日期/无下划线，6幅图与视频播放，2em缩进/2倍行高/版心居中；Tlias顶栏两端对齐、三筛选字段与五职位、默认空值、查询提交与重置、四行七列、灰底白字版权。浏览器检查实际样式与交互，静态演示不得声称数据库管理。

## 实验3 JavaScript
计数0→1→0和零值禁用，状态与DOM同步；浏览器名称/版本/窗口/URL/加载耗时，刷新后重新读取，处理loadEventEnd尚未就绪；表格数据行移入#f2e2e2、移出白色。课外视频如为选做，单列不适用，不冒充观看。

## 实验4 Maven/Spring
Maven仓库/镜像/环境，IDEA真实导入与Maven设置不能由命令行构建代替；POM/标准目录/依赖坐标和排除/target Jar；官方Spring骨架与身份Hello；GET查询串和POST表单体的实际解析与响应字段；user.txt→DAO→Service→Controller→JSON→页面5用户；解释7个分层/注入注解与Controller/RestController、返回视图/返回正文差异。替代版本写明原因和未覆盖项。

## 实验5 数据访问
MySQL8真实实例与bigdata/emp30记录；24条SQL每条有语句、实际结果、条件分析，空集不改数据凑结果；NULL、COUNT、AVG分母、WHERE/HAVING、稳定排序/分页；JDBC/注解Mapper/XML Mapper各CRUD，校验错误密码、注入样式输入、更新旧值失效、删除与回读；properties/YAML分别实际测试，保留测试数与动作数区别。XML namespace/@Param对应，PreparedStatement/#{}参数绑定，资源关闭与临时数据定向清理。
