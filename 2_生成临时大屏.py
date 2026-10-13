from sqlalchemy import create_engine  # 创建数据库连接
import pandas as pd
import jieba  # 中文分词
import collections
from pyecharts.charts import WordCloud, Bar, Pie, Page, EffectScatter  # 画图
from pyecharts.globals import ThemeType, CurrentConfig  # 颜色主题
import pyecharts.options as opts  # 配置项
from pyecharts.components import Table  # 数据表格
from snownlp import SnowNLP  # 中文情感分析库
from pprint import pprint

# 修正pyecharts资源CDN路径(v6目录下缺少主题文件,如themes/chalk.js返回404,会导致主题静默失效:透明背景+默认蓝色)
# 必须在创建任何图表对象之前设置,否则不生效
CurrentConfig.ONLINE_HOST = 'https://assets.pyecharts.org/assets/v5/'

# 全局设置主题颜色
theme_config = ThemeType.CHALK  # 颜色方案
# 表格和标题的颜色
table_color = ""
if theme_config == ThemeType.DARK:
	table_color = '#333333'
elif theme_config == ThemeType.CHALK:
	table_color = '#293441'
elif theme_config == ThemeType.PURPLE_PASSION:
	table_color = '#5B5C6E'
elif theme_config == ThemeType.ROMANTIC:
	table_color = '#F0E8CD'
elif theme_config == ThemeType.ESSOS:
	table_color = '#FDFCF5'
else:
	table_color = ''


def get_stopwords(v_file, v_append):
	"""获取停用词"""
	with open(v_file, 'r') as f:
		stopwords_list = f.readlines()
	stopwords_list = [i.strip() for i in stopwords_list]
	stopwords_list.extend(v_append)
	return stopwords_list


def make_title(v_title):
	"""最上面的大标题"""
	table = Table()
	table.chart_id = 'title1'  # 固定chart_id:默认是随机uuid,重跑一次排版配置(chart_config.json)就对不上了
	table.add(headers=[v_title], rows=[], attributes={
		"align": "center",
		"border": "False",
		"padding": "2px",
		"style": "background:{}; width:1350px; height:50px; font-size:25px; color:#C0C0C0;".format(table_color)
	})
	table.render('大标题.html')
	print('生成完毕:大标题.html')
	return table


def make_table(v_df):
	"""绘制数据表格"""
	# 标题
	data_list = v_df.values.tolist()
	table = Table(page_title='我的表格标题', )
	table.chart_id = 'table1'  # 固定chart_id:默认是随机uuid,重跑一次排版配置(chart_config.json)就对不上了
	table.add(headers=['排名', '电影名称', '评分', '评论数', '上映年', '一句话短评'], rows=data_list, attributes={
		"align": "left",
		"border": "False",
		"padding": "20px",
		"style": "background:{}; width:450px; height:350px; font-size:10px; color:#C0C0C0;padding:3px;".format(
			table_color)
	}).set_global_opts(title_opts=opts.TitleOpts(title='这是表格1'))
	table.render('电影排名TOP10_数据表格.html')
	print('生成完毕:电影排名TOP10_数据表格.html')
	return table


def filmname_wordcloud(v_str):
	"""绘制词云图"""
	# cut_words = list(jieba.cut(v_str))
	# 停用词列表
	stopwords = get_stopwords(v_file='hit_stopwords.txt',
	                          v_append=[' ', '都', 'None', '不', '最', '不是', '不会', '没有', '中', '才'])
	print('stopwords is:')
	pprint(stopwords)
	result = []
	for word in v_str:
		if word not in stopwords:
			result.append(word)
	data = collections.Counter(result)
	data = data.most_common(300)
	wc = WordCloud(init_opts=opts.InitOpts(width="450px", height="350px", theme=theme_config, chart_id='wc1'))
	wc.add(series_name="电影名称",
	       data_pair=data,
	       word_size_range=[15, 20],
	       width='400px',  # 宽度
	       height='300px',  # 高度
	       word_gap=5  # 单词间隔
	       )  # 增加数据
	wc.set_global_opts(
		title_opts=opts.TitleOpts(pos_left='center',
		                          title="豆瓣电影分析-词云图",
		                          title_textstyle_opts=opts.TextStyleOpts(font_size=20)  # 设置标题
		                          ),
		tooltip_opts=opts.TooltipOpts(is_show=True),  # 不显示工具箱
	)
	wc.set_series_opts(label_opts=opts.LabelOpts(is_show=True))
	wc.render('电影名称_词云图.html')  # 生成html文件
	print('生成完毕:电影名称_词云图.html')
	return wc


def make_top10_comment_bar(v_df):
	"""TOP10评论数电影-条形图"""
	df_top10_comment = v_df.nlargest(columns='comments', n=10)
	print(df_top10_comment)
	x_data = df_top10_comment['filmname'].values.tolist()
	x_data.sort()
	y_data = df_top10_comment['comments'].values.tolist()
	y_data.sort()
	# 画条形图
	bar = Bar(
		init_opts=opts.InitOpts(theme=theme_config, width="450px", height="350px", chart_id='bar_cmt1'))  # 初始化条形图
	bar.add_xaxis(x_data)  # 增加x轴数据
	bar.add_yaxis("评论数量", y_data)  # 增加y轴数据
	bar.reversal_axis()  # 设置水平方向
	bar.set_series_opts(label_opts=opts.LabelOpts(position="right"))  # Label出现位置
	bar.set_global_opts(
		legend_opts=opts.LegendOpts(pos_left='right'),
		title_opts=opts.TitleOpts(title="评论数TOP10电影-条形图", pos_left='center'),  # 标题
		toolbox_opts=opts.ToolboxOpts(is_show=False, ),  # 不显示工具箱
		xaxis_opts=opts.AxisOpts(name="评论",  # x轴名称
		                         axislabel_opts=opts.LabelOpts(font_size=8, rotate=0),
		                         splitline_opts=opts.SplitLineOpts(is_show=False)
		                         ),
		yaxis_opts=opts.AxisOpts(name="电影",  # y轴名称
		                         axislabel_opts=opts.LabelOpts(font_size=7, rotate=45),  # y轴名称
		                         )
	)
	bar.render("评论数TOP10_条形图.html")  # 生成html文件
	print('生成完毕:评论数TOP10_条形图.html')
	return bar


def make_analyse_pie(v_cmt_list):
	score_list = []  # 情感评分值
	tag_list = []  # 打标分类结果
	pos_count = 0  # 计数器-积极
	mid_count = 0  # 计数器-中性
	neg_count = 0  # 计数器-消极
	for comment in v_cmt_list:
		tag = ''
		sentiments_score = SnowNLP(comment).sentiments
		if sentiments_score < 0.4:  # 情感分小于0.4判定为消极
			tag = '消极'
			neg_count += 1
		elif 0.4 <= sentiments_score <= 0.6:  # 情感分在[0.4,0.6]直接判定为中性
			tag = '中性'
			mid_count += 1
		else:  # 情感分大于0.6判定为积极
			tag = '积极'
			pos_count += 1
		score_list.append(sentiments_score)  # 得分值
		tag_list.append(tag)  # 判定结果
	# 仅有真实短评的行有情感结果,空短评行留空(整列赋值会因长度不符报错,掩码赋新列会让空值写成 'na')
	mask = df['comment'].notna() & (df['comment'].astype(str).str.strip() != '')
	df['情感得分'] = float('nan')
	df['分析结果'] = ''
	df.loc[mask, '情感得分'] = score_list
	df.loc[mask, '分析结果'] = tag_list
	df.to_excel('情感判定结果.xlsx', index=None)  # 把情感分析结果保存到excel文件
	# 画饼图
	pie = (
		Pie(init_opts=opts.InitOpts(theme=theme_config, width="450px", height="350px", chart_id='pie1'))
			.add(series_name="评价情感分布",  # 系列名称
		         data_pair=[['积极', pos_count],  # 添加数据
		                    ['中性', mid_count],
		                    ['消极', neg_count]],
		         rosetype="radius",  # 是否展示成南丁格尔图
		         radius=["30%", "55%"],  # 扇区圆心角展现数据的百分比，半径展现数据的大小
		         )  # 加入数据
			.set_global_opts(  # 全局设置项
			title_opts=opts.TitleOpts(title="短评情感分布-饼图", pos_left='center'),  # 标题
			legend_opts=opts.LegendOpts(pos_left='right', orient='vertical')  # 图例设置项,靠右,竖向排列
		)
			.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}")))  # 样式设置项
	pie.render('情感分布_饼图.html')  # 生成html文件
	print('生成完毕:情感分布_饼图.html')
	return pie


def make_cmt_count_bar(v_df):
	"""评价数分段统计"""
	cmt_count_list = v_df['comments'].values.tolist()
	# 设置分段
	bins = [0, 100000, 200000, 300000, 500000, 1000000, 4000000]
	# 设置标签
	labels = ['0-10w', '10w-20w', '20w-30w', '30w-50w', '50w-100w', '100w-400w']
	# 按分段离散化数据
	segments = pd.cut(cmt_count_list, bins, labels=labels)  # 按分段切割数据
	counts = segments.value_counts().reindex(labels, fill_value=0).values.tolist()  # 统计个数
	bar = Bar(
		init_opts=opts.InitOpts(theme=theme_config, width="450px", height="350px", chart_id='bar_cmt2'))  # 初始化条形图
	bar.add_xaxis(labels, )  # 增加x轴数据
	bar.add_yaxis("评价数", counts)  # 增加y轴数据
	bar.set_global_opts(
		legend_opts=opts.LegendOpts(pos_left='right'),
		title_opts=opts.TitleOpts(title="评价数量区间分布-柱形图", pos_left='center'),  # 标题
		toolbox_opts=opts.ToolboxOpts(is_show=False, ),  # 不显示工具箱
		xaxis_opts=opts.AxisOpts(name="评论数",  # x轴名称
		                         axislabel_opts=opts.LabelOpts(font_size=8)),  # 字体大小
		yaxis_opts=opts.AxisOpts(name="电影数量",
		                         axislabel_opts={"rotate": 0},
		                         splitline_opts=opts.SplitLineOpts(is_show=True,
		                                                           linestyle_opts=opts.LineStyleOpts(type_='solid')),
		                         ),  # y轴名称
	)
	# 标记最大值
	bar.set_series_opts(
		markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max", name="最大值"), ],
		                                  symbol_size=35)  # 标记符号大小
	)
	bar.render("评价数分布-柱形图.html")  # 生成html文件
	print('生成完毕:评价数分布-柱形图.html')
	return bar


def make_scatter(x_data, y_data):
	sc = (EffectScatter(init_opts=opts.InitOpts(width="450px", height="350px", theme=theme_config, chart_id='scatter1'))
	      .add_xaxis(xaxis_data=x_data)
	      .add_yaxis(
		series_name="",
		y_axis=y_data,
		symbol_size=10,
		label_opts=opts.LabelOpts(is_show=False),
	)
	      .set_series_opts()
	      .set_global_opts(title_opts=opts.TitleOpts(title='评分年份分布-涟漪散点图', pos_left='center'),
	                       xaxis_opts=opts.AxisOpts(name='年份',  # x轴名称
	                                                type_="value",
	                                                splitline_opts=opts.SplitLineOpts(is_show=True,
	                                                                                  linestyle_opts=opts.LineStyleOpts(
		                                                                                  type_='dashed')),
	                                                split_number=10,  # 分隔段数
	                                                min_=1930,  # 最小值
	                                                max_=2020  # 最大值
	                                                ),
	                       yaxis_opts=opts.AxisOpts(name='评分值',  # y轴名称
	                                                type_="value",
	                                                axistick_opts=opts.AxisTickOpts(is_show=True),
	                                                splitline_opts=opts.SplitLineOpts(is_show=True,
	                                                                                  linestyle_opts=opts.LineStyleOpts(
		                                                                                  type_='dashed')),
	                                                min_=9,  # 最小值
	                                                max_=10  # 最大值
	                                                ),
	                       tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross", is_show=True),
	                       # visualmap_opts=opts.VisualMapOpts(type_="size", max_=10, min_=5),
	                       )
	      )
	sc.render('评分年份分布-散点图.html')
	print('生成完毕:散点图.html')
	return sc


if __name__ == '__main__':
	# mysql连接串
	engine = create_engine('mysql+pymysql://root:123456@127.0.0.1/douban_bigscreen')
	df = pd.read_sql(sql='select * from t_film', con=engine)  # 取数据库数据
	df_table = pd.read_sql(sql='select `rank`,filmname,score,comments,showtime,comment from t_film limit 10',
	                       con=engine)
	# 电影名称列表
	film_all_list = df['filmname'].values.tolist()
	# 电影名称字符串
	film_all_str = ' '.join(film_all_list)
	# 短评列表（过滤空短评:空值 str() 后会变成字符串 'nan',会被 SnowNLP 误判为中性）
	comment_all_list = [str(i) for i in df['comment'].dropna() if str(i).strip()]
	# 上映年份
	year_list = df['showtime'].values.tolist()[:50]
	score_list = df['score'].values.tolist()[:50]
	# 绘制:整个页面
	page = Page(
		page_title="基于Python的豆瓣电影数据分析大屏",
		layout=Page.DraggablePageLayout,  # 拖拽方式
	)
	page.add(
		# 增加:大标题
		make_title(v_title='基于Python的豆瓣电影数据分析大屏'),
		# 绘制:中下方数据表格
		make_table(v_df=df_table),
		# 绘制:电影名称词云图
		filmname_wordcloud(v_str=film_all_list),
		# 绘制:TOP10评论数-条形图
		make_top10_comment_bar(v_df=df),
		# 绘制情感分布饼图
		make_analyse_pie(v_cmt_list=comment_all_list),
		# 绘制:评价数分段统计-柱形图
		make_cmt_count_bar(v_df=df),
		# 绘制:散点图
		make_scatter(x_data=year_list, y_data=score_list)
	)
	page.render('大屏_临时.html')  # 执行完毕后,打开临时html并排版,排版完点击Save Config，把json文件放到本目录下
	print('生成完毕:大屏_临时.html')
