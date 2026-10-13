# 程序功能：爬取豆瓣电影TOP250的数据
import requests  # 发送请求
from bs4 import BeautifulSoup  # 解析网页
import pandas as pd  # 存取csv
from time import sleep  # 等待时间
from sqlalchemy import create_engine  # 连接数据库

movie_name = []  # 电影名称
movie_url = []  # 电影链接
movie_star = []  # 电影评分
movie_star_people = []  # 评分人数
movie_director = []  # 导演
movie_actor = []  # 主演
movie_year = []  # 上映年份
movie_country = []  # 国家
movie_type = []  # 类型
short_comment = []  # 一句话短评


def get_movie_info(url, headers):
	"""
	获取豆瓣电影详情数据
	:param url: 爬取地址
	:param headers: 爬取请求头
	:return: None
	"""
	res = requests.get(url, headers=headers)  # 发送请求
	soup = BeautifulSoup(res.text, 'html.parser')  # 解析页面
	for movie in soup.select('.item'):
		name = movie.select('.hd a')[0].text.replace('\n', '')  # 电影名称
		movie_name.append(name.split(' / ')[0])
		url = movie.select('.hd a')[0]['href']  # 电影链接
		movie_url.append(url)
		star = movie.select('.rating_num')[0].text  # 电影评分
		movie_star.append(star)
		star_people = [i.text for i in movie.select('.bd span') if '人评价' in i.text][0]  # 评分人数
		star_people = star_people.strip().replace('人评价', '')
		movie_star_people.append(star_people)
		movie_infos = movie.select('.bd p')[0].text.strip()  # 导演、主演、年份、国家、类型
		director = movie_infos.split('\n')[0].split('   ')[0]
		movie_director.append(director.replace('导演: ', ''))
		try:  # 一句话短评
			comment = movie.select('.quote')[0].text.strip()
			short_comment.append(comment)
		except:
			short_comment.append(None)
		try:  # 页面上既有导演，又有主演
			actor = movie_infos.split('\n')[0].split('   ')[1]
			movie_actor.append(actor.replace('主演: ', ''))
		except:  # 页面上只有导演，没有主演（比如，黑客帝国2，第10页）
			movie_actor.append(None)
		# 年份可能有多段（大闹天宫、天书奇谭、高山下的花环）：倒数第2段是国家、最后1段是类型，其余都是年份
		info_parts = [i.strip() for i in movie_infos.split('\n')[1].split('/')]
		movie_year.append('/'.join(info_parts[:-2]))
		movie_country.append(info_parts[-2])
		movie_type.append(info_parts[-1])


def save_to_csv(csv_name):
	"""
	数据保存到csv
	:return: None
	"""
	df = pd.DataFrame()  # 初始化一个DataFrame对象
	df['rank'] = [i for i in range(1, 251)]  # 排名
	df['filmname'] = movie_name
	df['url'] = movie_url
	df['score'] = movie_star
	df['comments'] = movie_star_people
	df['directors'] = movie_director
	df['actors'] = movie_actor
	df['showtime'] = movie_year
	df['areas'] = movie_country
	df['genres'] = movie_type
	df['comment'] = short_comment
	df.to_csv(csv_name, encoding='utf_8_sig', index=False)  # 将数据保存到csv文件
	print('csv文件已保存:', csv_name)


if __name__ == "__main__":
	# 定义一个请求头(防止反爬)
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
	# 开始爬取豆瓣数据
	for i in range(10):  # 爬取共10页，每页25条数据
		page_url = 'https://movie.douban.com/top250?start={}'.format(str(i * 25))
		print('开始爬取第{}页，地址是:{}'.format(str(i + 1), page_url))
		get_movie_info(page_url, headers)
		sleep(1)  # 等待1秒(防止反爬)
	# 保存到csv文件
	save_to_csv(csv_name="MovieDouban250.csv")
	# 把csv导入mysql数据库(需先安装并启动MySQL,参考:说明.txt;导入失败不影响已保存的csv)
	try:
		engine = create_engine('mysql+pymysql://root:123456@localhost/douban_bigscreen')
		df = pd.read_csv('MovieDouban250.csv')
		df.to_sql(name='t_film', con=engine, chunksize=1000, if_exists='replace', index=None)
		print('数据已导入MySQL数据库,表名:t_film')
	except Exception as e:
		print('导入MySQL失败(不影响csv结果,请先安装并启动MySQL):', e)
