from selenium import webdriver
from slugify import slugify
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
wd = webdriver.Chrome('chromedriver', options=options)

wd.get("https://www.thespruce.com/plants-a-to-z-5116344")
cards = wd.find_elements_by_class_name('alphabetical-card')

links = []
for card in cards:
  links.append(card.get_attribute('href'))
del links[:8]

def split_list(array, elem, type = 1):
  for idx, el in enumerate(array):
    if el == elem:
      return array[:idx] if type == 1 else array[idx+1:]

def convert_dict(array):  
    init = iter(array)
    res_dct = dict(zip(init, init))  
    return res_dct

def remove_words(array):
  for word in array:
    if word.replace(' ', '').isupper():
      array.remove(word)
  return array

def separate_arrays(array):
  titles = []
  contents = []
  aux_contents = []

  count = 0

  try:
    for elem in array:
      if len(elem.split(' ')) < 6:
        titles.append(elem)
        if count != 0:
          contents.append(aux_contents)
          aux_contents = []
        count += 1
      else:
        aux_contents.append(elem)
  except:
    return False, False

  return titles, contents

def handle_content(content):
  titles, contents = separate_arrays(content)

  new_titles = []
  new_contents = []

  if not titles and not contents:
    return False

  for (idx, content) in enumerate(contents):
    contents[idx] = ' '.join(content)

  for (idx, title) in enumerate(titles):
    slugs = ['light', 'soil', 'water', 'temperature-and-humidity', 'fertilizer']
    slug = slugify(title)

    if slug in slugs:
      new_titles.append(slug)
      new_contents.append(contents[idx])

  zip_iterator = zip(new_titles, new_contents)
  content_dict = dict(zip_iterator)
  return content_dict

def check_title(text):
  if text == 'native-areas':
    text = 'native-area'

  elif text == 'hardiness-zone' or text == 'usda-plant-hardiness-zones':
    text = 'hardiness-zones'

  elif text == 'latin-name':
    text = 'botanical-name'

  elif text == 'common-names':
    text = 'common-name'

  elif text == 'native-range':
    text = 'native-area'

  return text

def inspect_plant(link):
  wd.get(link)

  try:
    link = wd.find_element_by_xpath('/html/body/main/article/div[1]/div/div[2]/div[2]')
  except:
    return False

  page_list = link.text.split('\n')
  remove_words(page_list)

  try:
    table = link.find_element_by_tag_name('table')
  except:
    return False

  # Get description
  description = split_list(page_list, table.text.split('\n')[0])
  description = ''.join(description)

  content = split_list(page_list, table.text.split('\n')[-1], 2)
  content_dict = handle_content(content)

  if not content_dict:
    return False

  # Get image
  try:
    image = link.find_element_by_xpath('/html/body/main/article/div[1]/div/div[1]/figure/div/div/img')
    image = image.get_attribute('src')
  except:
    return False
  
  # Get table
  table = table.find_elements_by_tag_name('td')
  dict_table = []
  for (idx, column) in enumerate(table):
    text = column.text
    if idx % 2 == 0:
      text = slugify(text)
      text = check_title(text)
      
    dict_table.append(text)
  dict_table = convert_dict(dict_table)

  return {'description': description, **dict_table, **content_dict, 'image': image}

res = []
for link in links[:50]:
  plant = inspect_plant(link)
  if plant:
    res.append(plant)

df = pd.DataFrame(res)

if 'bloom-color' in df.columns:
  del df['bloom-color']

df = df.dropna()

from google.colab import files
df.to_csv('plants.csv', index=False) 
files.download('plants.csv')