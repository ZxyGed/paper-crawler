paperCrawler能够根据关键词爬取顶会论文的摘要以及PDF，采用selenium/requests/pyquery，运行前需要确认运行环境的google版本，并从[ChromDriver Downloads](https://chromedriver.chromium.org/downloads)下载对应的ChromeDriver，该项目目前仅支持ICLR/ICML/NIPS三大会议，项目的结构以及运行结果截图如下：

![image-20210627152515161](C:%5CUsers%5C15487%5CAppData%5CRoaming%5CTypora%5Ctypora-user-images%5Cimage-20210627152515161.png)

![image-20210627153059100](C:%5CUsers%5C15487%5CAppData%5CRoaming%5CTypora%5Ctypora-user-images%5Cimage-20210627153059100.png)

结果的文件结构：来源/年份/关键词

- **abstract.md：根据该关键词爬取的论文摘要汇总**
- **noResultFound.md：arxiv中找不到的论文名，需要自己手动查找**
- paperList.json：根据关键词筛选后的论文列表
- totalPaperList.json：该年份下该会议接收的所有论文，如NIPS 2021的所有接收论文
- fetchedAbsList.md：已爬取的摘要的论文列表，防止重复爬取
- fetchedPDFList.md：已爬取PDF的论文列表，防止重复爬取
- fail2abstract.md：爬取摘要失败的论文列表，用于重新爬取
- fail2pdf.md：爬取PDF失败的论文列表，用于重新爬取
- log.md：爬取过程中发生的错误





