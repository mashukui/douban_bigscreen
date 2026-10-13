from pyecharts.charts import Page  # 画图

# 执行之前,请确保:1、已经把json文件放到本目录下 2、把json中的title(71行)和table(137行)的id替换掉
Page.save_resize_html(
	source="大屏_临时.html",
	cfg_file="chart_config.json",
	dest="大屏_最终.html"
)

print('生成完毕：大屏_最终.html')