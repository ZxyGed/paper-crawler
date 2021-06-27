import os
import time
import json
import requests
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class paperCrawler():
    def __init__(self, keyword, source, year, saveDir, browser):
        self.keyword = keyword
        self.source = source
        self.year = year
        self.saveDir = saveDir
        self.browser = browser
        self.base = '%s/%s/%s/%s' % (self.saveDir, self.source, self.year, self.keyword)
        if not os.path.exists(self.base):
            os.makedirs(self.base)
        open('%s/fetchedAbsList.md' % self.base, 'a').close()
        open('%s/fetchedPDFList.md' % self.base, 'a').close()
        open('%s/fail2abstract.md' % self.base, 'a').close()
        open('%s/fail2pdf.md' % self.base, 'a').close()

    def savePaperList(self, folder, fileName, paperList):
        '''
        :param folder: paperList保存的文件夹
        :param fileName: paperList保存的文件名，包括会议所有论文的totalPaperList.json以及包含筛选得到的paperList.json
        :param paperList: 需要保存的paperList
        '''
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open('%s/%s' % (folder, fileName), 'w', encoding='utf-8') as f:
            paperListStr = json.dumps(paperList)
            json.dump(paperListStr, f)

    def checkTotalPaperList(self):
        '''
        查看是否保存有该会议概念的完整论文列表，如果有就读取并返回，否则返回空列表
        :return: List-会议完整的论文列表
        '''
        listLoc = '%s/%s/%s/totalPaperList.json' % (self.saveDir, self.source, self.year)
        if not os.path.exists(listLoc):
            return []
        with open(listLoc, 'r', encoding='utf-8') as f:
            paperListStr = json.load(f)
            paperList = json.loads(paperListStr)
        return paperList

    def filterPaper(self, paperList):
        '''
        根据关键词及其变体，如去除'-'，筛选列表中是否有包含关键词的论文，并返回筛选的论文列表
        :param paperList: 需要筛选的论文列表
        :return: List-包含关键字的论文组成的列表
        '''
        keywords = {self.keyword, self.keyword.replace('-', '')}
        res = []
        for paper in paperList:
            for keyword in keywords:
                if keyword.lower() in paper.lower():
                    res.append(paper)
                    break
        return res

    def getPaperList(self):
        '''
        返回筛选后的论文列表结果
        如果存在会议完整论文列表，直接从中进行筛选，否则调用专门的论文列表爬取函数并返回结果
        :return: List-根据关键词筛选得到的论文列表
        '''
        totalPaperList = self.checkTotalPaperList()
        if totalPaperList:
            return self.filterPaper(totalPaperList)
        if self.source == 'ICLR':
            paperList = self.getICLRPaperList()
        elif self.source == 'ICML':
            paperList = self.getICMLPaperList()
        elif self.source == 'NIPS':
            paperList = self.getNIPSPaperList()
        else:
            raise Warning("source(%s) not supported!" % self.source)
        folder = '%s/%s/%s/%s' % (self.saveDir, self.source, self.year, self.keyword)
        fileName = 'paperList.json'
        self.savePaperList(folder, fileName, paperList)
        return paperList

    def getICLRPaperList(self):
        '''
        爬取ICLR完整的论文列表，保存并根据关键词筛选符合条件的论文并返回
        由于使用的selenium而不是抓包爬取，需要等第一条记录出现后等5秒，页面加载完成后才能爬取，同时需要模拟双击进行页面切换
        :return: List-ICLR中根据关键词筛选后的论文列表
        '''
        totalPaperList = []
        self.browser.get('https://openreview.net/group?id=ICLR.cc/%s/Conference' % (self.year))
        wait = WebDriverWait(self.browser, 20)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-unstyled li h4')),
                   message='oral papers not present')
        time.sleep(5)
        paperTitles = pq(self.browser.page_source)('.list-unstyled li h4')
        totalPaperList.extend([paper.text() for paper in paperTitles.items()])
        # totalRes.extend([title.text() for title in paperTitles.items() if self.keyword.lower() in title.text().lower()])

        # 模拟双击spotlight标签进行页面跳转（直接使用get进行跳转无效）
        spotlightButton = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#notes li')),
                                     message='spotlight not present')
        ActionChains(self.browser).double_click(spotlightButton[2]).perform()
        # 等到第一条结果出现后再等待5秒让结果加载完全，必须等待5秒，否则只会爬取第一条结果
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-unstyled li h4')),
                   message='spotlight papers not present')
        time.sleep(5)
        paperTitles = pq(self.browser.page_source)('.list-unstyled li h4')
        totalPaperList.extend([paper.text() for paper in paperTitles.items()])
        # totalRes.extend([title.text() for title in paperTitles.items() if self.keyword.lower() in title.text().lower()])

        posterButton = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#notes li')),
                                  message='poster not present')
        ActionChains(self.browser).double_click(posterButton[3]).perform()
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-unstyled li h4')),
                   message='poster papers not present')
        time.sleep(5)
        paperTitles = pq(self.browser.page_source)('.list-unstyled li h4')
        totalPaperList.extend([paper.text() for paper in paperTitles.items()])

        folder = '%s/%s/%s' % (self.saveDir, self.source, self.year)
        fileName = 'totalPaperList.json'
        self.savePaperList(folder, fileName, totalPaperList)
        return self.filterPaper(totalPaperList)

    def getNIPSPaperList(self):
        '''
        爬取NIPS完整的论文列表，保存并根据关键词筛选符合条件的论文并返回
        :return: List-NIPS中根据关键词筛选后的论文列表
        '''
        self.browser.get('https://proceedings.neurips.cc/paper/%s' % self.year)
        paperTitles = pq(self.browser.page_source)('.col ul li a')
        totalPaperList = [paper.text() for paper in paperTitles.items()]
        folder = '%s/%s/%s' % (self.saveDir, self.source, self.year)
        fileName = 'totalPaperList.json'
        self.savePaperList(folder, fileName, totalPaperList)
        return [paper for paper in totalPaperList if self.keyword.lower() in paper.lower()]
        # return [title.text() for title in paperTitles.items() if self.keyword.lower() in title.text().lower()]

    def getICMLPaperList(self):
        '''
        爬取ICML完整的论文列表，保存并根据关键词筛选符合条件的论文并返回
        :return: List-ICML中根据关键词筛选后的论文列表
        '''
        self.browser.get('https://icml.cc/Conferences/%s/AcceptedPapersInitial' % self.year)
        # pq得到的内容即使在cell最后一行也必须print才能看见
        paperTitles = pq(self.browser.page_source)('div .col-xs-9 b')
        totalPaperList = [paper.text() for paper in paperTitles.items()]
        folder = '%s/%s/%s' % (self.saveDir, self.source, self.year)
        fileName = 'totalPaperList.json'
        self.savePaperList(folder, fileName, totalPaperList)
        return [paper for paper in totalPaperList if self.keyword.lower() in paper.lower()]
        # 通过.text获取标签内的文本，然后进行比较并筛除包含关键字的论文名
        # return [title.text() for title in paperTitles.items() if self.keyword.lower() in title.text().lower()]

    def fetchPaper(self, paper, fetchAbs=True, fetchPDF=True):
        '''
        从arxiv爬取摘要和论文PDF，主要流程为模拟搜索，将搜索结果与论文名进行精确匹配，爬取摘要以及PDF
        :param paper: 论文名
        :param fetchAbs: 是否爬取论文摘要
        :param fetchPDF: 是否爬取PDF
        :return: bool-爬取是否成功
        '''
        arxiv = 'https://arxiv.org/search/?query=&searchtype=all&abstracts=show&order=-announced_date_first&size=50'
        self.browser.get(arxiv)
        wait = WebDriverWait(self.browser, 10)
        inputBox = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#query')),
                              message='inputBox not present')
        submitButton = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.breathe-vertical .field button')),
            message='submit button not present')
        if len(inputBox) != 1:
            raise Exception('seletor of inputBox is inaccurate!')
        if len(submitButton) != 1:
            raise Exception('seletor of submitButton is inaccurate!')
        inputBox, submitButton = inputBox[0], submitButton[0]
        inputBox.clear()
        inputBox.send_keys(paper)
        submitButton.click()
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.arxiv-result')),
                       message='result not present')
        except:
            # 没有搜索到对应论文，将结果保存到noResultFound.md
            with open('%s/noResultFound.md' % (self.base), 'a', encoding='utf-8') as f:
                f.write('%s (%s %s)\n' % (paper, self.source, self.year))
            return False
        searchRes = pq(self.browser.page_source)('.arxiv-result')
        # 不能写为for res in searchRes,否则会报错str没有.text()方法
        for res in searchRes.items():
            # 检查搜索列表中的结果，其题目是否与搜索论文匹配，注意需要统一大小写并去除内部空格防止匹配失败
            if res.find('.title').text().lower().replace(' ', '') == paper.lower().replace(' ', ''):
                if fetchPDF:
                    # 检查该论文的PDF是否已经爬取过
                    with open('%s/fetchedPDFList.md' % (self.base), 'r', encoding='utf-8') as f:
                        records = f.readlines()
                    if paper + '\n' not in records:
                        pdflink = res('.list-title a').eq(1).attr('href')
                        try:
                            # 爬取PDF文件
                            pdf = requests.get('%s.pdf' % pdflink)
                        except:
                            print('getpdf of %s fail' % paper)
                            # 爬取PDF失败，将结果写入fail2pdf.md
                            with open('%s/fail2pdf.md' % (self.base), 'a', encoding='utf-8') as f:
                                f.write('%s\n' % (paper))
                            return False
                        # 爬取成功，将PDF保存到指定位置，注意PDF文件名中不能包含':','?','/'等
                        pdfName = paper.replace(':', '_').replace('?', '').replace('/', '_')
                        with open('%s/%s (%s %s).pdf' % (self.base, pdfName, self.source, self.year), 'wb') as f:
                            f.write(pdf.content)
                        # 将已爬取的文章名称保存到fetchPDFList.md中，防止重复爬取
                        with open('%s/fetchedPDFList.md' % (self.base), 'a', encoding='utf-8') as f:
                            f.write('%s\n' % paper)
                if fetchAbs:
                    # 检查改论文的摘要是否爬取过了
                    with open('%s/fetchedAbsList.md' % (self.base), 'r', encoding='utf-8') as f:
                        records = f.readlines()
                    if paper + '\n' not in records:
                        abstractlink = res.find('.list-title a').eq(0).attr('href')
                        try:
                            # 爬取论文摘要
                            page = requests.get(abstractlink)
                        except:
                            # 爬取摘要失败，写入fail2abstract.md
                            print('getabs of %s fail' % paper)
                            with open('%s/fail2abstract.md' % (self.base), 'a', encoding='utf-8') as f:
                                f.write('%s\n' % (paper))
                            return False
                        abstract = pq(page.text.encode('utf-8'))('#abs .abstract').text()
                        # 爬取成功，将摘要写入abstract.md
                        with open('%s/abstract.md' % (self.base), 'a', encoding='utf-8') as f:
                            f.write('<h3>%s (%s %s)</h3>\n' % (paper, self.source, self.year))
                            f.write('%s\n' % abstract)
                        # 将已爬取摘要的论文写入fetchAbsList.md，防止重复爬取
                        with open('%s/fetchedAbsList.md' % (self.base), 'a', encoding='utf-8') as f:
                            f.write('%s\n' % paper)
                return True
        # 返回搜索结果，但是搜索结果中没有有效记录
        with open('%s/noResultFound.md' % (self.base), 'a', encoding='utf-8') as f:
            f.write('%s\n' % (paper))
        return False

    def fetch(self, paperList):
        '''
        使用fetchPaper爬取paperLi内所有论文
        :param paperList: 需要爬取的论文列表
        :return: None
        '''
        numPaper = len(paperList)
        for paper in paperList:
            print('processing %s, %s paper of %s %s left' % (paper, numPaper, self.source, self.year))
            try:
                self.fetchPaper(paper, self.source, self.year)
            # 将除fetchPaper中没有找到论文/爬取摘要失败/爬取PDF失败的异常记录到log.md文件中
            except Exception as e:
                with open('%s/log.md' % (self.base), 'a', encoding='utf-8') as f:
                    f.write('%s (%s %s) %s\n' % (paper, self.source, self.year, repr(e)))
            time.sleep(3)
            numPaper -= 1
        print('papers of %s %s complete' % (self.source, self.year))

    def fetchAgain(self):
        '''
        对于之前没有爬取成功的摘要和PDF，重新进行爬取
        :return: None
        '''
        # 由于需要读完清空，模式设置为'r+'
        with open('%s/fail2abstract.md' % (self.base), 'r+', encoding='utf-8') as f:
            records = f.readlines()
            f.truncate(0)
        print("starting refetch paper abstract failed before")
        numAbs = len(records)
        for record in records:
            paper = record.strip()
            print("refetching abstract of %s, %s left" % (paper, numAbs))
            self.fetchPaper(paper, fetchAbs=True, fetchPDF=False)
            time.sleep(3)
            numAbs -= 1

        with open('%s/fail2pdf.md' % (self.base), 'r+', encoding='utf-8') as f:
            records = f.readlines()
            f.truncate(0)
        print("starting refetch paper PDF failed before")
        numpdfs = len(records)
        for record in records:
            paper = record.strip()
            print("refetching pdf of %s, %s left" % (paper, numpdfs))
            self.fetchPaper(paper, fetchAbs=False, fetchPDF=True)
            numpdfs -= 1

    def crawl(self):
        '''
        执行完整的爬取流程，获取列表，爬取内容
        :return: None
        '''
        paperList = self.getPaperList()
        self.fetch(paperList)
        self.fetchAgain()


if __name__ == '__main__':
    '''
    如果要更新totalPaperList,记得remove掉'saveDir/source/year'下的内容
    '''
    SAVEDIR = 'paper-warehouse'
    KEYWORDS = ['multi-view', 'tensor', 'Graph learning', 'graph neural network', 'cluster']
    # KEYWORDS=['graph neural network']
    # NIPS2021目前还没出
    ICMLyear, ICLRyear, NIPSyear = 2020, 2020, 2019

    # options = webdriver.ChromeOptions()
    # options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # # options.add_argument('headless')
    # browser = webdriver.Chrome(options=options)

    options = webdriver.ChromeOptions()
    options.add_argument('enable-webgl')
    # 如果想要监测浏览器运行，注释掉这一项
    # options.add_argument('headless')
    options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs",
                                    {"profile.password_manager_enabled": False, "credentials_enable_service": False})

    browser = webdriver.Chrome(options=options)
    browser.maximize_window()

    try:
        for KEYWORD in KEYWORDS:
            paperCrawler(KEYWORD, 'ICLR', ICLRyear, SAVEDIR, browser).crawl()
            paperCrawler(KEYWORD, 'ICML', ICMLyear, SAVEDIR, browser).crawl()
            paperCrawler(KEYWORD, 'NIPS', NIPSyear, SAVEDIR, browser).crawl()
    except Exception as e:
        print(repr(e))
    finally:
        browser.quit()
