# coding: utf8
from __future__ import unicode_literals
  
import csv,os,json,io
from exceptions import ValueError
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from unidecode import unidecode
from nltk import wordpunct_tokenize
from nltk.corpus import stopwords
import pandas as pd

# Airbnb scrapper made for the Hackatal 2017 event : https://github.com/HackaTAL/2017
__author__ = "Gael Guibon <https://github.com/gguibon>"
__license__ = "AGPL"
__version__ = "0.1.0"
__maintainer__ = "Gael Guibon"
__email__ = "gael.guibon@lsis.org"
__status__ = "Development"

driver = webdriver.Firefox()

def init_driver():
    driver = webdriver.Firefox()

def selenium_airbnb(asin, city="none"):
    jProduct = dict()
    lReviews = list()
 
    url="https://www.airbnb.fr/rooms/"+asin
    driver.get(url)
    jProduct['productTitle'] = driver.find_element(By.XPATH, '//div[@id="listing_name"]').text
    jProduct['id'] = asin
    star_rating_wrappers_labels = driver.find_elements(By.XPATH, '//div[@id="reviews"]//span[@class="text_5mbkop-o_O-size_reduced_1oti1ib-o_O-weight_light_1nmzz2x-o_O-inline_g86r3e"]')
    star_rating_wrappers = driver.find_elements(By.XPATH, '//div[@class="star-rating-wrapper"]')
    jProduct['averageRanking'] = float(star_rating_wrappers[2].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[0].text).lower()] = float(star_rating_wrappers[3].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[1].text).lower()] = float(star_rating_wrappers[4].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[2].text).lower()] = float(star_rating_wrappers[5].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[3].text).lower()] = float(star_rating_wrappers[6].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[4].text).lower()] = float(star_rating_wrappers[7].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct[unidecode(star_rating_wrappers_labels[5].text).lower()] = float(star_rating_wrappers[8].get_attribute('aria-label').replace('Moyenne de ','').replace(' sur 5 étoiles',''))
    jProduct['nbReviews'] = int( star_rating_wrappers[0].get_attribute('aria-label').split(' les ')[1].split(' ')[0] )
    jProduct['resume'] = ""
    
    pages = driver.find_elements(By.XPATH, '//div[@class="pagination pagination-responsive"]//li')
    iMaxPages = int( pages[-2].text )
    
    for i in range(iMaxPages):

        reviewRows = driver.find_elements(By.XPATH, '//div[@class="row review"]')
        print len(reviewRows)
        names = driver.find_elements(By.XPATH, '//div[@class="name"]')
        dates = driver.find_elements(By.XPATH, '//div[@class="date"]')
        # comments = driver.find_elements(By.XPATH, '//div[@class="review-content"]//div[@class="text_5mbkop-o_O-size_reduced_1oti1ib-o_O-weight_light_1nmzz2x"]')
        comments = driver.find_elements(By.XPATH, '//div[@class="review-content"]//div[@class="review-text space-top-2"]')
        
        for j in range( len(reviewRows) ):
            lang = detect_language(comments[j].text)
            print names[j].text, dates[j].text, lang
            if lang == "english" or lang == "french":
                jReview = {"name":names[j].text, "date":dates[j].text, "text":comments[j].text, "lang":lang, "pos":[], "neg":[]}
                lReviews.append(jReview)
        try:
            next_page = driver.find_element(By.XPATH, '//div[@class="pagination pagination-responsive"]/ul[@class="list-unstyled"]/li[@class="next next_page"]/a')
            next_page.click()
        except:
            print 'no more pages'
        # WebDriverWait(driver, 30).until(lambda driver: driver.execute_script("return jQuery.active == 0"))
        WebDriverWait(driver, 30).until(not_loading)
        print 'page', i

    jProduct['reviews'] = lReviews
    print len(lReviews), 'reviews sur ', jProduct['nbReviews']
    jProduct['nbReviews'] = len(lReviews)

    with io.open('data-airbnb/w2vauto/'+city+'-'+asin+'-'+str(jProduct['averageRanking'])+'.json', 'w', encoding='utf8') as json_file:
        data = json.dumps(jProduct, ensure_ascii=False, indent=4)
        json_file.write(unicode(data))
    #     driver.close()
    # finally:
    #     driver.quit()


def _calculate_languages_ratios(text):
    '''
    Author: Melchior de Toldi
    '''
    languages_ratios = {}

    tokens = wordpunct_tokenize(text)
    words = [word.lower() for word in tokens]

    # Compute per language included in nltk number of unique stopwords
    # appearing in analyzed text
    for language in stopwords.fileids():
        stopwords_set = set(stopwords.words(language))
        words_set = set(words)
        common_elements = words_set.intersection(stopwords_set)

        languages_ratios[language] = len(common_elements)  # language "score"

    return languages_ratios

def detect_language(text):
    '''
    Author: Melchior de Toldi
    '''
    ratios = _calculate_languages_ratios(text)
    most_rated_language = max(ratios, key=ratios.get)
    return most_rated_language

def not_loading(driver):
    element = driver.find_element(By.XPATH, '//div[@class="review-main"]')
    if element:
        return element
    else:
        return False 

def not_loading_search(driver):
    element1 = driver.find_element(By.XPATH, '//div[@class="search-results"]')
    element2 = driver.find_element(By.XPATH, '//nav[@role="navigation"]')
    element3 = driver.find_element(By.XPATH, '//li[@class="buttonContainer_1am0dt-o_O-noRightMargin_10fyztj"]')
    if element1 and element2 and element3:
        return element3
    else:
        return False     

        
def check_exists_by_xpath(xpath):
    try:
        webdriver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True    

def readFileLines(path):
        '''read a file given a path. Return the content in a list of lines'''
        with open(path) as f:
            res = f.readlines()
        return res

def read_asin():
    AsinList = readFileLines("asin-fr-airbnb-w2v.ls")
    for asin in AsinList:
        if '## ' not in asin:
            selenium_airbnb( asin.strip('\n') )
            sleep(60)# wait one minute

def search(city, min_comments=1, max_articles=10):
    search_url = "https://www.airbnb.fr/s/"+city
    driver.get(search_url)
    try:
        close_popup = driver.find_element(By.XPATH, '//div[@class="responsiveCloseButton_1y33c39"]//button[@class="container_1rp5252"]')
        close_popup.click()
    except:
        pass
    i_articles = 0
    l_asin = list()
    df_asin = pd.DataFrame()

    pages = driver.find_elements(By.XPATH, '//a[@class="link_1ko8une"]')
    iMaxPages = int( pages[-2].text )
    print iMaxPages

    df_asin_global = pd.read_csv("df_asin.tsv", sep='\t', encoding='utf-8')
    l_global_asin = df_asin_global['asin'].tolist()

    for i in range(iMaxPages):
        if i_articles >= max_articles:
                break
        offers = driver.find_elements(By.XPATH, '//div[@class="infoContainer_v72lrv"]/a[@class="linkContainer_15ns6vh"]')
        for offer in offers:
            n_comments = offer.text.split("\n")[-1].replace(" commentaires","").replace(' commentaire','')
            if "NOUVEAU" in n_comments: continue
            try:
                n_comments = int( n_comments )
            except:
                print 'comment not in format'
                continue
            o_asin = offer.get_attribute('href').replace("https://www.airbnb.fr/rooms/","").replace("?location="+city, "")
            try:
                f_rating = float( offer.find_element(By.XPATH, './/span[@role="img"] ').get_attribute('aria-label').replace("Évaluation de ","").replace(" sur 5","") )
            except NoSuchElementException:
                print 'no rating'
                continue
            # print o_asin, n_comments, f_rating
            if n_comments >= min_comments and i_articles < max_articles and f_rating == 5.0: 
                
                if o_asin not in l_global_asin:
                    l_asin.append(o_asin)
                    d_row = {"asin":o_asin, "nb_reviews":n_comments, "globalRating":f_rating, "city":city}
                    df_asin = df_asin.append(d_row, ignore_index=True)
                else:
                    print 'doublon'
                print o_asin, n_comments, f_rating
                i_articles+=1



        try:
            # next_page = driver.find_element(By.XPATH, '//a[@class="link_1ko8une"][last()]')
            next_page = driver.find_element(By.XPATH, '//li[@class="buttonContainer_1am0dt-o_O-noRightMargin_10fyztj"]')
            next_page.click()
        except:
            print 'no more pages'
        # WebDriverWait(driver, 30).until(lambda driver: driver.execute_script("return jQuery.active == 0"))
        WebDriverWait(driver, 10).until(not_loading_search)
        print 'page', i

    print l_asin   
    current = 0
    for asin in l_asin:
        if '## ' not in asin:
            selenium_airbnb( asin.strip('\n'), city=city )
            sleep(60)# wait one minute
            current+=1
            print current, ' / ', len(l_asin)

    with open('df_asin.tsv', 'a') as f:
        df_asin.to_csv(f, sep=str('\t'), header=False, index=False) 

if __name__ == "__main__":
    # init_driver()
    # read_asin() # to scrap from external list of asin (one per line)

    search("Paris", min_comments=10, max_articles=10) # to search and dynamically create list of asin, then scrap it

    
    # example using asin directly
    # selenium_airbnb("13253")
    driver.close()
    driver.quit()