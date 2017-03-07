import time

from selenium import webdriver
from pytime import pytime
from datetime import datetime
from db import shop_collection, shoe_collection, account, password



TAOBAO_DATE_FORMAT = '%Y年%m月%d日 %H:%M'

def item_next_page():
    try:
        driver.find_element_by_xpath('//li[@class="item next"]/a[@class="J_Ajax num icon-tag"]').click()
        return True
    except:
        return False


def generate_shop_link(shop_list = [], shop_names = []):
    for element in driver.find_elements_by_xpath('//div[@class="item J_MouserOnverReq  "]'):
        try:
            # count
            _count = element.find_element_by_xpath('descendant::div[@class="deal-cnt"]').text
            count = int(_count.replace('人付款', ''))
            if not count:
                continue
            # name
            name = element.find_element_by_xpath('descendant::div[@class="shop"]').text
            if name in shop_names:
                continue
            # store link
            link = element.find_element_by_xpath('descendant::div[@class="shop"]/a').get_attribute('href')
            shop_list.append({'name': name, 'link': link})
            shop_names.append(name)

        except:
            continue
    flag = item_next_page()
    if flag:
        time.sleep(2)
        return generate_shop_link(shop_list, shop_names)
    else:
        return shop_list


def get_single_shop_history(shop_name, early_day, keys, out_of_date=False):
    for element in driver.find_elements_by_xpath('//div[@class="rate-item"]'):
       item_name = element.find_element_by_xpath('descendant::div[@class="rate-auction"]/a').text
       if not all([key in item_name.lower() for key in keys['match_name']]):
           continue
       item_price = element.find_element_by_xpath('descendant::div[@class="rate-auction"]/div[@class="price"]/em').text
       item_date = element.find_element_by_xpath('descendant::div[@class="rate-content"]//span[@class="tb-r-date"]').text
       if item_date and item_date < early_day:
           out_of_date = True
           break
       item_category = element.find_element_by_xpath('descendant::div[@class="rate-content"]//span[@class="tb-r-sku"]').text
       _z = False
       _br = False
       if any([key in item_category.lower() for key in keys['match_zebra']]):
           _z = True
       elif any([key in item_category.lower() for key in keys['match_blackred']]):
           _br = True
       else:
           continue
       # 都通过了，save into DB
       shoe_collection.insert_one({
           'name': ' '.join(keys['match_name']),
           'actual_name': item_name,
           'actual_category': item_category,
           'category': '斑马' if _z else '黑红字母',
           'price': item_price,
           'date': datetime.strptime(item_date, TAOBAO_DATE_FORMAT),
           'shop_name': shop_name,
       })
    if out_of_date:
        return

    try:
        driver.find_element_by_xpath('//li[@class="pg-next pg-disabled"]')
        return;
    except:
        pass

    try:
        driver.find_element_by_xpath('//li[@class="pg-next"]').click()
    except:
        return
    time.sleep(2)
    return get_single_shop_history(shop_name, early_day, keys)


def get_history_by_shop(shop_list, keys):
    early_day = datetime.strftime(pytime.last_week()[0], TAOBAO_DATE_FORMAT)
    if len(shop_list) == 0:
        return []
    else:
        for item in shop_list:
            driver.get(item['link'])
            time.sleep(5)
            try:
                if 'tmall.com/' in shop_list:
                    # 点击展开
                    driver.find_element_by_xpath('//a[@class="slogo-triangle"]').click()
                    # 获得链接
                    rate_url = driver.find_element_by_xpath('//ul[@class="render-byjs"]/li/a').get_attribute('href')
                else:
                    rate_url = driver.find_element_by_xpath('//a[@class="mini-dsr J_TGoldlog"]').get_attribute('href')
            except:
                continue
            driver.get(rate_url)
            item['rate_url'] = rate_url
            if not shop_collection.find_one({'name': item['name']}):
                shop_collection.insert_one(item)
            time.sleep(5)
            get_single_shop_history(item['name'], early_day, keys)


# disable images
chrome_options = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images":2}
chrome_options.add_experimental_option("prefs",prefs)

driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)

# access login page
driver.get('https://login.taobao.com/member/login.jhtml')

time.sleep(3)
# checkout to password mode
driver.find_element_by_class_name('login-switch').click()
# do login
# notice: email must be registered by email
driver.find_element_by_xpath('//input[@id="TPL_username_1"]').send_keys(account)
driver.find_element_by_xpath('//input[@id="TPL_password_1"]').send_keys(password)
driver.find_element_by_xpath('//button[@id="J_SubmitStatic"]').click()


time.sleep(8)

cookies = driver.get_cookies()

url_keys = 'yeezy+boost+350+v2'


# TODO: 需要一个判断是否是目标商品的更精准的算法
keys = {
        'match_name': ['yeezy', 'boost', '350', 'v2'],
        'match_zebra': ['斑马', '白', '白斑马', 'zebra'],
        'match_blackred': ['黑红字母', '黑 红', '黑红字', '黑红'],
        }

driver.get('https://s.taobao.com/search?q={keys}'.format(keys=url_keys))

shop_list = generate_shop_link()


get_history_by_shop(shop_list, keys)
