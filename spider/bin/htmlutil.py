#coding=utf-8

import re

def get_all_links(html):
  matches = re.findall('"((http|ftp)s?://.*?)"', html)
  links = []
  for i in matches:
    links.append(i[0])
  return links


def remove_html_tag(html):
   #把html标签删除
  html= html.strip()
  dr = re.compile(r'<[^>]+>',re.S)
  html = dr.sub('',html)
  return html
